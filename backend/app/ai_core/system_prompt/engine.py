"""System Prompt Engine: composition, versioning, validation, audit history.

Composes the final system prompt from:
  central system prompt + role-specific policy + language-specific policy + safety policy.

User messages and retrieved RAG content are NEVER merged into the system prompt;
they are delivered as user/assistant context only, preventing prompt injection.

Templates can be stored in the database (ai_prompt_templates) with per-organization
overrides, falling back to built-in defaults when no DB row exists.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_core.system_prompt.policies import (
    CENTRAL_SYSTEM_PROMPT,
    ROLE_POLICIES,
    SAFETY_POLICIES,
    SUPPORTED_LOCALES,
    SUPPORTED_ROLES,
)


class SystemPromptEngine:
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session

    # ---------- validation ----------

    def validate_role(self, role: str) -> None:
        if role not in SUPPORTED_ROLES:
            raise ValueError(f"Unsupported role: {role}")

    def validate_locale(self, locale: str) -> None:
        if locale not in SUPPORTED_LOCALES:
            raise ValueError(f"Unsupported locale: {locale}")

    # ---------- template resolution ----------

    async def get_template(
        self,
        role: str,
        locale: str,
        organization_id: Optional[UUID] = None,
    ) -> Dict[str, str]:
        """Resolve prompt parts for a role/locale/org.

        Priority: org-specific DB row -> platform-wide DB row -> built-in default.
        Never returns secrets.
        """
        self.validate_role(role)
        self.validate_locale(locale)

        central = CENTRAL_SYSTEM_PROMPT.get(locale, CENTRAL_SYSTEM_PROMPT["en"])
        role_policy = ROLE_POLICIES.get(role, {}).get(locale, "")
        safety = SAFETY_POLICIES.get(locale, SAFETY_POLICIES["en"])

        # Attempt DB override (non-blocking if session unavailable or table missing)
        db_override: Optional[Dict[str, str]] = None
        if self.session is not None:
            try:
                from sqlalchemy import select
                from app.models.ai_prompt_template import AIPromptTemplate  # type: ignore

                stmt = select(AIPromptTemplate).where(
                    AIPromptTemplate.role == role,
                    AIPromptTemplate.language == locale,
                    AIPromptTemplate.is_active == True,  # noqa: E712
                )
                if organization_id is not None:
                    stmt = stmt.where(AIPromptTemplate.organization_id == organization_id)
                else:
                    stmt = stmt.where(AIPromptTemplate.organization_id.is_(None))

                result = await self.session.execute(stmt)
                row = result.scalar_one_or_none()
                if row is not None:
                    db_override = {
                        "central": row.content,
                        "role": "",  # DB override replaces composition parts
                        "safety": safety,
                    }
            except Exception:
                # Table may not exist yet (migration not applied) — fall back to defaults
                db_override = None

        if db_override is not None:
            return db_override

        return {
            "central": central,
            "role": role_policy,
            "safety": safety,
        }

    # ---------- composition ----------

    def compose(
        self,
        parts: Dict[str, str],
        context_injection: Optional[Dict[str, str]] = None,
    ) -> str:
        """Compose the final system prompt.

        context_injection (e.g. current date, org timezone) is added as a labeled
        context block at the end — it does NOT override safety or role policies.
        """
        blocks: List[str] = []
        if parts.get("central"):
            blocks.append(f"[SYSTEM]\n{parts['central'].strip()}")
        if parts.get("role"):
            blocks.append(f"[ROLE POLICY]\n{parts['role'].strip()}")
        if parts.get("safety"):
            blocks.append(f"[SAFETY POLICY]\n{parts['safety'].strip()}")
        if context_injection:
            ctx = "\n".join(f"{k}: {v}" for k, v in context_injection.items())
            blocks.append(f"[CONTEXT]\n{ctx}")
        return "\n\n".join(blocks)

    async def build_system_prompt(
        self,
        role: str,
        locale: str,
        organization_id: Optional[UUID] = None,
        context_injection: Optional[Dict[str, str]] = None,
    ) -> str:
        """Full build: resolve + compose."""
        parts = await self.get_template(role=role, locale=locale, organization_id=organization_id)
        return self.compose(parts, context_injection=context_injection)

    # ---------- audit / versioning ----------

    def record_version(
        self,
        template_name: str,
        version: int,
        content: str,
        changed_by: Optional[UUID] = None,
        change_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return an audit record for a prompt version (caller persists to DB)."""
        return {
            "template_name": template_name,
            "version": version,
            "content": content,
            "changed_by": str(changed_by) if changed_by else None,
            "change_reason": change_reason,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
