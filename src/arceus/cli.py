from __future__ import annotations

import argparse
import json
import sys

from arceus.codex_runner import CodexRunError, run_handoff_with_codex
from arceus.config import get_settings
from arceus.conversation import ConversationStore, ConversationTurn
from arceus.migrations import migrate
from arceus.queue import EnqueueRequest, RemoteTaskQueue, to_pretty_json
from arceus.runtimes import get_runtime, inspect_codex_app_server, inspect_codex_runtime
from arceus.web import serve
from arceus.worker import drain_once, run_polling_worker


def parse_payload(value: str) -> dict:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"Payload must be valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise argparse.ArgumentTypeError("Payload must be a JSON object.")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="arceus",
        description="Local-first Arceus command tools.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    subcommands.add_parser("setup-db", help="Create or update Arceus database tables.")

    enqueue = subcommands.add_parser("enqueue", help="Add a task to the durable queue.")
    enqueue.add_argument("--role", default=None, help="Target worker role.")
    enqueue.add_argument("--kind", required=True, help="Task kind, for example noop.")
    enqueue.add_argument("--payload", default="{}", type=parse_payload, help="JSON task payload.")
    enqueue.add_argument("--owner", default=None, help="Owner id.")
    enqueue.add_argument("--expires-at", default=None, help="Optional ISO timestamp.")

    show = subcommands.add_parser("show-task", help="Show one task as JSON.")
    show.add_argument("task_id")

    list_tasks = subcommands.add_parser("list-tasks", help="List recent tasks.")
    list_tasks.add_argument("--limit", type=int, default=20)

    drain = subcommands.add_parser("drain", help="Claim and process pending tasks once.")
    drain.add_argument("--role", default=None, help="Worker role to drain.")
    drain.add_argument("--worker-id", default=None, help="Worker identity.")

    worker = subcommands.add_parser("worker", help="Run the polling worker.")
    worker.add_argument("--role", default=None, help="Worker role to drain.")
    worker.add_argument("--worker-id", default=None, help="Worker identity.")
    worker.add_argument("--poll-interval", type=float, default=5.0)

    chat = subcommands.add_parser("chat", help="Start a local Arceus conversation shell.")
    chat.add_argument("--title", default="Arceus Conversation")

    handoffs = subcommands.add_parser("list-handoffs", help="List recent Codex handoffs.")
    handoffs.add_argument("--limit", type=int, default=20)

    show_handoff = subcommands.add_parser("show-handoff", help="Show one handoff as JSON.")
    show_handoff.add_argument("handoff_id")

    run_handoff = subcommands.add_parser(
        "run-handoff",
        help="Run a stored handoff through local Codex and record the result automatically.",
    )
    run_handoff.add_argument("handoff_id")

    record = subcommands.add_parser("record-handoff-result", help="Record a manual Codex result.")
    record.add_argument("handoff_id")
    record.add_argument("--summary", default=None, help="Short result summary.")
    record.add_argument("--memory", default=None, help="Memory-worthy note.")
    record.add_argument(
        "--result-file",
        default=None,
        help="Path to a text file containing the result. Use '-' to read stdin.",
    )
    record.add_argument("--result", default=None, help="Inline result text.")

    subcommands.add_parser("runtime-doctor", help="Inspect local Codex/Claude runtime availability.")

    app_server = subcommands.add_parser(
        "app-server-doctor",
        help="Inspect Codex app-server feasibility without enabling direct control.",
    )
    app_server.add_argument(
        "--schema-dir",
        default=None,
        help="Optional directory for generated protocol schemas. Defaults to a temp directory.",
    )
    app_server.add_argument(
        "--no-experimental",
        action="store_true",
        help="Generate only stable schemas, if Codex supports that split.",
    )
    app_server.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    memory = subcommands.add_parser("memory-summary", help="Summarize recent Arceus memory records.")
    memory.add_argument("--limit", type=int, default=5)
    memory.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    web = subcommands.add_parser("web", help="Run the local Arceus dashboard.")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8787)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    queue = RemoteTaskQueue(settings)

    if args.command == "setup-db":
        migrate(settings)
        print("Arceus database is ready.")
        return 0

    if args.command == "chat":
        store = ConversationStore(settings)
        runtime = get_runtime(settings)
        session_id = store.create_session(args.title)

        print("Arceus is awake.")
        print(f"Runtime: {runtime.name}")
        print(f"Session: {session_id}")
        print("Type 'exit' to end the conversation.")

        while True:
            try:
                user_message = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nArceus: Sealed for now. Return when the thought sharpens.")
                return 0

            if not user_message:
                continue
            if user_message.lower() in {"exit", "quit"}:
                print("Arceus: Sealed for now. Return when the thought sharpens.")
                return 0

            history = list(store.list_messages(session_id))
            response = runtime.respond(user_message, history)
            assistant_message = response.content
            if response.handoff_prompt:
                handoff_id = store.create_runtime_handoff(
                    session_id=session_id,
                    runtime=response.runtime,
                    user_intent=user_message,
                    handoff_prompt=response.handoff_prompt,
                )
                assistant_message = (
                    f"{assistant_message}\n\n"
                    f"Handoff ID: {handoff_id}\n\n"
                    "Codex handoff packet:\n\n"
                    "```markdown\n"
                    f"{response.handoff_prompt}\n"
                    "```\n\n"
                    "After Codex finishes, record the result with:\n"
                    f"`./scripts/arceus record-handoff-result {handoff_id} --result-file <path>`"
                )
            store.record_turn(
                ConversationTurn(
                    session_id=session_id,
                    user_message=user_message,
                    assistant_message=assistant_message,
                    runtime=response.runtime,
                )
            )
            print(f"Arceus: {assistant_message}")
        return 0

    if args.command == "list-handoffs":
        store = ConversationStore(settings)
        print(to_pretty_json(store.list_handoffs(args.limit)))
        return 0

    if args.command == "show-handoff":
        store = ConversationStore(settings)
        handoff = store.get_handoff(args.handoff_id)
        if handoff is None:
            print(f"No handoff found with id {args.handoff_id}.", file=sys.stderr)
            return 1
        print(to_pretty_json(handoff))
        return 0

    if args.command == "run-handoff":
        try:
            print(to_pretty_json(run_handoff_with_codex(settings, args.handoff_id)))
        except CodexRunError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0

    if args.command == "record-handoff-result":
        result_text = args.result
        if args.result_file == "-":
            result_text = sys.stdin.read()
        elif args.result_file:
            with open(args.result_file, "r", encoding="utf-8") as result_file:
                result_text = result_file.read()

        if not result_text:
            fallback_parts = []
            if args.summary:
                fallback_parts.append(f"Summary: {args.summary}")
            if args.memory:
                fallback_parts.append(f"Memory: {args.memory}")
            result_text = "\n".join(fallback_parts)

        if not result_text:
            print(
                "Provide --result, --result-file <path>, --result-file -, "
                "or at least --summary/--memory.",
                file=sys.stderr,
            )
            return 1

        store = ConversationStore(settings)
        recorded = store.record_handoff_result(
            args.handoff_id,
            result_text=result_text,
            result_summary=args.summary,
            memory_summary=args.memory,
        )
        if not recorded:
            print(f"No handoff found with id {args.handoff_id}.", file=sys.stderr)
            return 1
        print("Codex handoff result recorded.")
        return 0

    if args.command == "runtime-doctor":
        print(to_pretty_json(inspect_codex_runtime(settings)))
        return 0

    if args.command == "app-server-doctor":
        report = inspect_codex_app_server(
            settings,
            schema_dir=args.schema_dir,
            include_experimental=not args.no_experimental,
        )
        if args.json:
            print(to_pretty_json(report))
        else:
            print(format_app_server_report(report))
        return 0

    if args.command == "memory-summary":
        store = ConversationStore(settings)
        summary = store.build_memory_summary(args.limit)
        if args.json:
            print(to_pretty_json(summary))
        else:
            print(format_memory_summary(summary))
        return 0

    if args.command == "web":
        serve(settings, args.host, args.port)
        return 0

    if args.command == "enqueue":
        task_id = queue.enqueue(
            EnqueueRequest(
                worker_role=args.role or settings.worker_role,
                kind=args.kind,
                payload=args.payload,
                owner_id=args.owner or settings.owner_id,
                expires_at=args.expires_at,
            )
        )
        print(task_id)
        return 0

    if args.command == "show-task":
        task = queue.get_task(args.task_id)
        if task is None:
            print(f"No task found with id {args.task_id}.", file=sys.stderr)
            return 1
        print(to_pretty_json(task))
        return 0

    if args.command == "list-tasks":
        print(to_pretty_json(list(queue.list_tasks(args.limit))))
        return 0

    if args.command == "drain":
        count = drain_once(
            queue,
            worker_role=args.role or settings.worker_role,
            worker_id=args.worker_id or settings.worker_id,
        )
        print(f"Processed {count} task(s).")
        return 0

    if args.command == "worker":
        run_polling_worker(
            queue,
            worker_role=args.role or settings.worker_role,
            worker_id=args.worker_id or settings.worker_id,
            poll_interval_seconds=args.poll_interval,
        )
        return 0

    raise AssertionError(f"Unknown command {args.command}")


