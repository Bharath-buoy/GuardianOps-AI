"""
MongoDB Atlas connection manager using Motor (async driver).

GuardianOps AI is designed to run in two modes:
  1. CONNECTED  - a real MONGODB_URI is reachable -> data persists in Atlas.
  2. STANDALONE - Mongo is unreachable / not configured -> the in-memory
                  mock data service transparently takes over so the app
                  (and `npm run dev` / `uvicorn --reload` demo flow)
                  never fails to boot just because a DB isn't provisioned yet.

This mirrors how real observability platforms degrade gracefully when a
storage backend is briefly unavailable.
"""
import logging

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import settings

logger = logging.getLogger("guardianops.database")


class Database:
    client: AsyncIOMotorClient | None = None
    db = None
    connected: bool = False


database = Database()


async def connect_to_mongo() -> None:
    """Attempt to connect to MongoDB Atlas. Never raises - falls back to mock mode."""
    try:
        database.client = AsyncIOMotorClient(
            settings.MONGODB_URI, serverSelectionTimeoutMS=3000
        )
        await database.client.admin.command("ping")
        database.db = database.client[settings.MONGODB_DB_NAME]
        database.connected = True
        logger.info("✅ Connected to MongoDB Atlas: %s", settings.MONGODB_DB_NAME)
        await ensure_indexes()
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as exc:  # noqa: BLE001
        database.connected = False
        logger.warning(
            "⚠️  MongoDB unavailable (%s). Falling back to in-memory mock data mode. "
            "Set MONGODB_URI in .env to enable persistence.",
            str(exc)[:200],
        )


async def close_mongo_connection() -> None:
    if database.client:
        database.client.close()
        logger.info("MongoDB connection closed")


async def ensure_indexes() -> None:
    """Create indexes used by the application's query patterns."""
    if not database.connected:
        return
    try:
        await database.db.services.create_index("service_id", unique=True)
        await database.db.incidents.create_index("incident_id", unique=True)
        await database.db.incidents.create_index("created_at")
        await database.db.metrics.create_index([("service_id", 1), ("timestamp", -1)])
        await database.db.logs.create_index([("service_id", 1), ("timestamp", -1)])
        await database.db.workflow_runs.create_index("run_id", unique=True)
        await database.db.workflow_runs.create_index("started_at")
        await database.db.recommendations.create_index("incident_id")
        await database.db.agents.create_index("agent_id", unique=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Index creation skipped: %s", exc)


def get_collection(name: str):
    """Return a Mongo collection handle, or None if running in mock-only mode."""
    if database.connected and database.db is not None:
        return database.db[name]
    return None
