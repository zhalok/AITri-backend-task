from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Identity, Index, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditEvent(Base):
    """One change to a scores/issues/todos/meetings row. Written by a database trigger, never by the app.

    There are no foreign keys on purpose: an audit row must outlive the row it describes. The table is
    append-only; the database refuses updates, deletes and truncates (see migration f6c2d8e41a37).
    """

    __tablename__ = "audit_events"
    __table_args__ = (
        CheckConstraint("op in ('INSERT','UPDATE','DELETE')", name="ck_audit_op"),
        Index("ix_audit_events_team_id_id", "team_id", "id"),
        Index("ix_audit_events_row", "table_name", "row_key", "id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)  # the order things happened in
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("clock_timestamp()"))
    txid: Mapped[int] = mapped_column(BigInteger, server_default=text("txid_current()"))  # same txid = same transaction
    table_name: Mapped[str] = mapped_column(String(32))
    op: Mapped[str] = mapped_column(String(8))
    team_id: Mapped[str | None] = mapped_column(String(64))
    row_key: Mapped[str] = mapped_column(String(200))  # the row's id; scores: "<measurable_id>|<week_start>"
    actor_id: Mapped[str | None] = mapped_column(String(64))  # who, as tagged by the API; None for untagged writes
    old_row: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    new_row: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
