from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, LinkPreviewOptions

def to_small_caps(text: str) -> str:
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    small =  "ᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇғɢʜɪᴊᴋʟᴍɴᴏᴘǫʀsᴛᴜᴠᴡxʏᴢ"
    trans = str.maketrans(normal, small)
    return text.translate(trans)

# Private /start command
@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    text = (
        f"✨ **{to_small_caps('welcome to post search bot')}** ✨\n\n"
        f"{to_small_caps('i am an advanced channel post indexing system.')}\n\n"
        f"📌 **{to_small_caps('features:')}**\n"
        f"• {to_small_caps('connect channel via')} `/connect`\n"
        f"• {to_small_caps('auto bold post indexing')}\n"
        f"• {to_small_caps('rapid search in group')}\n"
        f"• {to_small_caps('silent fallback when no results found')}"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(to_small_caps("add to group"), url=f"https://t.me/{client.me.username}?startgroup=true")]
    ])
    
    await message.reply_text(
        text,
        reply_markup=keyboard,
        link_preview_options=LinkPreviewOptions(is_disabled=True)
    )

# Group Welcome Message when Bot is Added
@Client.on_message(filters.group & filters.new_chat_members)
async def group_welcome_handler(client: Client, message: Message):
    for member in message.new_chat_members:
        if member.id == client.me.id:
            welcome_text = (
                f"👋 **{to_small_caps('thanks for adding me to')} {message.chat.title}!**\n\n"
                f"📌 **{to_small_caps('how to setup:')}**\n"
                f"1. {to_small_caps('make me admin in your channel')}\n"
                f"2. {to_small_caps('use')} `/connect -100xxxxxxxxxx` {to_small_caps('to bind channel')}\n"
                f"3. {to_small_caps('use')} `/index` {to_small_caps('to index existing bold posts')}\n\n"
                f"⚙️ {to_small_caps('only group admins can configure the bot.')}"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(to_small_caps("close ❌"), callback_data="close_message")]
            ])
            
            await message.reply_text(
                welcome_text,
                reply_markup=keyboard,
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )

# Close Callback Handler
@Client.on_callback_query(filters.regex("^close_message$"))
async def close_callback_handler(client: Client, callback_query: CallbackQuery):
    await callback_query.message.delete()
