from pyrogram import Client, filters
from pyrogram.types import Message, LinkPreviewOptions
from database import connect_channel, disconnect_channel, get_connected_channel
from plugins.start import to_small_caps

@Client.on_message(filters.group & filters.command("connect"))
async def connect_handler(client: Client, message: Message):
    member = await message.chat.get_member(message.from_user.id)
    if member.status.value not in ["administrator", "owner"]:
        return await message.reply_text(
            to_small_caps("only group admins can use this command."),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    if len(message.command) < 2:
        return await message.reply_text(
            f"❌ **{to_small_caps('usage:')}** `/connect -100xxxxxxxxxx`\n\n"
            f"{to_small_caps('provide the target channel id to connect.')}",
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    try:
        channel_id = int(message.command[1])
        chat = await client.get_chat(channel_id)
        
        await connect_channel(message.chat.id, chat.id, chat.title)
        
        await message.reply_text(
            f"✅ **{to_small_caps('successfully connected!')}**\n\n"
            f"📌 **{to_small_caps('channel:')}** {chat.title}\n"
            f"🆔 **{to_small_caps('channel id:')}** `{chat.id}`",
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
    except Exception as e:
        await message.reply_text(
            f"❌ **{to_small_caps('error:')}** {str(e)}\n{to_small_caps('ensure bot is admin in the channel.')}",
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

@Client.on_message(filters.group & filters.command("disconnect"))
async def disconnect_handler(client: Client, message: Message):
    member = await message.chat.get_member(message.from_user.id)
    if member.status.value not in ["administrator", "owner"]:
        return await message.reply_text(
            to_small_caps("only group admins can use this command."),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )

    await disconnect_channel(message.chat.id)
    await message.reply_text(
        to_small_caps("channel disconnected successfully."),
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

@Client.on_message(filters.group & filters.command("connection"))
async def connection_info_handler(client: Client, message: Message):
    member = await message.chat.get_member(message.from_user.id)
    if member.status.value not in ["administrator", "owner"]:
        return

    data = await get_connected_channel(message.chat.id)
    if not data:
        return await message.reply_text(
            to_small_caps("no channel connected to this group."),
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
    
    await message.reply_text(
        f"🔗 **{to_small_caps('active connection:')}**\n\n"
        f"📌 **{to_small_caps('title:')}** {data['channel_title']}\n"
        f"🆔 **{to_small_caps('id:')}** `{data['channel_id']}`",
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )
