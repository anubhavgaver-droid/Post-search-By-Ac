import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, LinkPreviewOptions
from pyrogram.enums import MessageEntityType
from pyrogram.errors import FloodWait, RPCError
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

# Automatic Live Indexer from Channels (Real-Time listener)
@Client.on_message(filters.channel & (filters.text | filters.caption))
async def auto_channel_indexer(client: Client, message: Message):
    title = extract_only_bold_title(message) or (message.text or message.caption or "").split("\n")[0].strip()
    if not title:
        return

    post_link = message.link
    if post_link:
        await save_post(message.chat.id, message.id, title, post_link)

# Manual Batch Indexer using ID Range Fetching (Bot API Compatible)
@Client.on_message(filters.group & filters.command("index"))
async def batch_index_handler(client: Client, message: Message):
    try:
        member = await message.chat.get_member(message.from_user.id)
        if member.status.value not in ["administrator", "owner"]:
            return await message.reply_text(
                to_small_caps("only group admins can use this command."),
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
    except Exception:
        return

    conn = await get_connected_channel(message.chat.id)
    if not conn:
        return await message.reply_text(
            to_small_caps("please connect a channel first using /connect."),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    channel_id = conn["channel_id"]

    status = await message.reply_text(
        to_small_caps("indexing channel posts... please wait."),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

    total_scanned = 0
    saved_count = 0
    skipped_count = 0

    try:
        # 1. लेटेस्ट मैसेज ID प्राप्त करें
        dummy_msg = await client.send_message(channel_id, "🔍 Indexing Sync...")
        latest_id = dummy_msg.id
        await dummy_msg.delete()

        # 2. BOT_METHOD_INVALID से बचने के लिए Message IDs की लिस्ट बनाकर get_messages का उपयोग करें
        chunk_size = 100
        for start_id in range(1, latest_id + 1, chunk_size):
            message_ids = list(range(start_id, min(start_id + chunk_size, latest_id + 1)))
            
            try:
                messages = await client.get_messages(channel_id, message_ids)
            except RPCError:
                continue

            for msg in messages:
                if not msg or msg.empty:
                    continue
                
                total_scanned += 1

                if not (msg.text or msg.caption):
                    skipped_count += 1
                    continue

                # पहले Bold टाइटल चेक करें, न होने पर पहली लाइन लें
                title = extract_only_bold_title(msg) or (msg.text or msg.caption).split("\n")[0].strip()
                
                if title and msg.link:
                    await save_post(channel_id, msg.id, title, msg.link)
                    saved_count += 1
                else:
                    skipped_count += 1

            # लाइव प्रोग्रेस अपडेट (हर 100 मैसेज स्कैन पर)
            try:
                await status.edit_text(
                    f"🔄 **{to_small_caps('indexing in progress...')}**\n\n"
                    f"📊 **{to_small_caps('scanned:')}** `{total_scanned}`\n"
                    f"✅ **{to_small_caps('saved:')}** `{saved_count}`\n"
                    f"⏭️ **{to_small_caps('skipped:')}** `{skipped_count}`",
                    link_preview_options=LinkPreviewOptions(is_disabled=True)
                )
            except Exception:
                pass

            await asyncio.sleep(1) # Rate Limit सेफ्टी डिले

        summary_text = (
            f"📌 **{to_small_caps('indexing completed!')}**\n\n"
            f"📊 **{to_small_caps('total scanned:')}** `{total_scanned}`\n"
            f"✅ **{to_small_caps('posts indexed:')}** `{saved_count}`\n"
            f"⏭️ **{to_small_caps('skipped:')}** `{skipped_count}`"
        )

        final_msg = await status.edit_text(
            summary_text,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

        # Self Auto-Pin Summary Message
        try:
            await client.pin_chat_message(message.chat.id, final_msg.id)
        except Exception:
            pass

    except FloodWait as e:
        await asyncio.sleep(e.value)
        await status.edit_text(
            f"⚠️ Telegram FloodWait: Retrying in {e.value} seconds.",
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
    except Exception as e:
        await status.edit_text(
            f"❌ Unexpected Error: `{str(e)}`",
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
