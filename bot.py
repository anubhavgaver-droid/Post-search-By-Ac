import os
import asyncio
import aiohttp
from aiohttp import web
from pyrogram import Client
import config

# --- AIOHTTP WEB SERVER FOR RENDER PORT BINDING ---
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response({"status": "running", "bot": "post_search_bot"})

async def web_server():
    web_app = web.Application()
    web_app.add_routes(routes)
    return web_app

# --- ADVANCED DEDICATED 5-MINUTE FQDN SELF-PING SYSTEM ---
async def self_ping_loop():
    """
    Executes an automated self-ping every 5 minutes (300 seconds) 
    using Render's FQDN to completely eliminate sleep-mode inactivity.
    """
    await asyncio.sleep(10)  # Wait for server initialization
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                url = config.URL
                if not url.endswith("/"):
                    url += "/"
                
                async with session.get(url) as response:
                    print(f"🔄 [SELF-PING SUCCESS] Target: {url} | Status Code: {response.status}")
            except Exception as e:
                print(f"⚠️ [SELF-PING FAILED] Error: {e}")
            
            # Ping every 5 minutes (300 seconds)
            await asyncio.sleep(300)

# --- MAIN APPLICATION LAUNCHER ---
app = Client(
    "post_search_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="plugins")
)

async def main():
    # 1. Start Pyrogram Client
    await app.start()
    print("🤖 Enterprise Post Search Engine Online...")

    # 2. Start Web Server on Render PORT
    port = int(os.environ.get("PORT", 8080))
    server = web.AppRunner(await web_server())
    await server.setup()
    site = web.TCPSite(server, "0.0.0.0", port)
    await site.start()
    print(f"🌐 Web Server Active & Listening on Port {port}")

    # 3. Launch 5-Min Self-Ping Task
    asyncio.create_task(self_ping_loop())

    # 4. Keep Process Alive
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
