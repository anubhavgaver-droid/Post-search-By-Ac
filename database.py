from motor.motor_asyncio import AsyncIOMotorClient
from rapidfuzz import process, fuzz
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
    RapidFuzz based search with score tracking to avoid unrelated suggestions.
    """
    all_posts = await posts_col.find({"channel_id": channel_id}).to_list(length=None)
    if not all_posts:
        return []

    titles_map = {post["title"]: post for post in all_posts if "title" in post}
    titles_list = list(titles_map.keys())

    if not titles_list:
        return []

    # Score cutoff बढ़कर 55 कर दिया ताकि Kalu जैसी फ़ालतू पोस्ट्स मैच न हों
    matches = process.extract(
        query,
        titles_list,
        scorer=fuzz.WRatio,
        limit=limit,
        score_cutoff=55
    )

    results = []
    for match_title, score, _ in matches:
        if match_title in titles_map:
            post_obj = titles_map[match_title].copy()
            post_obj["match_score"] = score  # Score attach किया ताकि UI निर्णय ले सके
            results.append(post_obj)

    return results
