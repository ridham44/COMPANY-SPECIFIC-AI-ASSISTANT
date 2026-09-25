from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import Settings
from app.models.conversation import Conversation, Message
from app.models.document import KnowledgeDocument


async def init_db(settings: Settings) -> AsyncIOMotorClient:
    client = AsyncIOMotorClient(settings.mongo_uri)
    await init_beanie(
        database=client[settings.mongo_db_name],
        document_models=[KnowledgeDocument, Conversation, Message],
    )
    return client
