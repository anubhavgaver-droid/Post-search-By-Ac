import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions, CallbackQuery
from database import search_posts_fuzzy, get_connected_channel
from plugins.start import to_small_caps

async def auto_delete_message(msg: Message, delay: int = 600):
    """10 मिनट (600 सेकंड) बाद मैसेज को अपने आप डिलीट करने वाला फ़ंक्शन"""
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

    # RapidFuzz से टॉप 5 मैचेस निकालें
    results = await search_posts_fuzzy(conn["channel_id"], query, limit=5)

    if not results:
        return

    # पहला और सबसे बेस्ट मैच
    best_match = results[0]

    # सुंदर टेक्स्ट फ़ॉर्मेट में मैसेज + डायरेक्ट लिंक
    text_response = (
        f"🎬 **{to_small_caps('here is your requested post!')}**\n\n"
        f"📌 **{to_small_caps('title:')}** `{best_match['title']}`\n"
        f"🔗 **{to_small_caps('link:')}** {best_match['link']}\n\n"
        f"👤 {to_small_caps('requested by:')} {message.from_user.mention}\n"
        f"⏳ _{to_small_caps('this message will auto-delete in 10 minutes.')}_"
    )

    buttons = []

    # अगर RapidFuzz को और भी मैच (Suggestions) मिले हैं, तो उनके बटन जोड़ें
    if len(results) > 1:
        for post in results[1:]:
            btn_title = f"📌 {post['title'][:35]}"
            buttons.append([InlineKeyboardButton(text=btn_title, url=post["link"])])

    # क्लोज़ (Manual Delete) बटन
    buttons.append([InlineKeyboardButton(to_small_caps("close ❌"), callback_data="close_search_msg")])

    reply_markup = InlineKeyboardMarkup(buttons)

    sent_msg = await message.reply_text(
        text=text_response,
        reply_markup=reply_markup,
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

    # 10 मिनट (600 सेकंड) बाद इस मैसेज को ऑटो-डिलीट करने के लिए बैकग्राउंड टास्क शुरू करें
    asyncio.create_task(auto_delete_message(sent_msg, 600))


# Close बटन दबाने पर मैसेज तुरंत मैनुअली डिलीट हो जाएगा
@Client.on_callback_query(filters.regex("^close_search_msg$"))
async def close_search_callback(client: Client, callback_query: CallbackQuery):
    try:
        await callback_query.message.delete()
    except Exception:
        pass
