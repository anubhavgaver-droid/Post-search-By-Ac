from pyrogram import Client, filters
from pyrogram.types import Message, LinkPreviewOptions
from pyrogram.enums import MessageEntityType
from database import save_post, get_connected_channel
from plugins.start import to_small_caps

def extract_only_bold_title(message: Message) -> str:
    """Strictly extracts ONLY text that is formatted as BOLD in the message."""
    text = message.text or message.caption
    entities = message.entities or message.caption_entities
    
    if not text or not entities:
        return None

    bold_parts = []
    for entity in entities:
        if entity.type == MessageEntityType.BOLD:
            bold_text = text[entity.offset : entity.offset + entity.length].strip()
            if bold_text:
                bold_parts.append(bold_text)

    if bold_parts:
        return " ".join(bold_parts)
    
    return None

# Automatic Live Indexer from Channels
@Client.on_message(filters.channel & (filters.text | filters.caption))
async def auto_channel_indexer(client: Client, message: Message):
    title = extract_only_bold_title(message)
    if not title:
        return

    post_link = message.link
    if post_link:
        await save_post(message.chat.id, message.id, title, post_link)

# Manual Batch Indexer (Admins Only)
@Client.on_message(filters.group & filters.command("index"))
async def batch_index_handler(client: Client, message: Message):
    member = await message.chat.get_member(message.from_user.id)
    if member.status.value not in ["administrator", "owner"]:
        return await message.reply_text(
            to_small_caps("only group admins can use this command."),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    conn = await get_connected_channel(message.chat.id)
    if not conn:
        return await message.reply_text(
            to_small_caps("please connect a channel first using /connect."),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    status = await message.reply_text(
        to_small_caps("indexing channel posts... please wait."),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
    count = 0

    async for msg in client.get_chat_history(conn["channel_id"], limit=500):
        if (msg.text or msg.caption) and msg.link:
            title = extract_only_bold_title(msg)
            if title:
                await save_post(conn["channel_id"], msg.id, title, msg.link)
                count += 1

    await status.edit_text(
        f"✅ **{to_small_caps('indexing completed!')}**\n\n{to_small_caps('bold posts indexed:')} `{count}`",
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
