"""
API-key auth dependency for Guardian Agent telemetry ingestion.

Guardian Agents (see /guardian-agent) are standalone processes, not logged-in
operators, so they authenticate with a static shared secret rather than a
user JWT — sent via header: X-Agent-Api-Key: <key>.

Usage in a router:
    from app.core.agent_auth import verify_agent_api_key

    @router.post("/telemetry")
    async def ingest_telemetry(payload: ..., _: str = Depends(verify_agent_api_key)):
        ...
"""
from fastapi import Header, HTTPException, status

from app.core.config import settings


async def verify_agent_api_key(x_agent_api_key: str | None = Header(default=None)) -> str:
    if not settings.AGENT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Guardian Agent telemetry ingestion is disabled: AGENT_API_KEY is not configured on the server.",
        )
    if not x_agent_api_key or x_agent_api_key != settings.AGENT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Guardian Agent API key.",
        )
    return x_agent_api_key
