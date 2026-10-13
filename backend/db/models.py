from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from .session import Base
from datetime import datetime
import uuid


def now_iso():
    return datetime.utcnow().isoformat()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    created_at = Column(String, default=now_iso)


class Action(Base):
    __tablename__ = 'actions'
    name = Column(String, primary_key=True, index=True)
    required_permission = Column(String, nullable=True)
    created_at = Column(String, default=now_iso)


class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    goal = Column(Text, nullable=False)
    state = Column(String, nullable=False)
    created_at = Column(String, default=now_iso)
    context_json = Column(Text, nullable=True)
    status_message = Column(String, nullable=True)

    plan_steps = relationship('PlanStep', back_populates='task', cascade='all, delete-orphan')
    results = relationship('TaskResult', back_populates='task', cascade='all, delete-orphan')
    approvals = relationship('Approval', back_populates='task', cascade='all, delete-orphan')
    evidences = relationship('Evidence', back_populates='task', cascade='all, delete-orphan')


class PlanStep(Base):
    __tablename__ = 'plan_steps'
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey('tasks.id'))
    seq = Column(Integer, nullable=False, default=0)
    action = Column(String, nullable=False)
    input_json = Column(Text, nullable=True)
    status = Column(String, nullable=False, default='PENDING')

    task = relationship('Task', back_populates='plan_steps')


class TaskResult(Base):
    __tablename__ = 'task_results'
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, ForeignKey('tasks.id'))
    step_id = Column(String, nullable=True)
    action = Column(String, nullable=True)
    output_json = Column(Text, nullable=True)
    created_at = Column(String, default=now_iso)

    task = relationship('Task', back_populates='results')


class Approval(Base):
    __tablename__ = 'approvals'
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, ForeignKey('tasks.id'))
    approved_at = Column(String, default=now_iso)
    approver_id = Column(Integer, nullable=True)
    approved_actions_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    task = relationship('Task', back_populates='approvals')


class Evidence(Base):
    __tablename__ = 'evidence'
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, ForeignKey('tasks.id'))
    description = Column(Text, nullable=True)
    source = Column(String, nullable=True)
    stored_at = Column(String, default=now_iso)
    metadata_json = Column(Text, nullable=True)

    task = relationship('Task', back_populates='evidences')


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(String, default=now_iso)
    event = Column(String, nullable=False)
    details_json = Column(Text, nullable=True)