def format_memory_summary(summary: dict) -> str:
    lines = [
        "Arceus Memory Summary",
        "=====================",
        f"Owner: {summary['owner_id']}",
        f"Runtime: {summary['runtime_mode']}",
        "",
        "Recent Sessions",
        "---------------",
    ]

    sessions = summary["recent_sessions"]
    if not sessions:
        lines.append("No conversation sessions yet.")
    for session in sessions:
        lines.append(
            f"- {session['title']} ({session['runtime']}): "
            f"{session['message_count']} message(s), updated {session['updated_at']}"
        )

    lines.extend(["", "Recent Codex Handoffs", "---------------------"])
    handoffs = summary["recent_handoffs"]
    if not handoffs:
        lines.append("No Codex handoffs yet.")
    for handoff in handoffs:
        detail = handoff["memory_summary"] or handoff["result_summary"] or handoff["user_intent"]
        lines.append(
            f"- {handoff['status']} via {handoff['runtime']}: {detail}"
        )

    lines.extend(["", "Task Counts", "-----------"])
    task_counts = summary["task_counts"]
    if not task_counts:
        lines.append("No remote tasks yet.")
    for status, count in task_counts.items():
        lines.append(f"- {status}: {count}")

    return "\n".join(lines)


def format_app_server_report(report: dict) -> str:
    lines = [
        "Codex App-Server Feasibility",
        "============================",
        f"Status: {report['status']}",
        f"Codex found: {'yes' if report['available'] else 'no'}",
        f"Codex path: {report['resolved_path'] or report['configured_path']}",
        f"Daemon online: {'yes' if report.get('daemon_online') else 'no'}",
        f"Direct bridge ready: {'yes' if report['direct_bridge_ready'] else 'no'}",
        f"Recommendation: {report['active_recommendation']}",
        "",
    ]

    cli_version = _doctor_output(report.get("cli_version"))
    if cli_version:
        lines.extend(["Codex Version", "-------------", cli_version, ""])

    daemon_version = _doctor_output(report.get("daemon_version"))
    if daemon_version:
        lines.extend(["Daemon Check", "------------", daemon_version, ""])

    schema_generation = report.get("schema_generation")
    if isinstance(schema_generation, dict):
        schema_ok = "passed" if schema_generation.get("ok") else "failed"
        lines.extend(
            [
                "Schema Check",
                "------------",
                f"Generation: {schema_ok}",
                f"Schema directory: {report['schema_dir']}",
                f"Schema files: {report['schema_file_count']}",
                "",
            ]
        )

    lines.extend(["Protocol Signals", "----------------"])
    lines.append(f"Client methods: {len(report['client_methods'])}")
    lines.append(f"Server approval requests: {len(report['approval_request_methods'])}")
    lines.append(f"High-power client methods: {len(report['high_power_client_methods'])}")
    lines.append("")

    approval_methods = report["approval_request_methods"][:8]
    if approval_methods:
        lines.append("Approval methods found:")
        for method in approval_methods:
            lines.append(f"- {method}")
        lines.append("")

    high_power_methods = report["high_power_client_methods"][:10]
    if high_power_methods:
        lines.append("High-power methods found:")
        for method in high_power_methods:
            lines.append(f"- {method}")
        lines.append("")

    lines.extend(["Readiness Notes", "---------------"])
    for note in report["readiness_notes"]:
        lines.append(f"- {note}")

    lines.extend(["", "Next Gates", "----------"])
    for gate in report["next_gates"]:
        lines.append(f"- {gate}")

    return "\n".join(lines)


def _doctor_output(value: object) -> str:
    if not isinstance(value, dict) or not value.get("output"):
        return ""
    return str(value["output"]).strip()


if __name__ == "__main__":
    raise SystemExit(main())
