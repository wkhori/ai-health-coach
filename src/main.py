"""FastAPI application for the AI Health Coach."""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Any
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

import structlog
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.config import Settings, get_settings

logger = structlog.get_logger(__name__)

# --- Module-level singletons ---
_llm_instance: Any = None
_checkpointer: Any = None


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Initialize LLM, checkpointer, and repos on startup."""
    global _llm_instance, _checkpointer  # noqa: PLW0603

    try:
        settings = get_settings()
    except Exception:
        settings = None

    # Initialize LLM
    if settings and settings.anthropic_api_key:
        try:
            from langchain_anthropic import ChatAnthropic

            _llm_instance = ChatAnthropic(
                model=settings.llm_model,
                temperature=settings.llm_temperature,
                max_tokens=settings.llm_max_tokens,
                streaming=True,
            )
            logger.info("llm_initialized", model=settings.llm_model)
        except Exception:
            logger.warning("llm_init_failed", exc_info=True)

    # Initialize checkpointer (in-memory)
    from langgraph.checkpoint.memory import MemorySaver

    _checkpointer = MemorySaver()
    logger.info("checkpointer_initialized", type="memory")

    # Initialize repositories
    if settings:
        try:
            get_repos(settings)
            logger.info("repos_initialized")

            # Auto-seed if DB is empty
            from src.db.client import get_db

            conn = get_db(settings.database_path)
            cursor = conn.execute("SELECT COUNT(*) FROM profiles")
            count = cursor.fetchone()[0]
            if count == 0:
                from src.db.seed import seed_db

                seed_db(conn)
                logger.info("demo_data_seeded")
        except Exception:
            logger.warning("repos_init_failed", exc_info=True)

    yield


app = FastAPI(title="AI Health Coach", version="0.1.0", lifespan=lifespan)

# CORS — configured at module level (must be before startup)
try:
    _cors_settings = get_settings()
    _cors_origins = _cors_settings.cors_origin_list
except Exception:
    _cors_origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting state (in-memory sliding window)
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


# --- Request/Response models ---


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    phase: str
    safety_result: dict = {}


class ConsentRequest(BaseModel):
    consent_version: str = "1.0"


class ConsentResponse(BaseModel):
    status: str
    phase: str


class ProfileResponse(BaseModel):
    user_id: str
    profile_id: str
    display_name: str
    phase: str
    consent_given: bool


class GoalResponse(BaseModel):
    goals: list[dict]


class HealthResponse(BaseModel):
    status: str
    timestamp: str


class ConversationResponse(BaseModel):
    turns: list[dict]
    total: int


class ScheduledMessageRequest(BaseModel):
    user_id: str
    reminder_id: str
    attempt_number: int = 1


class AuthRegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class AdminPatient(BaseModel):
    user_id: str
    profile_id: str
    display_name: str
    phase: str
    last_message_at: str | None
    active_goals_count: int
    total_milestones: int
    completed_milestones: int
    adherence_pct: int
    alerts_count: int


class AdminPatientsResponse(BaseModel):
    patients: list[AdminPatient]


class AdminAlert(BaseModel):
    id: str
    user_id: str
    patient_name: str
    alert_type: str
    urgency: str
    message: str
    created_at: str


class AdminAlertsResponse(BaseModel):
    alerts: list[AdminAlert]


class AdminResetResponse(BaseModel):
    status: str
    patients_count: int


# --- Auth helpers ---


def _hash_password(password: str) -> str:
    """Hash a password with a random salt using PBKDF2."""
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + hash_bytes.hex()


def _verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash."""
    salt_hex, hash_hex = stored_hash.split(":")
    salt = bytes.fromhex(salt_hex)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return hash_bytes.hex() == hash_hex


# --- Auth dependency ---


