import logging
from typing import Any, Dict, Optional, Tuple

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError
from pymongo.errors import DuplicateKeyError, PyMongoError
from starlette.datastructures import UploadFile

from app.database import get_database
from app.models.user_model import build_user_document
from app.resume_service import safe_process_resume
from app.schemas.user_schema import (
    SavedJobsResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.job_service import JobService
from app.utils.helpers import (
    create_access_token,
    decode_access_token,
    hash_password,
    serialize_mongo_document,
    verify_password,
)

router = APIRouter(prefix="/users", tags=["Users"])
security = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


async def _parse_registration_payload(
    request: Request,
) -> Tuple[UserRegisterRequest, Optional[UploadFile]]:
    payload_data: Dict[str, Any]
    resume: Optional[UploadFile] = None

    content_type = request.headers.get("content-type", "").lower()
    if "multipart/form-data" in content_type:
        try:
            form = await request.form()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid multipart form data. Ensure python-multipart is installed.",
            ) from exc

        resume_candidate = form.get("resume")
        if isinstance(resume_candidate, UploadFile):
            resume = resume_candidate

        payload_data = {
            "email": form.get("email"),
            "password": form.get("password"),
            "full_name": form.get("full_name"),
        }
    elif "application/json" in content_type:
        try:
            json_payload = await request.json()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload.",
            ) from exc

        if not isinstance(json_payload, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Registration payload must be a JSON object.",
            )
        payload_data = {
            "email": json_payload.get("email"),
            "password": json_payload.get("password"),
            "full_name": json_payload.get("full_name"),
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Registration expects multipart/form-data or application/json.",
        )

    try:
        payload = UserRegisterRequest(**payload_data)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=jsonable_encoder(exc.errors()),
        )
    return payload, resume


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    token = credentials.credentials
    try:
        user_id = decode_access_token(token)
        object_id = ObjectId(user_id)
    except (ValueError, InvalidId):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.")

    db = get_database()
    try:
        user = await db.users.find_one({"_id": object_id})
    except PyMongoError as exc:
        logger.exception("Database lookup failed during auth for user_id=%s error=%s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please try again.",
        ) from exc
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return serialize_mongo_document(user)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description=(
        "Creates a user account with hashed password storage. "
        "Accepts multipart/form-data (optional resume PDF) or application/json."
    ),
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["email", "password"],
                        "properties": {
                            "full_name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "password": {"type": "string"},
                            "resume": {"type": "string", "format": "binary"},
                        },
                    }
                },
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["email", "password"],
                        "properties": {
                            "full_name": {"type": "string"},
                            "email": {"type": "string", "format": "email"},
                            "password": {"type": "string"},
                        },
                    }
                },
            },
        }
    },
)
async def register_user(
    request: Request,
    background_tasks: BackgroundTasks,
) -> UserResponse:
    payload, resume = await _parse_registration_payload(request=request)

    db = get_database()
    normalized_email = payload.email.lower().strip()
    hashed_password = hash_password(payload.password)
    user_doc = build_user_document(
        email=normalized_email,
        hashed_password=hashed_password,
        full_name=payload.full_name,
    )
    try:
        result = await db.users.insert_one(user_doc)
        created_user = await db.users.find_one({"_id": result.inserted_id})
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists.")
    except PyMongoError as exc:
        logger.exception("Registration database error for email=%s error=%s", normalized_email, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please try again.",
        ) from exc

    if created_user is None:
        logger.error("Inserted user missing on readback for email=%s", normalized_email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed. Please try again.",
        )

    serialized = serialize_mongo_document(created_user)
    serialized["saved_jobs_count"] = len(serialized.get("saved_jobs", []))

    if resume is not None and (resume.filename or "").strip():
        try:
            file_bytes = await resume.read()
            background_tasks.add_task(
                safe_process_resume,
                db=db,
                user_id=str(result.inserted_id),
                name=payload.full_name,
                email=normalized_email,
                filename=resume.filename,
                content_type=resume.content_type,
                file_bytes=file_bytes,
            )
        except Exception as exc:  # pragma: no cover - safe path
            logger.exception(
                "Failed to queue resume processing for user_id=%s error=%s",
                result.inserted_id,
                exc,
            )

    return UserResponse(**serialized)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Validates user credentials and returns a JWT bearer token.",
)
async def login_user(payload: UserLoginRequest) -> TokenResponse:
    db = get_database()
    try:
        user = await db.users.find_one({"email": payload.email.lower().strip()})
    except PyMongoError as exc:
        logger.exception("Login database error for email=%s error=%s", payload.email, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please try again.",
        ) from exc

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(str(user["_id"]))
    return TokenResponse(access_token=token)


@router.get(
    "/{user_id}/saved-jobs",
    response_model=SavedJobsResponse,
    summary="Get saved jobs by user ID",
    description="Returns all jobs saved by the authenticated user.",
)
async def get_saved_jobs(
    user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> SavedJobsResponse:
    if current_user["_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this resource.")

    job_service = JobService(get_database())
    try:
        result = await job_service.get_saved_jobs_for_user(user_id)
    except PyMongoError as exc:
        logger.exception("Failed loading saved jobs for user_id=%s error=%s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Please try again.",
        ) from exc
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return SavedJobsResponse(**result)
