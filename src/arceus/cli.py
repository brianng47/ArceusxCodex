from __future__ import annotations

import argparse
import json
import sys

from arceus.codex_runner import CodexRunError, run_handoff_with_codex
from arceus.config import get_settings
from arceus.conversation import ConversationStore, ConversationTurn
from arceus.dashboard_launcher import (
    dashboard_status,
    install_mac_launcher,
    open_dashboard,
    start_dashboard,
    stop_dashboard,
)
from arceus.local_control import LocalControlService
from arceus.migrations import migrate
from arceus.path_policy import describe_path_policy, ensure_read_allowed
from arceus.queue import EnqueueRequest, RemoteTaskQueue, to_pretty_json
from arceus.runtimes import get_runtime, inspect_codex_app_server, inspect_codex_runtime
from arceus.status import StatusTracker, StatusUpdate, initialize_status_tracker
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

    status_summary = subcommands.add_parser(
        "status-summary",
        help="Show the compact current-state tracker for low-token session starts.",
    )
    status_summary.add_argument("--limit", type=int, default=5)
    status_summary.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    record_status = subcommands.add_parser("record-status", help="Record a compact Arceus status update.")
    record_status.add_argument("--actor", default="arceus_cli")
    record_status.add_argument("--runtime", default=None)
    record_status.add_argument("--workstream", required=True)
    record_status.add_argument("--status", required=True)
    record_status.add_argument("--summary", required=True)
    record_status.add_argument("--decision", action="append", default=[])
    record_status.add_argument("--file-changed", action="append", default=[])
    record_status.add_argument("--blocker", action="append", default=[])
    record_status.add_argument("--next-action", action="append", default=[])
    record_status.add_argument("--memory-note", default=None)
    record_status.add_argument("--project", default=None)
    record_status.add_argument("--task", default=None)
    record_status.add_argument("--agent", default=None)
    record_status.add_argument("--source-type", default="manual")
    record_status.add_argument("--source-id", default=None)
    record_status.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    init_status = subcommands.add_parser(
        "init-status-tracker",
        help="Seed the status tracker and Obsidian current-state files.",
    )
    init_status.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    path_policy = subcommands.add_parser("path-policy", help="Show Arceus read/write path allowlists.")
    path_policy.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    local_actions = subcommands.add_parser("local-actions", help="List dashboard-safe local actions.")
    local_actions.add_argument("--limit", type=int, default=8)
    local_actions.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    run_local_action = subcommands.add_parser("run-local-action", help="Run one dashboard-safe local action.")
    run_local_action.add_argument("action_key")
    run_local_action.add_argument("--confirm", default=None, help="Approval token. Use the action key for approval-gated actions.")
    run_local_action.add_argument("--payload", default="{}", type=parse_payload, help="Optional JSON payload.")
    run_local_action.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    web = subcommands.add_parser("web", help="Run the local Arceus dashboard.")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=8787)

    dashboard = subcommands.add_parser("dashboard", help="Start, stop, open, or inspect the dashboard service.")
    dashboard_subcommands = dashboard.add_subparsers(dest="dashboard_command", required=True)

    dashboard_start = dashboard_subcommands.add_parser("start", help="Start the dashboard without keeping Terminal open.")
    dashboard_start.add_argument("--host", default="127.0.0.1")
    dashboard_start.add_argument("--port", type=int, default=8787)
    dashboard_start.add_argument("--no-open", action="store_true", help="Start the server without opening a browser.")
    dashboard_start.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    dashboard_stop = dashboard_subcommands.add_parser("stop", help="Stop the dashboard service started by Arceus.")
    dashboard_stop.add_argument("--host", default="127.0.0.1")
    dashboard_stop.add_argument("--port", type=int, default=8787)
    dashboard_stop.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    dashboard_open = dashboard_subcommands.add_parser("open", help="Open the dashboard in your default browser.")
    dashboard_open.add_argument("--host", default="127.0.0.1")
    dashboard_open.add_argument("--port", type=int, default=8787)
    dashboard_open.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    dashboard_state = dashboard_subcommands.add_parser("status", help="Show whether the dashboard service is reachable.")
    dashboard_state.add_argument("--host", default="127.0.0.1")
    dashboard_state.add_argument("--port", type=int, default=8787)
    dashboard_state.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

    dashboard_install = dashboard_subcommands.add_parser(
        "install-launcher",
        help="Install a double-click macOS app that starts Arceus without a Terminal window.",
    )
    dashboard_install.add_argument("--app-path", default=None, help="Optional .app output path.")
    dashboard_install.add_argument("--json", action="store_true", help="Print raw JSON instead of readable text.")

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
            result_path = ensure_read_allowed(settings, args.result_file)
            with result_path.open("r", encoding="utf-8") as result_file:
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

    if args.command == "status-summary":
        tracker = StatusTracker(settings)
        summary = tracker.current_state(args.limit)
        if args.json:
            print(to_pretty_json(summary))
        else:
            print(format_status_summary(summary))
        return 0

    if args.command == "record-status":
        tracker = StatusTracker(settings)
        recorded = tracker.record(
            StatusUpdate(
                actor=args.actor,
                runtime=args.runtime or settings.runtime_mode,
                workstream=args.workstream,
                status=args.status,
                summary=args.summary,
                decisions=args.decision,
                files_changed=args.file_changed,
                blockers=args.blocker,
                next_actions=args.next_action,
                memory_notes=args.memory_note,
                linked_project=args.project,
                linked_task=args.task,
                linked_agent=args.agent,
                source_type=args.source_type,
                source_id=args.source_id,
            )
        )
        if args.json:
            print(to_pretty_json(recorded))
        else:
            print("Arceus status update recorded.")
            if recorded.get("obsidian_path"):
                print(f"Obsidian note: {recorded['obsidian_path']}")
            if recorded.get("obsidian_error"):
                print(f"Obsidian write issue: {recorded['obsidian_error']}")
        return 0

    if args.command == "init-status-tracker":
        tracker = StatusTracker(settings)
        recorded = initialize_status_tracker(settings, actor="arceus_cli")
        summary = tracker.current_state(5)
        if args.json:
            print(to_pretty_json({"recorded": recorded, "current_state": summary}))
        else:
            print("Arceus status tracker initialized.")
            print(format_status_summary(summary))
        return 0

    if args.command == "path-policy":
        policy = describe_path_policy(settings)
        if args.json:
            print(to_pretty_json(policy))
        else:
            print(format_path_policy(policy))
        return 0

    if args.command == "local-actions":
        local_control = LocalControlService(settings)
        payload = {
            "actions": local_control.catalog(),
            "recent_runs": local_control.recent_runs(args.limit),
        }
        if args.json:
            print(to_pretty_json(payload))
        else:
            print(format_local_actions(payload))
        return 0

    if args.command == "run-local-action":
        local_control = LocalControlService(settings)
        result = local_control.run(args.action_key, confirm=args.confirm, payload=args.payload)
        if args.json:
            print(to_pretty_json(result))
        else:
            print(format_local_action_result(result))
        return 0

    if args.command == "web":
        serve(settings, args.host, args.port)
        return 0

    if args.command == "dashboard":
        if args.dashboard_command == "start":
            result = start_dashboard(settings, args.host, args.port, open_browser=not args.no_open)
        elif args.dashboard_command == "stop":
            result = stop_dashboard(args.host, args.port, settings=settings)
        elif args.dashboard_command == "open":
            result = open_dashboard(args.host, args.port, settings=settings)
        elif args.dashboard_command == "status":
            result = dashboard_status(args.host, args.port, settings=settings)
        elif args.dashboard_command == "install-launcher":
            result = install_mac_launcher(settings, args.app_path)
        else:
            raise AssertionError(f"Unknown dashboard command {args.dashboard_command}")

        if args.json:
            print(to_pretty_json(result))
        else:
            print(format_dashboard_command_result(result))
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
    ]

    current_status = summary.get("current_status") or {}
    latest_update = current_status.get("latest_update")
    lines.extend(["", "Current State", "-------------"])
    if latest_update:
        lines.append(
            f"- {latest_update['status']} / {latest_update['workstream']}: "
            f"{latest_update['summary']}"
        )
    else:
        lines.append("No status tracker update recorded yet.")
    next_actions = current_status.get("next_actions") or []
    if next_actions:
        lines.append("- Next: " + "; ".join(next_actions[:3]))
    blockers = current_status.get("blockers") or []
    if blockers:
        lines.append("- Blocked: " + "; ".join(blockers[:3]))

    lines.extend(["", "Recent Sessions", "---------------"])

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


