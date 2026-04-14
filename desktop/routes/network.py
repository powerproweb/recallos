"""
/api/network/* — Network policy and activity log endpoints.

Exposes the sovereignty guardrails to the frontend:
  GET  /api/network/policy  — current policy state
  PUT  /api/network/policy  — update policy (global switch + per-feature)
  GET  /api/network/log     — recent network activity log
"""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from desktop.services.network_policy import NetworkPolicy

router = APIRouter(prefix="/network", tags=["network"])


class PolicyUpdate(BaseModel):
    enabled: bool | None = None
    features: dict[str, bool] | None = None


@router.get("/policy")
def get_policy():
    """Return the current network policy state."""
    policy = NetworkPolicy()
    return policy.get_policy()


@router.put("/policy")
def update_policy(body: PolicyUpdate):
    """Update the network policy.  Returns the new state."""
    policy = NetworkPolicy()
    return policy.set_policy(enabled=body.enabled, features=body.features)


@router.get("/log")
def get_log(limit: int = Query(default=100, ge=1, le=1000)):
    """Return recent network activity log entries (newest first)."""
    policy = NetworkPolicy()
    return {"entries": policy.get_log(limit=limit)}
