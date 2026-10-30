import asyncio
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, RedirectResponse

from ..inference.inference_service import InferenceEngine
from ..inference.pose_processor import PoseProcessor
from ..inference.target_tracker import TargetTracker
from ..inference.viewpoint_estimator import estimate_viewpoint
from ..persistence import service as persistence_service
from ..persistence.db import engine as db_engine, Base
from .analytics_router import router as analytics_router
from .auth_router import router as auth_router, signer
from ..persistence.service import ConflictError

app = FastAPI()
app.include_router(analytics_router)
app.include_router(auth_router)


@app.on_event("startup")
async def on_startup():
    # Create tables if they do not exist.
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def on_shutdown():
    await db_engine.dispose()


@app.get("/")
async def root():
    """Root endpoint redirecting to Swagger UI docs."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return JSONResponse(content={"status": "ok"})


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, mode: str = "auto"):
    """WebSocket streaming structured monitoring events."""
    await websocket.accept()
    
    # Extract user_id from auth cookie if present
    user_id = None
    token = websocket.cookies.get("session")
    if token:
        try:
            user_id = int(signer.unsign(token, max_age=86400).decode())
        except Exception:
            user_id = None

    engine = InferenceEngine()
    pose_processor = PoseProcessor()
    target_tracker = TargetTracker()
    websocket.session_id = None


    try:
        if mode == "demo":
            # Deterministic simulation loop for automated tests
            for step in range(7):
                ts = time.time()
                if step < 3:
                    label = "TUP"
                    probabilities = {"TUP": 0.92, "TLF": 0.04, "TLB": 0.04}
                else:
                    label = "TLF"
                    probabilities = {"TLF": 0.90, "TUP": 0.05, "TLB": 0.05}
                result = engine.process(timestamp=ts, label=label, probabilities=probabilities)
                if result["alert_event"]:
                    event_type = "ALERT"
                    payload = result["alert_event"]
                else:
                    event_type = "POSTURE_UPDATE"
                    payload = {
                        "timestamp": ts,
                        "posture": label,
                        "confidence": result["confidence"],
                        "risk_score": result["risk_score"],
                        "risk_level": result["risk_level"],
                        "temporal_state": result["temporal_state"],
                        "viewpoint": result.get("viewpoint", "FRONT"),
                        "tracking_state": result.get("tracking_state", "TRACKING"),
                        "pose_valid": result.get("pose_valid", True),
                    }
                asyncio.create_task(persistence_service.persist_event(event_type, payload, user_id=user_id))
                await websocket.send_json({"type": event_type, "payload": payload})
                await asyncio.sleep(0.05)
            return

        # Interactive loop for real webcam frames
        while True:
            try:
                message = await websocket.receive_json()
            except (WebSocketDisconnect, RuntimeError):
                break
            except Exception as exc:
                print(f"[WebSocket] Receive error: {exc}")
                break
            msg_type = message.get("type")

            # ----------------------------------------------------------
            # Session control messages
            # ----------------------------------------------------------
            if msg_type == "START_SESSION":
                request_id = message.get("request_id")
                try:
                    session_id = await persistence_service.start_session(user_id=user_id, request_id=request_id)
                    websocket.session_id = session_id
                    await websocket.send_json({"type": "SESSION_STARTED", "session_id": session_id})
                except ConflictError as e:
                    await websocket.send_json({"type": "SESSION_CONFLICT", "message": str(e)})
                continue
            elif msg_type == "RESUME_SESSION":
                sess_id = message.get("session_id")
                if not sess_id:
                    await websocket.send_json({"type": "ERROR", "message": "session_id required"})
                    continue
                try:
                    valid_id = await persistence_service.resume_session(user_id=user_id, session_id=int(sess_id))
                    websocket.session_id = valid_id
                    await websocket.send_json({"type": "SESSION_RESUMED", "session_id": valid_id})
                except Exception as e:
                    await websocket.send_json({"type": "ERROR", "message": str(e)})
                continue
            elif msg_type == "STOP_MONITORING":
                if websocket.session_id is not None:
                    await persistence_service.close_session(user_id=user_id, session_id=websocket.session_id)
                    await websocket.send_json({"type": "SESSION_CLOSED", "session_id": websocket.session_id})
                    websocket.session_id = None
                continue
            # ----------------------------------------------------------
            # Calibration protocol messages
            # ----------------------------------------------------------
            if msg_type == "START_CALIBRATION":
                engine.start_calibration()
                await websocket.send_json({
                    "type": "CALIBRATION_STATE",
                    "payload": {
                        "calibration_state": "CALIBRATING",
                        "message": "Calibration started — sit naturally upright",
                    }
                })
                continue

            elif msg_type == "FINALIZE_CALIBRATION":
                success = engine.finalize_calibration()
                if success:
                    await websocket.send_json({
                        "type": "CALIBRATION_STATE",
                        "payload": {
                            "calibration_state": "CALIBRATION_COMPLETE",
                            "message": "Calibration complete — baseline established",
                            "calibration_info": engine.calibration.get_debug_info(),
                        }
                    })
                else:
                    await websocket.send_json({
                        "type": "CALIBRATION_STATE",
                        "payload": {
                            "calibration_state": "CALIBRATION_FAILED",
                            "message": f"Calibration failed — need at least {5} valid samples, got {engine.calibration.sample_count}",
                            "calibration_info": engine.calibration.get_debug_info(),
                        }
                    })
                continue

            elif msg_type == "SELECT_TARGET":
                target_id = message.get("target_id")
                click_x = message.get("click_x")
                click_y = message.get("click_y")
                click_coords = (click_x, click_y) if (click_x is not None and click_y is not None) else None
                
                # Store preference or execute selection on target_tracker
                if target_id is not None or click_coords is not None:
                    # Target selection command will be applied on next frame candidate set or stored
                    pending_target_id = target_id
                    pending_click_coords = click_coords
                await websocket.send_json({"type": "TARGET_SELECTION_ACK", "target_id": target_id})
                continue

            elif msg_type == "RESET_TARGET" or msg_type == "CHANGE_TARGET":
                target_tracker.reset()
                engine.risk_engine._reset_state()
                await websocket.send_json({"type": "TARGET_RESET_ACK"})
                continue

            elif msg_type == "FRAME":
                client_ts = message.get("timestamp", time.time())
                frame_data = message.get("frame")

                if not frame_data:
                    continue

                # 1. Pose Candidate extraction
                candidates = pose_processor.process_base64_candidates(frame_data)

                # 2. Target selection & continuity tracking
                manual_id = message.get("select_target_id")
                click_x = message.get("click_x")
                click_y = message.get("click_y")
                click_coords = (click_x, click_y) if (click_x is not None and click_y is not None) else None

                target_info = target_tracker.process_candidates(
                    candidates,
                    manual_target_id=manual_id,
                    click_coords=click_coords,
                )

                # 3. Gated Posture Inference & Risk Engine
                if target_info["target_selected"] and target_info["tracking_state"] in ("TARGET_TRACKING", "TRACKING") and target_info["pose_valid"] and target_info["active_landmarks"]:
                    vp = estimate_viewpoint(target_info["active_landmarks"])
                    result = engine.process(
                        timestamp=client_ts,
                        landmarks=target_info["active_landmarks"],
                        viewpoint=vp,
                        tracking_state=target_info["tracking_state"],
                        pose_valid=True,
                    )
                else:
                    # Invalid pose / target lost / awaiting selection guard
                    result = engine.process(
                        timestamp=client_ts,
                        label="TUP",
                        probabilities={"TUP": 1.0},
                        confidence=0.0,
                        viewpoint="UNKNOWN",
                        tracking_state=target_info["tracking_state"],
                        pose_valid=False,
                        invalid_state=target_info["tracking_state"],
                    )

                landmarks_data = None
                if target_info.get("active_landmarks"):
                    landmarks_data = [
                        {"x": float(lm.x), "y": float(lm.y), "z": float(getattr(lm, "z", 0.0))}
                        for lm in target_info["active_landmarks"]
                    ]

                # During calibration, never emit ALERT events
                is_calibrating = engine.calibration_state == engine.CALIB_CALIBRATING

                if not is_calibrating and result["alert_event"]:
                    event_type = "ALERT"
                    payload = result["alert_event"]
                    payload["pose_landmarks"] = landmarks_data
                    payload["posture_evaluation"] = result.get("posture_evaluation")
                else:
                    event_type = "POSTURE_UPDATE"
                    payload = {
                        "timestamp": client_ts,
                        "posture": result["posture"],
                        "class_probabilities": result["class_probabilities"],
                        "confidence": result["confidence"],
                        "viewpoint": result["viewpoint"],
                        "person_state": target_info["person_state"],
                        "tracking_state": target_info["tracking_state"],
                        "target_selected": target_info["target_selected"],
                        "target_id": target_info["target_id"],
                        "target_confidence": target_info["target_confidence"],
                        "target_bbox": target_info["target_bbox"],
                        "candidates": target_info["candidates"],
                        "reselection_required": target_info.get("reselection_required", False),
                        "pose_valid": target_info["pose_valid"],
                        "risk_score": result["risk_score"],
                        "risk_level": result["risk_level"],
                        "temporal_state": result["temporal_state"],
                        "alert_event": None,
                        "recommendation": result.get("recommendation"),
                        "posture_evaluation": result.get("posture_evaluation"),
                        "pose_landmarks": landmarks_data,
                        "calibration_state": result.get("calibration_state"),
                        "calibration_info": result.get("calibration_info"),
                    }
                    if target_info.get("voice_message"):
                        payload["voice_message"] = target_info["voice_message"]

                # Non-blocking persistence — skip during calibration
                if not is_calibrating:
                    asyncio.create_task(persistence_service.persist_event(event_type, payload, user_id=user_id, session_id=websocket.session_id))
                await websocket.send_json({"type": event_type, "payload": payload})

            elif msg_type == "DEMO":
                # Explicit DEMO mode command from client
                for step in range(7):
                    ts = time.time()
                    label = "TUP" if step < 3 else "TLF"
                    probabilities = {"TUP": 0.92, "TLF": 0.04, "TLB": 0.04} if step < 3 else {"TLF": 0.90, "TUP": 0.05, "TLB": 0.05}
                    result = engine.process(timestamp=ts, label=label, probabilities=probabilities)
                    event_type = "ALERT" if result["alert_event"] else "POSTURE_UPDATE"
                    payload = result["alert_event"] if result["alert_event"] else {
                        "timestamp": ts,
                        "posture": label,
                        "confidence": result["confidence"],
                        "risk_score": result["risk_score"],
                        "risk_level": result["risk_level"],
                        "temporal_state": result["temporal_state"],
                        "viewpoint": result.get("viewpoint", "FRONT"),
                        "tracking_state": result.get("tracking_state", "TRACKING"),
                        "pose_valid": result.get("pose_valid", True),
                    }
                    asyncio.create_task(persistence_service.persist_event(event_type, payload))
                    await websocket.send_json({"type": event_type, "payload": payload})
                    await asyncio.sleep(0.05)
                break

    except WebSocketDisconnect:
        await persistence_service.close_session()
    finally:
        pose_processor.close()
        target_tracker.reset()
