"""Optional GitHub OAuth — set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET to enable."""

from __future__ import annotations

import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from backend.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

_oauth_states: dict[str, float] = {}


def oauth_enabled() -> bool:
    return bool(settings.github_client_id and settings.github_client_secret)


@router.get("/github")
async def github_login(request: Request):
    if not oauth_enabled():
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured")
    state = secrets.token_urlsafe(16)
    _oauth_states[state] = 1.0
    params = urlencode(
        {
            "client_id": settings.github_client_id,
            "redirect_uri": f"{settings.app_base_url}/api/auth/github/callback",
            "scope": "read:user",
            "state": state,
        }
    )
    return RedirectResponse(f"https://github.com/login/oauth/authorize?{params}")


@router.get("/github/callback")
async def github_callback(code: str, state: str):
    if not oauth_enabled():
        raise HTTPException(status_code=501, detail="GitHub OAuth not configured")
    if state not in _oauth_states:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    del _oauth_states[state]

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="OAuth token exchange failed")

        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        user_resp.raise_for_status()
        user = user_resp.json()

    username = user.get("login", "github-user")
    return RedirectResponse(f"{settings.app_base_url}/?user={username}")
