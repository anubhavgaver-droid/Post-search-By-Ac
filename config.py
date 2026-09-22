import os

API_ID = int(os.environ.get("API_ID", "123456"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")

MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://...")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "PRO_SEARCH_BOT")

OWNER_ID = int(os.environ.get("OWNER_ID", "123456789"))

# Render FQDN Domain Variable (Render provides this automatically)
URL = os.environ.get("RENDER_EXTERNAL_URL", "http://0.0.0.0:8080")
