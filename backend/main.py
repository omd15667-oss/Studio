from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv

from security.authentication import AuthenticationManager
from security.encryption import get_encryption_manager
from security.audit import AuditLogger

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

# ============= In-Memory Storage (v0.1) =============

users_db = {}
notes_db = {}
user_counter = 0
note_counter = 0

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
    
    try:
        payload = AuthenticationManager.verify_token(credentials.credentials)
        user_id = payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
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
    try:
        payload = AuthenticationManager.verify_token(credentials.credentials)
        user_id = payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
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
    try:
        payload = AuthenticationManager.verify_token(credentials.credentials)
        user_id = payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
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
    try:
        payload = AuthenticationManager.verify_token(credentials.credentials)
        user_id = payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
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
    try:
        payload = AuthenticationManager.verify_token(credentials.credentials)
        user_id = payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
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

# ============= Privacy & Audit Endpoints =============

@app.get("/api/v1/audit/logs", tags=["Privacy"])
async def get_audit_logs(credentials: HTTPAuthCredentials = Depends(security)):
    """Get user's audit logs"""
    try:
        payload = AuthenticationManager.verify_token(credentials.credentials)
        user_id = payload["user_id"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    
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
            "api": "/api/v1"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )