from motor.motor_asyncio import AsyncIOMotorClient
import re
import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client[config.DATABASE_NAME]

channels_col = db["connected_channels"]
posts_col = db["indexed_posts"]

# --- CHANNEL MANAGEMENT ---
async def connect_channel(chat_id: int, channel_id: int, channel_title: str):
    await channels_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"channel_id": channel_id, "channel_title": channel_title}},
        upsert=True
    )

async def disconnect_channel(chat_id: int):
    await channels_col.delete_one({"chat_id": chat_id})

async def get_connected_channel(chat_id: int):
    return await channels_col.find_one({"chat_id": chat_id})

# --- POST INDEXING & SEARCH ---
async def save_post(channel_id: int, message_id: int, title: str, post_link: str):
    await posts_col.update_one(
        {"channel_id": channel_id, "message_id": message_id},
        {"$set": {"title": title, "link": post_link}},
        upsert=True
    )

async def search_posts_fuzzy(channel_id: int, query: str, limit: int = 5):
    """
    Executes regex-based rapid partial/fuzzy matching inside the bound channel.
    """
    words = query.strip().split()
    regex_pattern = ".*".join([re.escape(w) for w in words])
    pattern = re.compile(regex_pattern, re.IGNORECASE)
    
    cursor = posts_col.find({
        "channel_id": channel_id,
        "title": {"$regex": pattern}
    }).limit(limit)
    
    return await cursor.to_list(length=limit)
