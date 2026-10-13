from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session
from typing import List

from db.session import get_db
from db import crud, models
from batu_core import BATUEngine, PERMISSIONS
from security.authentication import AuthenticationManager
from security.audit import AuditLogger

router = APIRouter()
security = HTTPBearer()
engine = BATUEngine()
audit_logger = AuditLogger()

# Register actions into BATU engine from DB (starter set)
engine.register_action("create_summary", lambda payload: {"summary": str(payload.get('text') or '')[:500], "character_count": len(str(payload.get('text') or ''))}, PERMISSIONS['PLAN'])
engine.register_action("read_local_file", lambda payload: {"path": payload.get('path'), "content_preview": 'preview' }, PERMISSIONS['LOCAL_READ'])
engine.register_action("write_local_file", lambda payload: {"path": payload.get('path'), "written": True }, PERMISSIONS['LOCAL_WRITE'])


def get_user_id_from_token(credentials: HTTPAuthCredentials):
    try:
        payload = AuthenticationManager.verify_token(credentials.credentials)
        return payload["user_id"]
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


@router.post('/api/v2/tasks', tags=['BATU'])
def api_create_task(req: dict, credentials: HTTPAuthCredentials = Depends(security), db: Session = Depends(get_db)):
    user_id = get_user_id_from_token(credentials)
    task = crud.create_task(db, user_id=user_id, goal=req.get('goal'), context=req.get('context') or {})
    crud.add_audit(db, 'TASK_CREATED', {'taskId': task.id, 'goal': task.goal})
    return task


@router.post('/api/v2/tasks/{task_id}/plan', tags=['BATU'])
def api_create_plan(task_id: str, req: dict, credentials: HTTPAuthCredentials = Depends(security), db: Session = Depends(get_db)):
    get_user_id_from_token(credentials)
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    steps = req.get('steps') or []
    # validate actions exist in engine
    for s in steps:
        if s.get('action') not in engine.registry:
            raise HTTPException(status_code=400, detail=f"Unknown action: {s.get('action')}")
    task = crud.add_plan_steps(db, task, steps)
    crud.record_task_state(db, task, 'PLANNED', 'Plan created; awaiting permission checks.')
    crud.add_audit(db, 'PLAN_CREATED', {'taskId': task.id, 'steps': [s.get('action') for s in steps]})
    return task


@router.post('/api/v2/tasks/{task_id}/execute', tags=['BATU'])
def api_execute_task(task_id: str, req: dict, credentials: HTTPAuthCredentials = Depends(security), db: Session = Depends(get_db)):
    get_user_id_from_token(credentials)
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    # convert DB task to engine task dict
    engine_task = {
        'id': task.id,
        'goal': task.goal,
        'state': task.state,
        'createdAt': task.created_at,
        'plan': [{'id': s.id, 'action': s.action, 'input': {} , 'status': s.status} for s in task.plan_steps],
        'results': [],
        'evidence': [],
        'approval': None,
        'context': {},
        'statusMessage': task.status_message or ''
    }
    updated = engine.execute_task(engine_task, req.get('granted_permissions') or [])
    # persist status and results
    crud.record_task_state(db, task, updated.get('state') or task.state, updated.get('statusMessage'))
    for res in updated.get('results'):
        crud.add_result(db, task, res.get('stepId'), res.get('action'), res.get('output'))
    crud.add_audit(db, 'TASK_EXECUTED', {'taskId': task.id, 'state': updated.get('state')})
    return crud.get_task(db, task_id)


@router.post('/api/v2/tasks/{task_id}/verify', tags=['BATU'])
def api_verify_task(task_id: str, req: dict, credentials: HTTPAuthCredentials = Depends(security), db: Session = Depends(get_db)):
    get_user_id_from_token(credentials)
    task = crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Task not found')
    if req.get('passed') is not True:
        crud.record_task_state(db, task, 'FAILED', 'Verification failed or evidence is missing.')
        crud.add_audit(db, 'VERIFICATION_FAILED', {'taskId': task.id})
        return crud.get_task(db, task_id)
    items = req.get('evidence') or []
    crud.add_evidence(db, task, items)
    crud.record_task_state(db, task, 'VERIFIED', 'Task verified with recorded evidence.')
    crud.add_audit(db, 'TASK_VERIFIED', {'taskId': task.id, 'evidenceCount': len(items)})
    return crud.get_task(db, task_id)


@router.get('/api/v2/actions', tags=['BATU'])
def api_list_actions(db: Session = Depends(get_db)):
    acts = crud.list_actions(db)
    return {'actions': [{ 'name': a.name, 'required_permission': a.required_permission } for a in acts]}


@router.get('/api/v2/audit', tags=['BATU'])
def api_get_audit(db: Session = Depends(get_db)):
    logs = db.query(models.AuditLog).order_by(models.AuditLog.timestamp.desc()).limit(500).all()
    return {'logs': [{ 'id': l.id, 'timestamp': l.timestamp, 'event': l.event, 'details': l.details_json } for l in logs]}
