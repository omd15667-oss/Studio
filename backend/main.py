from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv

from security.authentication import AuthenticationManager
from security.encryption import get_encryption_manager
from security.audit import AuditLogger
from batu_core import BATUEngine, PERMISSIONS

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Digital Sovereignty Mirror",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware
app.add_middleware(GZIPMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()
audit_logger = AuditLogger()
batu_engine = BATUEngine()

# ============= Models =============

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: str

class NoteCreate(BaseModel):
    title: str
    content: str

class NoteUpdate(BaseModel):
    title: str = None
    content: str = None

class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: str
    updated_at: str


class TaskCreateRequest(BaseModel):
    goal: str
    context: dict = {}


class TaskActionRequest(BaseModel):
    action: str
    input: dict = {}


class TaskPlanRequest(BaseModel):
    steps: list[TaskActionRequest] = []


class TaskExecutionRequest(BaseModel):
    granted_permissions: list[str] = []


class ApprovalRequest(BaseModel):
    confirmed: bool = False
    taskId: str
    actions: list[str] = []
    notes: str = ""


class EvidenceItem(BaseModel):
    description: str
    source: str
    metadata: dict = {}


class VerificationRequest(BaseModel):
    passed: bool = False
    evidence: list[EvidenceItem] = []


# ============= In-Memory Storage (v0.1) =============

users_db = {}
notes_db = {}
user_counter = 0
note_counter = 0
tasks_db = {}


# ============= Built-in BATU actions =============


def read_local_file(payload: dict):
    file_path = payload.get("path") or "README.md"
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        return {
            "path": file_path,
            "content_preview": content[:500],
            "line_count": len(content.splitlines()),
        }
    except Exception as exc:  # pragma: no cover - defensive code
        return {
            "path": file_path,
            "content_preview": f"File not accessible: {str(exc)}",
            "line_count": 0,
        }


def write_local_file(payload: dict):
    file_path = payload.get("path") or "output.txt"
    content = payload.get("content") or ""
    with open(file_path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return {
        "path": file_path,
        "written": True,
        "char_count": len(content),
    }


def create_summary(payload: dict):
    text = str(payload.get("text") or "").strip()
    return {
        "summary": text[:500],
        "character_count": len(text),
    }


def search_web(payload: dict):
    query = payload.get("query") or "BATU" 
    return {
        "query": query,
        "results": [
            {"title": f"Result for {query}", "url": "https://example.com/search?q=" + query},
            {"title": "BATU architecture overview", "url": "https://example.com/batu"},
        ],
    }


def publish_post(payload: dict):
    return {
        "published": True,
        "channel": payload.get("channel") or "internal",
        "message": payload.get("message") or "BATU update published",
    }


def financial_transfer(payload: dict):
    return {
        "status": "simulated",
        "amount": payload.get("amount") or 0,
        "currency": payload.get("currency") or "USD",
    }


batu_engine.register_action("create_summary", create_summary, PERMISSIONS["PLAN"])
batu_engine.register_action("read_local_file", read_local_file, PERMISSIONS["LOCAL_READ"])
batu_engine.register_action("write_local_file", write_local_file, PERMISSIONS["LOCAL_WRITE"])
batu_engine.register_action("search_web", search_web, PERMISSIONS["EXTERNAL_ACCESS"])
batu_engine.register_action("publish_post", publish_post, PERMISSIONS["PUBLISH"])
batu_engine.register_action("financial_transfer", financial_transfer, PERMISSIONS["FINANCIAL_ACTION"])


def get_user_id_from_token(credentials: HTTPAuthCredentials):
    try:
        payload = AuthenticationManager.verify_token(credentials.credentials)
        return payload["user_id"]
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


# ============= Auth Endpoints =============

@app.post("/api/v1/auth/register", response_model=UserResponse, tags=["Auth"])
async def register(req: RegisterRequest):
    """Register new user"""
    global user_counter

    if req.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_counter += 1
    hashed_pwd = AuthenticationManager.hash_password(req.password)

    user = {
        "id": user_counter,
        "username": req.username,
        "email": req.email,
        "password_hash": hashed_pwd,
        "created_at": datetime.utcnow().isoformat()
    }

    users_db[req.username] = user

    audit_logger.log_action(
        user_id=user["id"],
        action="register",
        resource_type="user"
    )

    logger.info(f"User registered: {req.username}")

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        created_at=user["created_at"]
    )


@app.post("/api/v1/auth/login", response_model=TokenResponse, tags=["Auth"])
async def login(req: LoginRequest):
    """Login user"""
    if req.username not in users_db:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = users_db[req.username]

    if not AuthenticationManager.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = AuthenticationManager.create_access_token({
        "user_id": user["id"],
        "username": user["username"]
    })

    audit_logger.log_action(
        user_id=user["id"],
        action="login",
        resource_type="auth"
    )

    logger.info(f"User logged in: {req.username}")

    return TokenResponse(access_token=token)


# ============= Notes Endpoints =============

@app.post("/api/v1/notes", response_model=NoteResponse, tags=["Notes"])
async def create_note(note: NoteCreate, credentials: HTTPAuthCredentials = Depends(security)):
    """Create new note"""
    global note_counter

    user_id = get_user_id_from_token(credentials)

    note_counter += 1
    now = datetime.utcnow().isoformat()

    new_note = {
        "id": note_counter,
        "user_id": user_id,
        "title": note.title,
        "content": note.content,
        "created_at": now,
        "updated_at": now
    }

    notes_db[note_counter] = new_note

    audit_logger.log_action(
        user_id=user_id,
        action="create_note",
        resource_type="note",
        resource_id=note_counter
    )

    logger.info(f"Note created: {note_counter} by user {user_id}")

    return NoteResponse(**new_note)


@app.get("/api/v1/notes", response_model=list, tags=["Notes"])
async def list_notes(credentials: HTTPAuthCredentials = Depends(security)):
    """List all notes for user"""
    user_id = get_user_id_from_token(credentials)

    user_notes = [
        NoteResponse(**note) for note in notes_db.values()
        if note["user_id"] == user_id
    ]

    audit_logger.log_action(
        user_id=user_id,
        action="list_notes",
        resource_type="note"
    )

    return user_notes


@app.get("/api/v1/notes/{note_id}", response_model=NoteResponse, tags=["Notes"])
async def get_note(note_id: int, credentials: HTTPAuthCredentials = Depends(security)):
    """Get specific note"""
    user_id = get_user_id_from_token(credentials)

    if note_id not in notes_db:
        raise HTTPException(status_code=404, detail="Note not found")

    note = notes_db[note_id]

    if note["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    audit_logger.log_action(
        user_id=user_id,
        action="get_note",
        resource_type="note",
        resource_id=note_id
    )

    return NoteResponse(**note)


@app.put("/api/v1/notes/{note_id}", response_model=NoteResponse, tags=["Notes"])
async def update_note(note_id: int, update: NoteUpdate, credentials: HTTPAuthCredentials = Depends(security)):
    """Update note"""
    user_id = get_user_id_from_token(credentials)

    if note_id not in notes_db:
        raise HTTPException(status_code=404, detail="Note not found")

    note = notes_db[note_id]

    if note["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    if update.title:
        note["title"] = update.title
    if update.content:
        note["content"] = update.content

    note["updated_at"] = datetime.utcnow().isoformat()

    audit_logger.log_action(
        user_id=user_id,
        action="update_note",
        resource_type="note",
        resource_id=note_id
    )

    logger.info(f"Note updated: {note_id}")

    return NoteResponse(**note)


@app.delete("/api/v1/notes/{note_id}", tags=["Notes"])
async def delete_note(note_id: int, credentials: HTTPAuthCredentials = Depends(security)):
    """Delete note"""
    user_id = get_user_id_from_token(credentials)

    if note_id not in notes_db:
        raise HTTPException(status_code=404, detail="Note not found")

    note = notes_db[note_id]

    if note["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    del notes_db[note_id]

    audit_logger.log_action(
        user_id=user_id,
        action="delete_note",
        resource_type="note",
        resource_id=note_id
    )

    logger.info(f"Note deleted: {note_id}")

    return {"message": "Note deleted successfully"}


# ============= BATU Task Engine Endpoints =============

@app.get("/api/v1/actions", tags=["BATU"])
async def list_actions():
    """List registered BATU actions."""
    actions = []
    for name, meta in batu_engine.registry.items():
        actions.append({
            "name": name,
            "required_permission": meta["required_permission"],
        })
    return {"actions": actions}


@app.post("/api/v1/tasks", tags=["BATU"])
async def create_task(req: TaskCreateRequest, credentials: HTTPAuthCredentials = Depends(security)):
    """Create a new BATU task."""
    user_id = get_user_id_from_token(credentials)
    task = batu_engine.create_task(req.goal, {"context": {**(req.context or {}), "user_id": user_id}})
    tasks_db[task["id"]] = task
    return task


@app.get("/api/v1/tasks", tags=["BATU"])
async def list_tasks(credentials: HTTPAuthCredentials = Depends(security)):
    """List all BATU tasks for the authenticated user."""
    get_user_id_from_token(credentials)
    return {"tasks": list(tasks_db.values())}


@app.get("/api/v1/tasks/{task_id}", tags=["BATU"])
async def get_task(task_id: str, credentials: HTTPAuthCredentials = Depends(security)):
    """Get task details."""
    get_user_id_from_token(credentials)
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_db[task_id]


@app.post("/api/v1/tasks/{task_id}/plan", tags=["BATU"])
async def create_plan(task_id: str, req: TaskPlanRequest, credentials: HTTPAuthCredentials = Depends(security)):
    """Attach a plan to a task."""
    get_user_id_from_token(credentials)
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    task = tasks_db[task_id]
    tasks_db[task_id] = batu_engine.create_plan(task, [step.model_dump() for step in req.steps])
    return tasks_db[task_id]


@app.post("/api/v1/tasks/{task_id}/approve", tags=["BATU"])
async def approve_task(task_id: str, req: ApprovalRequest, credentials: HTTPAuthCredentials = Depends(security)):
    """Approve a task for risky actions."""
    get_user_id_from_token(credentials)
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    task = tasks_db[task_id]
    tasks_db[task_id] = batu_engine.approve_task(task, req.model_dump())
    return tasks_db[task_id]


@app.post("/api/v1/tasks/{task_id}/execute", tags=["BATU"])
async def execute_task(task_id: str, req: TaskExecutionRequest, credentials: HTTPAuthCredentials = Depends(security)):
    """Execute a planned task."""
    get_user_id_from_token(credentials)
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    task = tasks_db[task_id]
    tasks_db[task_id] = batu_engine.execute_task(task, req.granted_permissions)
    return tasks_db[task_id]


@app.post("/api/v1/tasks/{task_id}/verify", tags=["BATU"])
async def verify_task(task_id: str, req: VerificationRequest, credentials: HTTPAuthCredentials = Depends(security)):
    """Attach evidence and mark task as verified."""
    get_user_id_from_token(credentials)
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    task = tasks_db[task_id]
    tasks_db[task_id] = batu_engine.verify_task(task, req.model_dump())
    return tasks_db[task_id]


@app.get("/api/v1/audit", tags=["BATU"])
async def get_audit_logs(credentials: HTTPAuthCredentials = Depends(security)):
    """Return BATU audit logs."""
    get_user_id_from_token(credentials)
    return {"logs": batu_engine.get_audit_log()}


# ============= Privacy & Audit Endpoints =============

@app.get("/api/v1/audit/logs", tags=["Privacy"])
async def get_audit_logs_for_user(credentials: HTTPAuthCredentials = Depends(security)):
    """Get user's audit logs"""
    user_id = get_user_id_from_token(credentials)

    logs = audit_logger.get_logs(user_id, limit=100)

    return {"user_id": user_id, "logs": logs, "total": len(logs)}


# ============= System Endpoints =============

@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "healthy",
        "service": "Digital Sovereignty Mirror API",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "name": "Digital Sovereignty Mirror",
        "version": "0.1.0",
        "mission": "Your Data. Your Knowledge. Your Decision.",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "api": "/api/v1",
            "batu_ui": "/batustudio",
        }
    }


@app.get("/batustudio", response_class=HTMLResponse, tags=["System"])
async def batu_studio_page():
    """Simple BATU Studio web UI for local testing."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>BATU Studio</title>
      <style>
        :root {
          --bg: #0b1020;
          --panel: #121b2f;
          --panel-alt: #1b2947;
          --line: #2e446d;
          --text: #edf4ff;
          --muted: #9aacd0;
          --green: #26c281;
          --orange: #f5a623;
          --red: #ff5d62;
          --purple: #9a7dff;
          --blue: #58a6ff;
        }
        * { box-sizing: border-box; }
        body {
          margin: 0;
          background: linear-gradient(180deg, #090d18 0%, #111a2c 100%);
          font-family: Arial, sans-serif;
          color: var(--text);
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 24px; }
        .header {
          display: flex; justify-content: space-between; align-items: center; padding: 20px 0 28px;
          border-bottom: 1px solid var(--line);
        }
        .brand { font-size: 2rem; font-weight: bold; color: var(--purple); }
        .grid { display: grid; grid-template-columns: 1.1fr 1.6fr; gap: 20px; margin-top: 24px; }
        .panel {
          background: rgba(18,27,47,0.92);
          border: 1px solid var(--line);
          border-radius: 16px;
          padding: 20px;
        }
        .panel h3 { margin-top: 0; color: var(--blue); }
        textarea, input, select, button {
          width: 100%; border-radius: 10px; border: 1px solid var(--line);
          background: var(--panel-alt); color: var(--text); padding: 10px 12px; margin-top: 10px;
        }
        button {
          background: linear-gradient(135deg, var(--blue), var(--purple));
          border: none; cursor: pointer; font-weight: bold;
        }
        .secondary { background: rgba(38, 194, 129, 0.18); }
        .danger { background: rgba(255, 93, 98, 0.2); }
        .row { display: flex; gap: 12px; margin: 12px 0; }
        .task-item {
          background: rgba(255,255,255,0.03); border: 1px solid var(--line); border-radius: 10px;
          padding: 12px; margin-top: 10px; cursor: pointer;
        }
        .task-item.active { border-color: var(--green); box-shadow: 0 0 0 1px rgba(38,194,129,.4); }
        .badge {
          display: inline-block; padding: 4px 8px; border-radius: 999px; font-size: 11px; font-weight: bold;
          margin-right: 8px;
        }
        .badge.plan { background: rgba(88,166,255,0.15); color: var(--blue); }
        .badge.exec { background: rgba(245,166,35,0.15); color: var(--orange); }
        .badge.ok { background: rgba(38,194,129,0.15); color: var(--green); }
        .badge.fail { background: rgba(255,93,98,0.15); color: var(--red); }
        .muted { color: var(--muted); }
        .steps { margin-top: 16px; }
        .step-item {
          background: rgba(255,255,255,.02); border:1px solid var(--line); border-radius: 10px; padding: 12px; margin-top: 10px;
        }
        code { background: rgba(255,255,255,.04); padding: 2px 6px; border-radius: 6px; }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <div class="brand">BATU Studio</div>
          <div class="muted">Goal → Plan → Permission → Execution → Verification</div>
        </div>

        <div class="grid">
          <div class="panel">
            <h3>Create Task</h3>
            <textarea id="goal" rows="6" placeholder="Describe the goal of the agent..."></textarea>
            <button id="createTaskBtn">Create Task</button>
            <div class="row">
              <button id="loadTasksBtn" class="secondary">Refresh Tasks</button>
            </div>
            <div id="taskList"></div>
          </div>

          <div class="panel">
            <h3>Selected Task</h3>
            <div id="taskDetail">Select a task to inspect it.</div>
          </div>
        </div>
      </div>

      <script>
        const state = {
          tasks: [],
          activeTask: null,
          permissions: ['PLAN', 'LOCAL_READ', 'LOCAL_WRITE', 'EXTERNAL_ACCESS', 'PUBLISH', 'FINANCIAL_ACTION']
        };

        async function api(path, method = 'GET', body = null) {
          const headers = { 'Content-Type': 'application/json' };
          const options = { method, headers };
          if (body) options.body = JSON.stringify(body);

          const token = localStorage.getItem('batu_token');
          if (token) headers['Authorization'] = `Bearer ${token}`;

          const response = await fetch(path, options);
          if (!response.ok) {
            const text = await response.text();
            throw new Error(text || 'Request failed');
          }
          return response.headers.get('content-type')?.includes('application/json') ? response.json() : response.text();
        }

        async function loginDemo() {
          try {
            const res = await api('/api/v1/auth/register', 'POST', {
              username: 'batu_admin',
              email: 'admin@batu.local',
              password: 'SecurePass123!'
            });
            console.log('register ok', res);
          } catch (err) {
            console.log('register may already exist', err.message);
          }

          try {
            const res = await api('/api/v1/auth/login', 'POST', {
              username: 'batu_admin',
              password: 'SecurePass123!'
            });
            localStorage.setItem('batu_token', res.access_token);
            console.log('login ok', res);
          } catch (err) {
            console.log('login failed', err.message);
          }
        }

        async function loadTasks() {
          try {
            const response = await api('/api/v1/tasks');
            state.tasks = response.tasks || [];
            if (!state.activeTask && state.tasks.length) {
              state.activeTask = state.tasks[0];
            }
            renderTasks();
            renderTaskDetail();
          } catch (err) {
            document.getElementById('taskDetail').innerHTML = '<div class="muted">' + err.message + '</div>';
          }
        }

        async function createTask() {
          const goal = document.getElementById('goal').value.trim();
          if (!goal) return;
          const created = await api('/api/v1/tasks', 'POST', { goal, context: {} });
          state.activeTask = created;
          state.tasks.unshift(created);
          renderTasks();
          renderTaskDetail();
          document.getElementById('goal').value = '';
        }

        async function createPlan() {
          const task = state.activeTask;
          if (!task) return;
          const steps = [
            { action: 'create_summary', input: { text: task.goal } },
            { action: 'read_local_file', input: { path: 'README.md' } },
            { action: 'write_local_file', input: { path: 'batu_output.txt', content: 'BATU task output\n' + task.goal } }
          ];
          const updated = await api('/api/v1/tasks/' + task.id + '/plan', 'POST', { steps });
          task.state = updated.state;
          task.plan = updated.plan;
          task.statusMessage = updated.statusMessage;
          renderTaskDetail();
          loadTasks();
        }

        async function executeTask() {
          const task = state.activeTask;
          if (!task) return;
          const payload = { granted_permissions: ['PLAN', 'LOCAL_READ', 'LOCAL_WRITE'] };
          const updated = await api('/api/v1/tasks/' + task.id + '/execute', 'POST', payload);
          state.activeTask = updated;
          renderTaskDetail();
          loadTasks();
        }

        async function approveTask() {
          const task = state.activeTask;
          if (!task) return;
          const updated = await api('/api/v1/tasks/' + task.id + '/approve', 'POST', {
            confirmed: true,
            taskId: task.id,
            actions: ['EXTERNAL_ACCESS', 'PUBLISH'],
            notes: 'Approved by local BATU admin'
          });
          state.activeTask = updated;
          renderTaskDetail();
          loadTasks();
        }

        async function verifyTask() {
          const task = state.activeTask;
          if (!task) return;
          const updated = await api('/api/v1/tasks/' + task.id + '/verify', 'POST', {
            passed: true,
            evidence: [
              { description: 'Task completed successfully', source: 'BATU Studio UI', metadata: { taskId: task.id } },
              { description: 'Output and logs recorded', source: 'local execution log', metadata: { taskId: task.id } }
            ]
          });
          state.activeTask = updated;
          renderTaskDetail();
          loadTasks();
        }

        function renderTasks() {
          const list = document.getElementById('taskList');
          if (!state.tasks.length) {
            list.innerHTML = '<div class="muted">No tasks yet.</div>';
            return;
          }
          list.innerHTML = state.tasks.map(task => `
            <div class="task-item ${state.activeTask && state.activeTask.id === task.id ? 'active' : ''}" data-id="${task.id}">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>${task.goal.slice(0, 40)}${task.goal.length > 40 ? '...' : ''}</strong>
                <span class="badge ${task.state === 'VERIFIED' ? 'ok' : task.state === 'FAILED' ? 'fail' : task.state === 'EXECUTING' ? 'exec' : 'plan'}">${task.state}</span>
              </div>
              <div class="muted">${task.createdAt}</div>
            </div>
          `).join('');
          list.querySelectorAll('.task-item').forEach(el => {
            el.onclick = () => {
              state.activeTask = state.tasks.find(task => task.id === el.dataset.id) || null;
              renderTasks();
              renderTaskDetail();
            };
          });
        }

        function renderTaskDetail() {
          const detail = document.getElementById('taskDetail');
          const task = state.activeTask;
          if (!task) {
            detail.innerHTML = '<div class="muted">No active task.</div>';
            return;
          }

          const planHtml = (task.plan || []).map(step => `
            <div class="step-item">
              <strong>${step.action}</strong><br>
              <span class="muted">Status: ${step.status}</span><br>
              <code>${JSON.stringify(step.input)}</code>
            </div>
          `).join('') || '<div class="muted">No plan created yet.</div>';

          const resultsHtml = (task.results || []).map(result => `
            <div class="step-item">
              <strong>${result.action}</strong><br>
              <code>${JSON.stringify(result.output)}</code>
            </div>
          `).join('') || '<div class="muted">No execution results yet.</div>';

          detail.innerHTML = `
            <div><span class="badge ${task.state === 'VERIFIED' ? 'ok' : task.state === 'FAILED' ? 'fail' : task.state === 'EXECUTING' ? 'exec' : 'plan'}">${task.state}</span></div>
            <h4>${task.goal}</h4>
            <div class="muted">${task.statusMessage || 'No status message.'}</div>
            <div class="row">
              <button onclick="createPlan()">Create Plan</button>
              <button class="secondary" onclick="executeTask()">Execute</button>
            </div>
            <div class="row">
              <button class="secondary" onclick="approveTask()">Approve</button>
              <button class="secondary" onclick="verifyTask()">Verify</button>
            </div>
            <div class="steps">
              <h4>Plan</h4>
              ${planHtml}
            </div>
            <div class="steps">
              <h4>Results</h4>
              ${resultsHtml}
            </div>
          `;
        }

        document.getElementById('createTaskBtn').onclick = createTask;
        document.getElementById('loadTasksBtn').onclick = loadTasks;
        loginDemo().then(loadTasks);
      </script>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )

