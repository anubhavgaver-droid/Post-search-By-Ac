import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions, CallbackQuery
from database import search_posts_fuzzy, get_connected_channel
from plugins.start import to_small_caps

async def auto_delete_message(msg: Message, delay: int = 600):
    """10 मिनट बाद ऑटो डिलीट करने वाला फ़ंक्शन"""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

@Client.on_message(filters.group & filters.text & ~filters.command(["start", "help", "connect", "disconnect", "connection", "index"]))
async def inline_search_engine(client: Client, message: Message):
    conn = await get_connected_channel(message.chat.id)
    if not conn:
        return

    query = message.text.strip()
    if len(query) < 2:
        return

    results = await search_posts_fuzzy(conn["channel_id"], query, limit=5)

    if not results:
        return

    best_match = results[0]
    top_score = best_match.get("match_score", 0)

    # 1. HIGH CONFIDENCE MATCH (Score >= 75) -> डायरेक्ट लिंक मैसेज में दिखाओ
    if top_score >= 75:
        text_response = (
            f"🎬 **{to_small_caps('here is your requested post!')}**\n\n"
            f"📌 **{to_small_caps('title:')}** `{best_match['title']}`\n"
            f"🔗 **{to_small_caps('link:')}** {best_match['link']}\n\n"
            f"👤 {to_small_caps('requested by:')} {message.from_user.mention}\n"
            f"⏳ _{to_small_caps('this message will auto-delete in 10 minutes.')}_"
        )

        buttons = []
        # केवल उन्हीं पोस्ट्स को सजेस्ट करो जो टॉप स्कोर के काफी करीब हों (ताकि फ़ालतू Kalu ना आए)
        for post in results[1:]:
            if post.get("match_score", 0) >= (top_score - 15):
                btn_title = f"📌 {post['title'][:35]}"
                buttons.append([InlineKeyboardButton(text=btn_title, url=post["link"])])

        buttons.append([InlineKeyboardButton(to_small_caps("close ❌"), callback_data="close_search_msg")])
        reply_markup = InlineKeyboardMarkup(buttons)

    # 2. MEDIUM CONFIDENCE MATCH (Score 55 - 74) -> "Did You Mean?" दिखाओ
    else:
        text_response = (
            f"❓ **{to_small_caps('did you mean one of these?')}**\n"
            f"_{to_small_caps('no exact match found for:')}_ `{query}`\n\n"
            f"👤 {to_small_caps('requested by:')} {message.from_user.mention}\n"
            f"⏳ _{to_small_caps('this message will auto-delete in 10 minutes.')}_"
        )

        buttons = []
        for post in results:
            btn_title = f"📌 {post['title'][:35]}"
            buttons.append([InlineKeyboardButton(text=btn_title, url=post["link"])])

        buttons.append([InlineKeyboardButton(to_small_caps("close ❌"), callback_data="close_search_msg")])
        reply_markup = InlineKeyboardMarkup(buttons)

    sent_msg = await message.reply_text(
        text=text_response,
        reply_markup=reply_markup,
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

    # 10 मिनट में मैसेज ऑटो-डिलीट हो जाएगा
    asyncio.create_task(auto_delete_message(sent_msg, 600))


# Close बटन हैंडलर
@Client.on_callback_query(filters.regex("^close_search_msg$"))
async def close_search_callback(client: Client, callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()
    except Exception:
        pass
