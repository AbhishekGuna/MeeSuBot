"""
DB operations for meeting summaries.

Functions
---------
save_summary        — persist one summary row linked to guild + channel
get_guild_summaries — fetch recent summaries for a guild (optional channel filter)
get_guild_stats     — aggregate stats (total meetings, total audio hours) for a guild
init_db             — create tables if they don't exist yet
"""

import json
from typing import Any

from db.connection import execute_query, pool
from models.summary import CREATE_SUMMARIES_TABLE_SQL, SummaryRecord


# --------------------------------------------------------------------- #
# Schema initialisation (call once on bot startup)                      #
# --------------------------------------------------------------------- #

async def init_db() -> None:
    """
    Idempotent schema migration.
    - Creates the summaries table if it doesn't exist.
    - Adds any missing columns to a pre-existing table.
    """
    from db.connection import pool as _pool
    if _pool is None:
        raise RuntimeError("DB pool not initialised — call connect_db() first.")

    # Language-level migrations so ADD COLUMN IF NOT EXISTS handles old tables
    MIGRATIONS = [
        # Step 1: ensure base table exists
        CREATE_SUMMARIES_TABLE_SQL,

        # Step 2: add any columns that may be missing on a pre-existing table
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS guild_id      BIGINT      NOT NULL DEFAULT 0;",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS channel_id    BIGINT      NOT NULL DEFAULT 0;",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS user_id       BIGINT      NOT NULL DEFAULT 0;",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS filename      TEXT        NOT NULL DEFAULT '';",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS tldr          TEXT        NOT NULL DEFAULT '';",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS key_decisions JSONB       NOT NULL DEFAULT '[]';",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS action_items  JSONB       NOT NULL DEFAULT '[]';",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS open_questions JSONB      NOT NULL DEFAULT '[]';",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS sentiment     TEXT        NOT NULL DEFAULT 'neutral';",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS topics        JSONB       NOT NULL DEFAULT '[]';",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW();",
        "ALTER TABLE summaries ADD COLUMN IF NOT EXISTS duration_seconds REAL;",

        # Step 3: indexes (IF NOT EXISTS is safe to re-run)
        "CREATE INDEX IF NOT EXISTS idx_summaries_guild_id   ON summaries (guild_id,   created_at DESC);",
        "CREATE INDEX IF NOT EXISTS idx_summaries_channel_id ON summaries (channel_id, created_at DESC);",
    ]

    async with _pool.acquire() as conn:
        for statement in MIGRATIONS:
            await conn.execute(statement)
    print("DB schema initialised / migrated.")


# --------------------------------------------------------------------- #
# Write                                                                  #
# --------------------------------------------------------------------- #

async def save_summary(
    *,
    guild_id: int,
    channel_id: int,
    user_id: int,
    filename: str,
    result: dict[str, Any],
    duration_seconds: float | None = None,
) -> int:
    """
    Persist a summary result dict (as returned by the AI) to the DB.

    Parameters
    ----------
    duration_seconds:
        Approximate audio/video length in seconds, if known. Pass ``None``
        for text transcripts or when the duration cannot be determined.

    Returns the new row id.
    """
    query = """
        INSERT INTO summaries
            (guild_id, channel_id, user_id, filename,
             tldr, key_decisions, action_items, open_questions,
             sentiment, topics, duration_seconds)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id
    """
    rows = await execute_query(
        query,
        guild_id,
        channel_id,
        user_id,
        filename,
        result["tldr"],
        json.dumps(result.get("key_decisions", [])),
        json.dumps(result.get("action_items", [])),
        json.dumps(result.get("open_questions", [])),
        result.get("meeting_sentiment", "neutral"),
        json.dumps(result.get("topics_discussed", [])),
        duration_seconds,
    )
    return rows[0]["id"]


# --------------------------------------------------------------------- #
# Read                                                                   #
# --------------------------------------------------------------------- #

async def get_guild_summaries(
    guild_id: int,
    *,
    channel_id: int | None = None,
    limit: int = 10,
) -> list[SummaryRecord]:
    """
    Return the most recent `limit` summaries for a guild.
    Optionally filter to a specific channel.
    """
    if channel_id is not None:
        query = """
            SELECT * FROM summaries
            WHERE guild_id = $1 AND channel_id = $2
            ORDER BY created_at DESC
            LIMIT $3
        """
        rows = await execute_query(query, guild_id, channel_id, limit)
    else:
        query = """
            SELECT * FROM summaries
            WHERE guild_id = $1
            ORDER BY created_at DESC
            LIMIT $2
        """
        rows = await execute_query(query, guild_id, limit)

    return [SummaryRecord.from_row(r) for r in rows]


# --------------------------------------------------------------------- #
# Aggregate stats                                                        #
# --------------------------------------------------------------------- #

async def get_guild_stats(guild_id: int) -> dict:
    """
    Return aggregate statistics for a guild.

    Keys returned
    -------------
    total_meetings   : int   — total rows in the summaries table for this guild
    total_seconds    : float — sum of duration_seconds (None rows counted as 0)
    timed_meetings   : int   — meetings where duration_seconds is not NULL
    """
    query = """
        SELECT
            COUNT(*)                               AS total_meetings,
            COALESCE(SUM(duration_seconds), 0)     AS total_seconds,
            COUNT(duration_seconds)                AS timed_meetings
        FROM summaries
        WHERE guild_id = $1
    """
    rows = await execute_query(query, guild_id)
    row = rows[0]
    return {
        "total_meetings": int(row["total_meetings"]),
        "total_seconds": float(row["total_seconds"]),
        "timed_meetings": int(row["timed_meetings"]),
    }
