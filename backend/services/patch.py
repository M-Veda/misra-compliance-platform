"""
patch.py  —  Thin adapter shim over the new offset-based patch engine.

All real logic lives in backend.services.patch_engine.
This module exists only to preserve the PatchService interface expected by
backend/api/main.py's /api/preview-patch endpoint.
"""

from typing import Optional
from backend.models.violation import RuleViolation
from backend.services import patch_engine


class PatchService:
    @staticmethod
    def generate_preview(
        source_code: str,
        violation: RuleViolation,
        decision: str,
        manual_code: Optional[str] = None,
    ) -> str:
        """
        Returns the modified source after applying the given decision.

        - 'Accept'  : apply the rule-specific auto-patch via patch_engine.
        - 'Reject'  : return source unchanged.
        - 'Skip'    : return source unchanged.
        - 'Manual'  : return manual_code if provided, else source unchanged.
        """
        if decision in ("Reject", "Skip"):
            return source_code

        if decision == "Manual":
            return manual_code if manual_code is not None else source_code

        # decision == 'Accept' — delegate to engine
        result = patch_engine.apply_single(source_code, violation)
        # apply_single always returns the original source on failure so
        # callers receive a usable result in every case.
        return result.patched_source