def format_status_summary(summary: dict) -> str:
    lines = [
        "Arceus Current State",
        "====================",
        f"Owner: {summary['owner_id']}",
        f"Obsidian vault: {summary.get('obsidian_vault_path') or 'not configured'}",
        "",
        "Latest Update",
        "-------------",
    ]

    latest = summary.get("latest_update")
    if latest:
        lines.append(f"- {latest['status']} / {latest['workstream']}: {latest['summary']}")
        lines.append(f"- Time: {latest['created_at']}")
    else:
        lines.append("No status updates yet.")

    lines.extend(["", "Next Actions", "------------"])
    next_actions = summary.get("next_actions") or []
    if not next_actions:
        lines.append("No next actions recorded.")
    for action in next_actions:
        lines.append(f"- {action}")

    lines.extend(["", "Blockers", "--------"])
    blockers = summary.get("blockers") or []
    if not blockers:
        lines.append("No blockers recorded.")
    for blocker in blockers:
        lines.append(f"- {blocker}")

    lines.extend(["", "Recent Updates", "--------------"])
    recent = summary.get("recent_updates") or []
    if not recent:
        lines.append("No recent updates.")
    for update in recent:
        lines.append(f"- {update['status']} / {update['workstream']}: {update['summary']}")

    return "\n".join(lines)


