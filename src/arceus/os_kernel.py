from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from arceus.config import Settings
from arceus.vault_memory import VaultMemory, WikiPageSpec


LOW_RISK_HINTS = (
    "summarize",
    "read",
    "inspect",
    "plan",
    "draft",
    "research",
    "list",
    "explain",
)
MEDIUM_RISK_HINTS = (
    "write",
    "edit",
    "update",
    "create",
    "run",
    "execute",
    "install",
    "generate",
)
HIGH_RISK_HINTS = (
    "delete",
    "remove",
    "publish",
    "send",
    "purchase",
    "buy",
    "credential",
    "password",
    "financial",
    "irreversible",
)


@dataclass(frozen=True)
class ApprovalGate:
    gate_id: str
    title: str
    risk_level: str
    required: bool
    reason: str


@dataclass(frozen=True)
class AgentRunPlan:
    agent: str
    runtime: str
    purpose: str
    depends_on: list[str] = field(default_factory=list)
    risk_level: str = "low"


@dataclass(frozen=True)
class JarvisPlan:
    plan_id: str
    created_at: str
    user_request: str
    problem_statement: str
    assumptions: list[str]
    clarifying_questions: list[str]
    context_pages: list[str]
    approval_gates: list[ApprovalGate]
    agent_runs: list[AgentRunPlan]
    expected_outputs: list[str]
    memory_writeback: list[str]
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class JarvisOSKernel:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.memory = VaultMemory(settings)

    def draft_plan(self, request: str, project: str | None = None) -> JarvisPlan:
        clean_request = " ".join(request.strip().split())
        if not clean_request:
            raise ValueError("Request is required.")
        self.memory.ensure_structure()
        context = self.memory.read_context()
        risk = _classify_risk(clean_request)
        questions = _clarifying_questions(clean_request, project)
        approval_gates = _approval_gates(clean_request, risk)
        agent_runs = _agent_runs(clean_request, project, risk)
        problem = _problem_statement(clean_request)
        context_pages = _context_pages(context["index"], project)
        return JarvisPlan(
            plan_id=f"jarvis-{uuid4()}",
            created_at=datetime.now(timezone.utc).astimezone().isoformat(),
            user_request=clean_request,
            problem_statement=problem,
            assumptions=_assumptions(project, risk),
            clarifying_questions=questions,
            context_pages=context_pages,
            approval_gates=approval_gates,
            agent_runs=agent_runs,
            expected_outputs=[
                "One synthesized answer or execution summary.",
                "Clear next actions and unresolved blockers.",
                "Memory writeback for reusable context.",
            ],
            memory_writeback=[
                "Update wiki/hot.md with durable current context.",
                "Append the workflow to wiki/log.md.",
                "Create or update project, preference, workflow, or analysis pages if new durable knowledge appears.",
            ],
            next_action="Answer clarifying questions if any are material, then request holistic approval before execution.",
        )

    def save_plan(self, plan: JarvisPlan) -> dict[str, Any]:
        body = _render_plan_body(plan)
        result = self.memory.upsert_page(
            WikiPageSpec(
                path=f"wiki/analyses/{plan.plan_id}.md",
                title=f"Jarvis Plan {plan.plan_id}",
                body=body,
                tags=("arceus", "jarvis-plan", "workflow"),
                sources=("direct user request",),
                related=("system/active-roadmap", "workflows/clarify-plan-approve-execute"),
            ),
            operation="plan",
        )
        self.memory.refresh_hot(
            {
                "Latest Plan": f"{plan.problem_statement}\n\nPlan page: [[analyses/{plan.plan_id}]]",
            }
        )
        return result


def _classify_risk(request: str) -> str:
    text = request.lower()
    if any(hint in text for hint in HIGH_RISK_HINTS):
        return "high"
    if any(hint in text for hint in MEDIUM_RISK_HINTS):
        return "medium"
    return "low"


def _problem_statement(request: str) -> str:
    trimmed = request.rstrip(".")
    return f"Resolve the user's request: {trimmed}."


def _clarifying_questions(request: str, project: str | None) -> list[str]:
    text = request.lower()
    questions: list[str] = []
    if not project and any(word in text for word in ("project", "business", "instagram", "content", "workflow")):
        questions.append("Which project should this attach to?")
    if any(word in text for word in ("best", "optimize", "improve", "growth", "strategy")):
        questions.append("What outcome metric should define success?")
    if any(word in text for word in ("run", "execute", "send", "publish", "edit", "write")):
        questions.append("Which actions should be approved now, and which should pause for review?")
    return questions


