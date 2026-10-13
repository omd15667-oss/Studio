from sqlalchemy.orm import Session
from . import models
from datetime import datetime
import json


def add_audit(db: Session, event: str, details: dict):
    entry = models.AuditLog(event=event, details_json=json.dumps(details or {}))
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def create_user(db: Session, username: str, email: str, password_hash: str):
    user = models.User(username=username, email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def create_action(db: Session, name: str, required_permission: str):
    action = models.Action(name=name, required_permission=required_permission)
    db.add(action)
    db.commit()
    return action


def list_actions(db: Session):
    return db.query(models.Action).all()


def create_task(db: Session, user_id: int, goal: str, context: dict = None):
    task = models.Task(user_id=user_id, goal=goal, state='RECEIVED', context_json=json.dumps(context or {}), status_message='Goal received.')
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: str):
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def list_tasks(db: Session, user_id: int = None):
    q = db.query(models.Task)
    if user_id:
        q = q.filter(models.Task.user_id == user_id)
    return q.order_by(models.Task.created_at.desc()).all()


def add_plan_steps(db: Session, task: models.Task, steps: list):
    # clear existing steps
    for s in task.plan_steps:
        db.delete(s)
    db.commit()

    for seq, step in enumerate(steps, start=1):
        ps = models.PlanStep(task_id=task.id, seq=seq, action=step.get('action'), input_json=json.dumps(step.get('input') or {}), status='PENDING')
        db.add(ps)
    db.commit()
    db.refresh(task)
    return task


def add_result(db: Session, task: models.Task, step_id: str, action: str, output: dict):
    tr = models.TaskResult(task_id=task.id, step_id=step_id, action=action, output_json=json.dumps(output or {}))
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr


def add_approval(db: Session, task: models.Task, approver_id: int, actions: list, notes: str):
    ap = models.Approval(task_id=task.id, approver_id=approver_id, approved_actions_json=json.dumps(actions or []), notes=notes)
    db.add(ap)
    db.commit()
    db.refresh(ap)
    return ap


def add_evidence(db: Session, task: models.Task, items: list):
    created = []
    for item in items:
        ev = models.Evidence(task_id=task.id, description=item.get('description'), source=item.get('source'), metadata_json=json.dumps(item.get('metadata') or {}))
        db.add(ev)
        created.append(ev)
    db.commit()
    return created


def record_task_state(db: Session, task: models.Task, state: str, status_message: str = None):
    task.state = state
    if status_message:
        task.status_message = status_message
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