def format_local_actions(payload: dict) -> str:
    lines = ["Arceus Local Control", "====================", "", "Allowed Actions", "---------------"]
    for action in payload.get("actions") or []:
        approval = "approval required" if action.get("approval_required") else "no approval needed"
        lines.append(f"- {action['key']}: {action['title']} ({action['risk_level']}, {approval})")

    lines.extend(["", "Recent Runs", "-----------"])
    runs = payload.get("recent_runs") or []
    if not runs:
        lines.append("No local action runs recorded yet.")
    for run in runs:
        lines.append(f"- {run['status']} / {run['action_key']}: {run.get('output_summary') or run.get('error_message') or run['title']}")
    return "\n".join(lines)


def format_local_action_result(result: dict) -> str:
    action = result.get("action") or {}
    lines = [
        "Arceus Local Action",
        "===================",
        f"Action: {action.get('title') or action.get('key')}",
        f"Status: {'completed' if result.get('ok') else 'failed'}",
    ]
    if result.get("error"):
        lines.append(f"Error: {result['error']}")
    action_result = result.get("result") or {}
    if action_result.get("summary"):
        lines.append(f"Summary: {action_result['summary']}")
    run = result.get("run")
    if run:
        lines.append(f"Run id: {run['id']}")
    return "\n".join(lines)


def format_dashboard_command_result(result: dict) -> str:
    status = result.get("status") if isinstance(result.get("status"), dict) else result
    lines = [
        "Arceus Dashboard",
        "================",
        str(result.get("summary") or status.get("summary") or "Dashboard status read."),
    ]
    if status.get("url"):
        lines.append(f"URL: {status['url']}")
    if status.get("running") is not None:
        lines.append(f"Running: {'yes' if status['running'] else 'no'}")
    if status.get("pid"):
        lines.append(f"PID: {status['pid']}")
    if status.get("log_path"):
        lines.append(f"Log: {status['log_path']}")
    if result.get("log_tail"):
        lines.extend(["", "Recent Log", "----------", str(result["log_tail"]).strip()])
    return "\n".join(lines)


def format_path_policy(policy: dict) -> str:
    lines = [
        "Arceus Path Policy",
        "==================",
        str(policy.get("summary") or "Path policy loaded."),
        "",
        "Read Roots",
        "----------",
    ]
    for path in policy.get("read_roots") or []:
        lines.append(f"- {path}")

    lines.extend(["", "Write Roots", "-----------"])
    for path in policy.get("write_roots") or []:
        lines.append(f"- {path}")
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
