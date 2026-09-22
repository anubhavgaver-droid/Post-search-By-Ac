from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, LinkPreviewOptions
from database import search_posts_fuzzy, get_connected_channel
from plugins.start import to_small_caps

@Client.on_message(filters.group & filters.text & ~filters.command(["start", "help", "connect", "disconnect", "connection", "index"]))
async def inline_search_engine(client: Client, message: Message):
    conn = await get_connected_channel(message.chat.id)
    if not conn:
        return

    query = message.text.strip()
    if len(query) < 2:
        return

    results = await search_posts_fuzzy(conn["channel_id"], query, limit=5)

    # SILENT FALLBACK: Stay quiet if search query yields no match in DB
    if not results:
        return

    buttons = []
    for post in results:
        btn_title = f"📌 {post['title'][:35]}"
        buttons.append([InlineKeyboardButton(text=btn_title, url=post["link"])])

    # Append Close button
    buttons.append([InlineKeyboardButton(to_small_caps("close ❌"), callback_data="close_message")])

    reply_markup = InlineKeyboardMarkup(buttons)
    header_text = f"🔍 **{to_small_caps('search results for:')}** `{query}`"

    await message.reply_text(
        text=header_text,
        reply_markup=reply_markup,
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
