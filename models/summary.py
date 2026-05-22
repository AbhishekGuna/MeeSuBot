"""
Model definition for meeting summaries stored in PostgreSQL.

Table: summaries
- id              BIGSERIAL primary key
- guild_id        Discord guild (server) snowflake ID
- channel_id      Discord channel snowflake ID
- user_id         Discord user who invoked the command
- filename        Original uploaded filename
- tldr            Short summary text
- key_decisions   JSON array of decision strings
- action_items    JSON array of {task, owner, deadline} objects
- open_questions  JSON array of question strings
- sentiment       positive | neutral | negative
- topics          JSON array of topic strings
- created_at      Timestamp (UTC)
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

# --------------------------------------------------------------------- #
# DDL — run once via db.init_db() on bot startup                        #
# --------------------------------------------------------------------- #

CREATE_SUMMARIES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS summaries (
    id              BIGSERIAL PRIMARY KEY,
    guild_id        BIGINT        NOT NULL,
    channel_id      BIGINT        NOT NULL,
    user_id         BIGINT        NOT NULL,
    filename        TEXT          NOT NULL,
    tldr            TEXT          NOT NULL,
    key_decisions   JSONB         NOT NULL DEFAULT '[]',
    action_items    JSONB         NOT NULL DEFAULT '[]',
    open_questions  JSONB         NOT NULL DEFAULT '[]',
    sentiment       TEXT          NOT NULL DEFAULT 'neutral',
    topics          JSONB         NOT NULL DEFAULT '[]',
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Index for fast per-guild history queries
CREATE INDEX IF NOT EXISTS idx_summaries_guild_id
    ON summaries (guild_id, created_at DESC);

-- Index for per-channel history queries
CREATE INDEX IF NOT EXISTS idx_summaries_channel_id
    ON summaries (channel_id, created_at DESC);
"""


# --------------------------------------------------------------------- #
# Dataclass — returned by get_guild_summaries / get_channel_summaries   #
# --------------------------------------------------------------------- #

@dataclass
class SummaryRecord:
    id: int
    guild_id: int
    channel_id: int
    user_id: int
    filename: str
    tldr: str
    key_decisions: list[str]
    action_items: list[dict[str, Any]]
    open_questions: list[str]
    sentiment: str
    topics: list[str]
    created_at: datetime

    @classmethod
    def from_row(cls, row) -> "SummaryRecord":
        """Build a SummaryRecord from an asyncpg Record."""
        return cls(
            id=row["id"],
            guild_id=row["guild_id"],
            channel_id=row["channel_id"],
            user_id=row["user_id"],
            filename=row["filename"],
            tldr=row["tldr"],
            key_decisions=row["key_decisions"],
            action_items=row["action_items"],
            open_questions=row["open_questions"],
            sentiment=row["sentiment"],
            topics=row["topics"],
            created_at=row["created_at"],
        )
