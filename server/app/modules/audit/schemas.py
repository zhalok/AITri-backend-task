from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    occurred_at: datetime
    txid: int
    table: str = Field(validation_alias="table_name")
    op: str
    team_id: str | None
    row_key: str
    actor_id: str | None
    old: dict[str, Any] | None = Field(validation_alias="old_row")
    new: dict[str, Any] | None = Field(validation_alias="new_row")
