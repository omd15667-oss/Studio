import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


PERMISSIONS = {
    "PLAN": "PLAN",
    "LOCAL_READ": "LOCAL_READ",
    "LOCAL_WRITE": "LOCAL_WRITE",
    "EXTERNAL_ACCESS": "EXTERNAL_ACCESS",
    "PUBLISH": "PUBLISH",
    "FINANCIAL_ACTION": "FINANCIAL_ACTION",
}

HIGH_RISK = {
    PERMISSIONS["EXTERNAL_ACCESS"],
    PERMISSIONS["PUBLISH"],
    PERMISSIONS["FINANCIAL_ACTION"],
}


class BATUEngine:
    """Lightweight BATU task engine implementing goal -> plan -> permission -> execution -> verification."""

    def __init__(self):
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def audit(self, event: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.audit_log.append({
            "id": str(uuid.uuid4()),
            "timestamp": self._utc_now(),
            "event": event,
            "details": details or {},
        })

    def register_action(self, name: str, handler, required_permission: str) -> None:
        if name in self.registry:
            raise ValueError(f"Action already registered: {name}")
        if not callable(handler):
            raise TypeError("Action handler must be callable.")
        if not required_permission:
            raise ValueError("required_permission is required for all actions.")
        self.registry[name] = {
            "handler": handler,
            "required_permission": required_permission,
        }

    def create_task(self, goal: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        goal_text = (goal or "").strip()
        if not goal_text:
            raise ValueError("A valid human goal is required.")

        task = {
            "id": str(uuid.uuid4()),
            "goal": goal_text,
            "state": "RECEIVED",
            "createdAt": self._utc_now(),
            "plan": [],
            "results": [],
            "evidence": [],
            "approval": None,
            "context": (options or {}).get("context") or (options or {}),
            "statusMessage": "Goal received.",
        }
        self.audit("TASK_CREATED", {"taskId": task["id"], "goal": task["goal"]})
        return task

    def create_plan(self, task: Dict[str, Any], steps: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        steps_list = list(steps)
        if not steps_list:
            raise ValueError("The plan must contain at least one step.")

        plan = []
        for index, step in enumerate(steps_list, start=1):
            action_name = step.get("action")
            if not action_name or action_name not in self.registry:
                raise ValueError(f"Unknown action at step {index}: {action_name}")
            plan.append({
                "id": str(uuid.uuid4()),
                "action": action_name,
                "input": step.get("input") or {},
                "status": "PENDING",
            })

        task["plan"] = plan
        task["state"] = "PLANNED"
        task["statusMessage"] = "Plan created; awaiting permission checks."
        self.audit("PLAN_CREATED", {"taskId": task["id"], "steps": [s["action"] for s in plan]})
        return task

    def check_permission(self, action_name: str, granted_permissions: Optional[List[str]] = None) -> Dict[str, Any]:
        granted_permissions = granted_permissions or []
        action = self.registry.get(action_name)
        if action is None:
            return {"allowed": False, "reason": "ACTION_NOT_REGISTERED"}

        required_permission = action["required_permission"]
        if not required_permission:
            return {"allowed": False, "reason": "MISSING_PERMISSION_DEFINITION"}

        if required_permission not in granted_permissions:
            return {
                "allowed": False,
                "reason": "PERMISSION_NOT_GRANTED",
                "requiredPermission": required_permission,
            }

        if required_permission in HIGH_RISK:
            return {
                "allowed": False,
                "reason": "EXPLICIT_APPROVAL_REQUIRED",
                "requiredPermission": required_permission,
            }

        return {"allowed": True, "reason": "PERMISSION_GRANTED"}

    def approve_task(self, task: Dict[str, Any], approval: Dict[str, Any]) -> Dict[str, Any]:
        if not approval or approval.get("confirmed") is not True:
            raise ValueError("Explicit human approval is required.")
        if approval.get("taskId") != task["id"]:
            raise ValueError("Approval does not match this task.")

        task["approval"] = {
            "taskId": task["id"],
            "approvedAt": self._utc_now(),
            "approvedActions": approval.get("actions") or [],
            "notes": approval.get("notes") or "",
        }
        self.audit("HUMAN_APPROVAL_RECORDED", {"taskId": task["id"], "approvedActions": task["approval"]["approvedActions"]})
        return task

    def execute_task(self, task: Dict[str, Any], granted_permissions: Optional[List[str]] = None) -> Dict[str, Any]:
        granted_permissions = granted_permissions or []
        if task.get("state") != "PLANNED":
            raise ValueError("Task must be planned before execution.")

        for step in task.get("plan", []):
            permission = self.check_permission(step["action"], granted_permissions)
            if not permission["allowed"]:
                step["status"] = "BLOCKED"
                task["state"] = "AWAITING_APPROVAL"
                task["statusMessage"] = permission["reason"]
                self.audit("ACTION_BLOCKED", {"taskId": task["id"], "action": step["action"], "reason": permission["reason"]})
                return task

        task["state"] = "EXECUTING"
        task["statusMessage"] = "Execution in progress."

        for step in task.get("plan", []):
            try:
                action = self.registry.get(step["action"])
                if action is None:
                    raise ValueError(f"Unknown action: {step['action']}")
                step["status"] = "RUNNING"
                output = action["handler"](step.get("input") or {})
                step["status"] = "COMPLETED"
                task["results"].append({
                    "stepId": step["id"],
                    "action": step["action"],
                    "output": output,
                })
                self.audit("ACTION_COMPLETED", {"taskId": task["id"], "stepId": step["id"], "action": step["action"]})
            except Exception as exc:  # pragma: no cover - defensive code
                step["status"] = "FAILED"
                task["state"] = "FAILED"
                task["statusMessage"] = "Execution failed."
                self.audit("ACTION_FAILED", {
                    "taskId": task["id"],
                    "stepId": step.get("id"),
                    "action": step.get("action"),
                    "error": str(exc),
                })
                return task

        return task

    def verify_task(self, task: Dict[str, Any], verification: Dict[str, Any]) -> Dict[str, Any]:
        if task.get("state") != "EXECUTING":
            raise ValueError("Task is not ready for verification.")

        if not verification or verification.get("passed") is not True:
            task["state"] = "FAILED"
            task["statusMessage"] = "Verification failed or evidence is missing."
            self.audit("VERIFICATION_FAILED", {"taskId": task["id"]})
            return task

        evidence_items = verification.get("evidence") or []
        if not isinstance(evidence_items, list) or len(evidence_items) == 0:
            task["state"] = "FAILED"
            task["statusMessage"] = "Verification failed or evidence is missing."
            self.audit("VERIFICATION_FAILED", {"taskId": task["id"]})
            return task

        task["evidence"] = [{
            "description": str(item.get("description") or ""),
            "source": str(item.get("source") or ""),
            "observedAt": self._utc_now(),
        } for item in evidence_items]
        task["state"] = "VERIFIED"
        task["statusMessage"] = "Task verified with recorded evidence."
        self.audit("TASK_VERIFIED", {"taskId": task["id"], "evidenceCount": len(task["evidence"])})
        return task

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return [dict(entry) for entry in self.audit_log]


__all__ = ["BATUEngine", "PERMISSIONS", "HIGH_RISK"]
