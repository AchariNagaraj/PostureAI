# ml/api/analytics_router.py
"""FastAPI Router for Phase 9 Analytics & Reports endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from ..persistence.db import AsyncSessionLocal
from ..persistence.models import User
from ..analytics import service as analytics_service
from .auth_router import get_current_user

router = APIRouter(prefix="/api", tags=["Analytics & Reports"])


@router.get("/analytics/summary")
async def get_summary_analytics(current_user: User = Depends(get_current_user)):
    """Return summary analytics for current user's monitoring sessions."""
    try:
        async with AsyncSessionLocal() as session:
            data = await analytics_service.get_summary_analytics(session, user_id=current_user.id)
            return JSONResponse(content=data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database query failure: {exc}")


@router.get("/analytics/postures")
async def get_posture_analytics(
    session_id: Optional[int] = Query(None, description="Optional session filter"),
    current_user: User = Depends(get_current_user),
):
    """Return posture observation counts, timestamp-derived durations, and transition matrix for current user."""
    try:
        async with AsyncSessionLocal() as session:
            data = await analytics_service.get_posture_analytics(session, session_id=session_id, user_id=current_user.id)
            return JSONResponse(content=data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database query failure: {exc}")


@router.get("/analytics/sessions")
async def get_sessions_list(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
):
    """Return paginated session summaries for current user."""
    try:
        async with AsyncSessionLocal() as session:
            data = await analytics_service.get_session_analytics_list(session, user_id=current_user.id, limit=limit, offset=offset)
            return JSONResponse(content=data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database query failure: {exc}")


@router.get("/analytics/sessions/{session_id}")
async def get_session_detail(
    session_id: int,
    current_user: User = Depends(get_current_user),
):
    """Return detailed timeline series, transitions, and alerts for a specific session of current user."""
    try:
        async with AsyncSessionLocal() as session:
            data = await analytics_service.get_single_session_detail(session, session_id=session_id, user_id=current_user.id)
            if not data:
                raise HTTPException(status_code=404, detail=f"Session #{session_id} not found.")
            return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database query failure: {exc}")


@router.get("/reports/sessions/{session_id}")
async def get_session_report(
    session_id: int,
    current_user: User = Depends(get_current_user),
):
    """Return structured inspection report payload for a specific session of current user."""
    try:
        async with AsyncSessionLocal() as session:
            data = await analytics_service.get_session_report(session, session_id=session_id, user_id=current_user.id)
            if not data:
                raise HTTPException(status_code=404, detail=f"Session #{session_id} not found.")
            return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database query failure: {exc}")