async def get_current_user(request: Request) -> dict:
    """Validate token from Authorization header.

    Returns a dict with user_id extracted from the session token.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Look up token in sessions table
    try:
        settings = get_settings()
        from src.db.client import get_db

        conn = get_db(settings.database_path)
        cursor = conn.execute(
            "SELECT user_id FROM sessions WHERE token = ?", (token,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="Unauthorized")
        return {"user_id": row[0]}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Unauthorized") from exc


# --- Rate limiting ---


def check_rate_limit(user_id: str, max_per_minute: int = 10) -> None:
    """Check if user has exceeded rate limit using sliding window."""
    now = time.time()
    window_start = now - 60

    # Clean old entries
    _rate_limit_store[user_id] = [t for t in _rate_limit_store[user_id] if t > window_start]

    if len(_rate_limit_store[user_id]) >= max_per_minute:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": "60"},
        )

    _rate_limit_store[user_id].append(now)


# --- Graph factory ---

_graph_instance: Any = None
_repos: dict[str, Any] = {}


def get_graph() -> Any:
    """Get or create the compiled graph instance."""
    global _graph_instance  # noqa: PLW0603
    if _graph_instance is None:
        from src.graph.router import build_graph

        repos = get_repos()
        _graph_instance = build_graph(
            llm=_llm_instance,
            checkpointer=_checkpointer,
            repos=repos,
        )
    return _graph_instance


def get_repos(settings: Settings | None = None) -> dict[str, Any]:
    """Get or create repository instances."""
    global _repos  # noqa: PLW0603
    if not _repos:
        if settings is None:
            settings = get_settings()
        from src.db.client import get_db
        from src.db.repositories import (
            AlertRepository,
            ConversationRepository,
            GoalRepository,
            MilestoneRepository,
            ProfileRepository,
            ReminderRepository,
            SafetyAuditRepository,
            SummaryRepository,
        )

        conn = get_db(settings.database_path)
        _repos = {
            "profile": ProfileRepository(conn),
            "goal": GoalRepository(conn),
            "milestone": MilestoneRepository(conn),
            "reminder": ReminderRepository(conn),
            "conversation": ConversationRepository(conn),
            "safety_audit": SafetyAuditRepository(conn),
            "summary": SummaryRepository(conn),
            "alert": AlertRepository(conn),
        }
    return _repos


# --- Endpoints ---


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint -- no auth required."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
    )


@app.post("/api/auth/register", response_model=AuthResponse)
async def auth_register(body: AuthRegisterRequest) -> AuthResponse:
    """Register a new user and create a profile in PENDING phase."""
    settings = get_settings()
    from src.db.client import get_db

    conn = get_db(settings.database_path)

    # Check if email already exists
    cursor = conn.execute("SELECT id FROM users WHERE email = ?", (body.email,))
    if cursor.fetchone():
        raise HTTPException(status_code=409, detail="Email already registered")

    user_id = str(uuid4())
    password_hash = _hash_password(body.password)
    token = str(uuid4())
    profile_id = str(uuid4())
    display_name = body.name or body.email.split("@")[0]

    conn.execute(
        "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
        (user_id, body.email, password_hash),
    )
    conn.execute(
        "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
        (token, user_id),
    )
    conn.execute(
        "INSERT INTO profiles (id, user_id, display_name, phase) VALUES (?, ?, ?, ?)",
        (profile_id, user_id, display_name, "PENDING"),
    )
    conn.commit()

    return AuthResponse(
        token=token,
        user={"user_id": user_id, "email": body.email, "name": display_name},
    )


@app.post("/api/auth/login", response_model=AuthResponse)
async def auth_login(body: AuthLoginRequest) -> AuthResponse:
    """Login with email and password."""
    settings = get_settings()
    from src.db.client import get_db

    conn = get_db(settings.database_path)

    cursor = conn.execute(
        "SELECT id, email, password_hash FROM users WHERE email = ?", (body.email,)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id, email, password_hash = row[0], row[1], row[2]
    if not _verify_password(body.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create a new session token
    token = str(uuid4())
    conn.execute(
        "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
        (token, user_id),
    )
    conn.commit()

    # Get display name from profile
    profile_cursor = conn.execute(
        "SELECT display_name FROM profiles WHERE user_id = ?", (user_id,)
    )
    profile_row = profile_cursor.fetchone()
    display_name = profile_row[0] if profile_row else email.split("@")[0]

    return AuthResponse(
        token=token,
        user={"user_id": user_id, "email": email, "name": display_name},
    )


@app.post("/api/auth/me")
async def auth_me(
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    """Get the current authenticated user's info."""
    user_id = user.get("user_id", "")
    settings = get_settings()
    from src.db.client import get_db

    conn = get_db(settings.database_path)

    cursor = conn.execute("SELECT id, email FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    profile_cursor = conn.execute(
        "SELECT display_name FROM profiles WHERE user_id = ?", (user_id,)
    )
    profile_row = profile_cursor.fetchone()
    display_name = profile_row[0] if profile_row else row[1].split("@")[0]

    return {"user_id": row[0], "email": row[1], "name": display_name}


