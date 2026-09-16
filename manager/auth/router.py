from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from manager.auth.service import (
    AuthenticationError,
    authenticate,
)

router = APIRouter(
    prefix="/api/auth",
    tags=["authentication"],
)


class LoginRequest(BaseModel):
    username: str = Field(
        min_length=1,
        max_length=255,
    )

    password: str = Field(
        min_length=1,
        max_length=1024,
    )


@router.post("/login")
def login(payload: LoginRequest):
    try:
        return authenticate(
            payload.username,
            payload.password,
        )

    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={
                "WWW-Authenticate": "Credentials",
            },
        )
