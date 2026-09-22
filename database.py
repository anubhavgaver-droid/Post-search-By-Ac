from motor.motor_asyncio import AsyncIOMotorClient
import re
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
    RapidFuzz based ultra-fast partial and fuzzy search for connected channels.
    """
    # 1. चैनल की सभी इंडेक्स पोस्ट्स डेटाबेस से लाएँ
    all_posts = await posts_col.find({"channel_id": channel_id}).to_list(length=None)
    if not all_posts:
        return []

    # 2. सभी पोस्ट्स के टाइटल्स की लिस्ट बनाएँ
    titles_map = {post["title"]: post for post in all_posts if "title" in post}
    titles_list = list(titles_map.keys())

    if not titles_list:
        return []

    # 3. RapidFuzz से बेस्ट 5 मैचेस निकालें (Spelling mistakes टॉलरेंस के साथ)
    matches = process.extract(
        query,
        titles_list,
        scorer=fuzz.WRatio,
        limit=limit,
        score_cutoff=40  # 40% से अधिक मैच होने पर रिज़ल्ट दिखाएगा
    )

    # 4. मैच हुए टाइटल्स से ओरिजिनल पोस्ट ऑब्जेक्ट निकालें
    results = [titles_map[match[0]] for match in matches if match[0] in titles_map]
    
    return results