@app.post("/api/chat", dependencies=[Depends(get_current_user)])
async def chat_stream(
    request: Request,
    body: ChatRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> EventSourceResponse:
    """SSE streaming chat endpoint."""
    user_id = user.get("user_id", "")
    check_rate_limit(user_id)

    graph = get_graph()

    graph_input = {
        "messages": [{"role": "user", "content": body.message}],
        "user_id": user_id,
        "profile_id": "",
        "phase": "",
        "consent_given": False,
        "conversation_summary": "",
        "turn_count": 0,
        "active_goals": [],
        "adherence_summary": {},
        "safety_result": {},
        "is_scheduled_message": False,
        "scheduled_message_type": "",
        "response_text": "",
        "retry_count": 0,
    }

    config = {"configurable": {"thread_id": user_id}}

    async def event_generator():
        safety_emitted = False
        try:
            async for event in graph.astream_events(graph_input, config, version="v2"):
                kind = event.get("event", "")

                if kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk", None)
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        content = chunk.content
                        # Handle content block lists from newer Anthropic SDK
                        if isinstance(content, list):
                            content = "".join(
                                block.get("text", "") if isinstance(block, dict) else str(block)
                                for block in content
                            )
                        if content:
                            yield {
                                "event": "message",
                                "data": json.dumps({"type": "token", "content": content}),
                            }

                elif kind == "on_tool_start":
                    tool_name = event.get("name", "")
                    tool_input = event.get("data", {}).get("input", {})
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "tool_start",
                            "tool": tool_name,
                            "args": tool_input,
                        }),
                    }

                elif kind == "on_tool_end":
                    tool_name = event.get("name", "")
                    tool_output = event.get("data", {}).get("output", "")
                    # Extract content from ToolMessage or similar objects
                    if hasattr(tool_output, "content"):
                        result_text = tool_output.content
                    elif isinstance(tool_output, dict) and "content" in tool_output:
                        result_text = tool_output["content"]
                    else:
                        result_text = str(tool_output)
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "tool_end",
                            "tool": tool_name,
                            "result": result_text,
                        }),
                    }

                elif kind == "on_chain_end":
                    output = event.get("data", {}).get("output", {})
                    if isinstance(output, dict):
                        if "phase" in output:
                            new_phase = output["phase"]
                            yield {
                                "event": "message",
                                "data": json.dumps({
                                    "type": "phase_change",
                                    "phase": new_phase,
                                }),
                            }
                        sr = output.get("safety_result")
                        if (
                            not safety_emitted
                            and isinstance(sr, dict)
                            and sr.get("classification")
                            and sr.get("reasoning") != "No assistant message to check."
                        ):
                            safety_emitted = True
                            yield {
                                "event": "message",
                                "data": json.dumps({
                                    "type": "safety_result",
                                    "result": sr,
                                }),
                            }

            yield {
                "event": "message",
                "data": json.dumps({"type": "done"}),
            }

        except Exception as e:
            yield {
                "event": "message",
                "data": json.dumps({"type": "error", "message": str(e)}),
            }

    return EventSourceResponse(
        event_generator(),
        ping=15,
    )


