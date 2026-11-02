from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class GuardResult:
    action: Literal["ALLOW", "BLOCK", "ESCALATE"]
    reason: str
    reference: str | None = None


class TransferIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    beneficiary_id: str = Field(min_length=1)
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    idempotency_key: str = Field(min_length=8)


SERVER_ACCOUNTS: dict[str, dict[str, set[str]]] = {
    "learner-17": {
        "roles": {"transfers:create"},
        "beneficiaries": {"friend-1"},
    },
    "learner-18": {"roles": set(), "beneficiaries": set()},
}
SIMULATED_LEDGER: dict[str, dict[str, str]] = {}


def authorize_transfer(
    user_id: str,
    request: TransferIntent,
    *,
    approved: bool = False,
) -> GuardResult:
    identity = SERVER_ACCOUNTS.get(user_id)
    if identity is None or "transfers:create" not in identity["roles"]:
        return GuardResult("BLOCK", "Missing server-side transfer permission")
    if request.beneficiary_id not in identity["beneficiaries"]:
        return GuardResult("BLOCK", "Beneficiary is not allowlisted")
    if request.amount > Decimal("1000.00") and not approved:
        return GuardResult("ESCALATE", "Independent approval required")
    return GuardResult("ALLOW", "Authorized by backend")


def execute_simulated_transfer(
    *,
    user_id: str,
    request: TransferIntent,
    approved: bool = False,
) -> GuardResult:
    """Record an in-memory demo transfer after backend policy checks."""
    policy = authorize_transfer(user_id, request, approved=approved)
    if policy.action != "ALLOW":
        return policy

    prior = SIMULATED_LEDGER.get(request.idempotency_key)
    if prior is not None:
        same_request = (
            prior["user"] == user_id
            and prior["beneficiary"] == request.beneficiary_id
            and prior["amount"] == str(request.amount)
        )
        if not same_request:
            return GuardResult("BLOCK", "Idempotency key reused with different arguments")
        return GuardResult("ALLOW", "Existing simulated transaction (no duplicate)", prior["reference"])

    reference = f"sim-{len(SIMULATED_LEDGER) + 1:04d}"
    SIMULATED_LEDGER[request.idempotency_key] = {
        "user": user_id,
        "beneficiary": request.beneficiary_id,
        "amount": str(request.amount),
        "reference": reference,
    }
    return GuardResult("ALLOW", "Simulated transaction recorded", reference)