def _assumptions(project: str | None, risk: str) -> list[str]:
    assumptions = [
        "Use Obsidian root wiki as the memory source before execution.",
        "Use Postgres/status tracker as the operational ledger.",
        "Use holistic approval before running the workflow.",
    ]
    if project:
        assumptions.append(f"Attach durable memory to project: {project}.")
    if risk == "low":
        assumptions.append("Treat this as low risk unless the plan discovers writes, credentials, publishing, purchases, or destructive actions.")
    else:
        assumptions.append(f"Treat this as {risk} risk until approval gates are reviewed.")
    return assumptions


def _approval_gates(request: str, risk: str) -> list[ApprovalGate]:
    gates = [
        ApprovalGate(
            gate_id="holistic_workflow_approval",
            title="Approve workflow plan",
            risk_level=max(risk, "medium", key={"low": 0, "medium": 1, "high": 2}.get),
            required=True,
            reason="Brian asked Arceus to present dependencies and approval needs before running.",
        )
    ]
    text = request.lower()
    if any(word in text for word in ("write", "edit", "delete", "publish", "send", "purchase", "credential", "financial")):
        gates.append(
            ApprovalGate(
                gate_id="explicit_high_impact_action",
                title="Approve high-impact action",
                risk_level="high" if risk == "high" else "medium",
                required=True,
                reason="The request may touch writes, external side effects, credentials, publishing, or destructive work.",
            )
        )
    return gates


def _agent_runs(request: str, project: str | None, risk: str) -> list[AgentRunPlan]:
    text = request.lower()
    runs = [
        AgentRunPlan(
            agent="Arceus",
            runtime="local_os_kernel",
            purpose="Clarify problem statement, coordinate workflow, and synthesize final answer.",
            risk_level="low",
        ),
        AgentRunPlan(
            agent="Memory Scribe",
            runtime="obsidian_root_wiki",
            purpose="Read relevant vault context and write reusable memory after completion.",
            risk_level="low",
        ),
    ]
    if any(word in text for word in ("file", "code", "repo", "implement", "edit", "write")):
        runs.append(
            AgentRunPlan(
                agent="Filesystem/Code Agent",
                runtime="codex_cli",
                purpose="Inspect files, draft changes, and apply only approved edits.",
                depends_on=["Memory Scribe"],
                risk_level="medium" if risk != "high" else "high",
            )
        )
    if project or any(word in text for word in ("instagram", "tcg", "content", "growth", "business")):
        runs.append(
            AgentRunPlan(
                agent="TCG Growth Strategist",
                runtime="runtime_broker_pending",
                purpose="Plan business workflow and attach outputs to project memory.",
                depends_on=["Memory Scribe"],
                risk_level="low",
            )
        )
    return runs[:4]


def _context_pages(index: str, project: str | None) -> list[str]:
    pages = ["wiki/index.md", "wiki/hot.md", "wiki/system/active-roadmap.md"]
    if project and "riprocket" in project.lower():
        pages.append("wiki/projects/riprocket-tcg-instagram-growth.md")
    if "brian-operating-preferences" in index:
        pages.append("wiki/preferences/brian-operating-preferences.md")
    return pages


def _render_plan_body(plan: JarvisPlan) -> str:
    lines = [
        f"User request: {plan.user_request}",
        "",
        "## Problem Statement",
        "",
        plan.problem_statement,
        "",
        "## Assumptions",
        "",
        *[f"- {item}" for item in plan.assumptions],
        "",
        "## Clarifying Questions",
        "",
    ]
    if plan.clarifying_questions:
        lines.extend(f"- {question}" for question in plan.clarifying_questions)
    else:
        lines.append("- None required before planning.")
    lines.extend(["", "## Context Pages", ""])
    lines.extend(f"- `{page}`" for page in plan.context_pages)
    lines.extend(["", "## Approval Gates", ""])
    lines.extend(
        f"- {gate.title} ({gate.risk_level}): {gate.reason}"
        for gate in plan.approval_gates
    )
    lines.extend(["", "## Agent Runs", ""])
    lines.extend(
        f"- {run.agent} via {run.runtime}: {run.purpose}"
        for run in plan.agent_runs
    )
    lines.extend(["", "## Expected Outputs", ""])
    lines.extend(f"- {item}" for item in plan.expected_outputs)
    lines.extend(["", "## Memory Writeback", ""])
    lines.extend(f"- {item}" for item in plan.memory_writeback)
    lines.extend(["", "## Next Action", "", plan.next_action])
    return "\n".join(lines)