@app.post("/api/chat/sync", response_model=ChatResponse)
async def chat_sync(
    body: ChatRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> ChatResponse:
    """Non-streaming chat fallback."""
    user_id = user.get("user_id", "")
    check_rate_limit(user_id)

    graph = get_graph()

    from langchain_core.messages import HumanMessage

    graph_input = {
        "messages": [HumanMessage(content=body.message)],
        "user_id": user_id,
        "profile_id": "",
        "phase": "",
        "consent_given": False,
        "conversation_summary": "",
        "turn_count": 0,
        "active_goals": [],
        "adherence_summary": {},
        "safety_result": {},
        "is_scheduled_message": False,
        "scheduled_message_type": "",
        "response_text": "",
        "retry_count": 0,
    }

    config = {"configurable": {"thread_id": user_id}}

    result = await graph.ainvoke(graph_input, config)

    return ChatResponse(
        response=result.get("response_text", ""),
        phase=result.get("phase", ""),
        safety_result=result.get("safety_result", {}),
    )


@app.post("/api/consent", response_model=ConsentResponse)
async def grant_consent(
    body: ConsentRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> ConsentResponse:
    """Grant consent for the wellness coaching program."""
    user_id = user.get("user_id", "")
    repos = get_repos()
    profile_repo = repos.get("profile")

    if not profile_repo:
        raise HTTPException(status_code=503, detail="Service unavailable")

    profile = profile_repo.get_by_user_id(UUID(user_id))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile_repo.update_consent(
        UUID(profile["id"]),
        body.consent_version,
    )

    # Transition to ONBOARDING if in PENDING
    new_phase = profile.get("phase", "PENDING")
    if new_phase == "PENDING":
        from src.models.enums import PhaseState

        profile_repo.update_phase(UUID(profile["id"]), PhaseState.ONBOARDING)
        new_phase = "ONBOARDING"

    return ConsentResponse(status="consent_granted", phase=new_phase)


@app.get("/api/profile", response_model=ProfileResponse)
async def get_profile(
    user: Annotated[dict, Depends(get_current_user)],
) -> ProfileResponse:
    """Get current user profile and phase."""
    user_id = user.get("user_id", "")
    repos = get_repos()
    profile_repo = repos.get("profile")

    if not profile_repo:
        raise HTTPException(status_code=503, detail="Service unavailable")

    profile = profile_repo.get_by_user_id(UUID(user_id))
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    consent_given = (
        profile.get("consent_given_at") is not None and profile.get("consent_revoked_at") is None
    )

    return ProfileResponse(
        user_id=str(profile.get("user_id", "")),
        profile_id=str(profile.get("id", "")),
        display_name=profile.get("display_name", ""),
        phase=profile.get("phase", "PENDING"),
        consent_given=consent_given,
    )


@app.get("/api/goals", response_model=GoalResponse)
async def get_goals(
    user: Annotated[dict, Depends(get_current_user)],
) -> GoalResponse:
    """Get user's goals and milestones."""
    user_id = user.get("user_id", "")
    repos = get_repos()
    goal_repo = repos.get("goal")

    if not goal_repo:
        raise HTTPException(status_code=503, detail="Service unavailable")

    goals = goal_repo.get_by_user(UUID(user_id))
    return GoalResponse(goals=goals)


@app.get("/api/conversation", response_model=ConversationResponse)
async def get_conversation(
    user: Annotated[dict, Depends(get_current_user)],
    limit: Annotated[int, Query(le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ConversationResponse:
    """Get conversation history (paginated)."""
    user_id = user.get("user_id", "")
    repos = get_repos()
    conversation_repo = repos.get("conversation")

    if not conversation_repo:
        raise HTTPException(status_code=503, detail="Service unavailable")

    turns = conversation_repo.get_recent_turns(UUID(user_id), limit=limit)
    total = conversation_repo.get_turn_count(UUID(user_id))

    return ConversationResponse(turns=turns, total=total)


@app.post("/api/webhooks/scheduled-message")
async def handle_scheduled_message(
    request: Request,
    body: ScheduledMessageRequest,
) -> dict:
    """Handle scheduled message webhook.

    Authenticated via shared webhook secret, not user JWT.
    """
    # Verify webhook secret
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = auth_header.removeprefix("Bearer ").strip()

    try:
        settings = get_settings()
        if token != settings.webhook_secret:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Unauthorized") from exc

    graph = get_graph()

    graph_input = {
        "messages": [],
        "user_id": body.user_id,
        "profile_id": "",
        "phase": "RE_ENGAGING",
        "consent_given": True,
        "conversation_summary": "",
        "turn_count": 0,
        "active_goals": [],
        "adherence_summary": {},
        "safety_result": {},
        "is_scheduled_message": True,
        "scheduled_message_type": str(body.attempt_number),
        "response_text": "",
        "retry_count": 0,
    }

    config = {"configurable": {"thread_id": body.user_id}}

    result = await graph.ainvoke(graph_input, config)

    return {
        "status": "sent",
        "response": result.get("response_text", ""),
        "user_id": body.user_id,
    }


# --- Admin endpoints (no auth — demo only) ---


@app.get("/api/admin/patients", response_model=AdminPatientsResponse)
async def admin_patients() -> AdminPatientsResponse:
    """Return all patient profiles with aggregated stats."""
    from src.db.client import get_db
    from src.db.repositories import (
        AlertRepository,
        GoalRepository,
        ProfileRepository,
    )

    settings = get_settings()
    conn = get_db(settings.database_path)
    profile_repo = ProfileRepository(conn)
    goal_repo = GoalRepository(conn)
    alert_repo = AlertRepository(conn)

    profiles = profile_repo.get_all()
    result: list[AdminPatient] = []

    for p in profiles:
        uid = UUID(p["user_id"])
        goals = goal_repo.get_active_goals(uid)
        total_milestones = 0
        completed_milestones = 0
        for g in goals:
            for m in g.get("milestones", []):
                total_milestones += 1
                if m.get("completed"):
                    completed_milestones += 1

        adherence_pct = (
            round(completed_milestones / total_milestones * 100)
            if total_milestones > 0
            else 0
        )

        result.append(
            AdminPatient(
                user_id=p["user_id"],
                profile_id=p["id"],
                display_name=p.get("display_name") or "Unknown",
                phase=p.get("phase", "PENDING"),
                last_message_at=p.get("last_message_at"),
                active_goals_count=len(goals),
                total_milestones=total_milestones,
                completed_milestones=completed_milestones,
                adherence_pct=adherence_pct,
                alerts_count=alert_repo.count_by_user(uid),
            )
        )

    return AdminPatientsResponse(patients=result)


@app.get("/api/admin/alerts", response_model=AdminAlertsResponse)
async def admin_alerts() -> AdminAlertsResponse:
    """Return all unacknowledged clinician alerts with patient names."""
    from src.db.client import get_db
    from src.db.repositories import AlertRepository

    settings = get_settings()
    conn = get_db(settings.database_path)
    alert_repo = AlertRepository(conn)
    alerts = alert_repo.get_unacknowledged_with_patient()

    return AdminAlertsResponse(
        alerts=[
            AdminAlert(
                id=a["id"],
                user_id=a["user_id"],
                patient_name=a.get("patient_name", "Unknown"),
                alert_type=a.get("alert_type", ""),
                urgency=a.get("urgency", "routine"),
                message=a.get("message", ""),
                created_at=a.get("created_at", ""),
            )
            for a in alerts
        ]
    )


@app.post("/api/admin/reset", response_model=AdminResetResponse)
async def admin_reset() -> AdminResetResponse:
    """Re-seed the database for demo recording."""
    from src.db.client import get_db
    from src.db.seed import seed_db

    settings = get_settings()
    conn = get_db(settings.database_path)

    # Drop all data
    tables = [
        "clinician_alerts",
        "safety_audit_log",
        "conversation_summaries",
        "conversation_turns",
        "reminders",
        "milestones",
        "goals",
        "profiles",
        "sessions",
        "users",
    ]
    for table in tables:
        conn.execute(f"DELETE FROM {table}")  # noqa: S608
    conn.commit()

    # Re-seed
    seed_db(conn)

    # Count patients
    count = conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]

    return AdminResetResponse(status="reset_complete", patients_count=count)
