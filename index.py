import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pyrogram import Client

app = FastAPI()

API_ID = int(os.getenv("API_ID") or 0)
API_HASH = os.getenv("API_HASH") or ""
SESSION_STRING = os.getenv("SESSION_STRING") or ""
BOT_TOKEN = os.getenv("BOT_TOKEN") or ""

async def get_userbot():
    if not API_ID or not API_HASH or not SESSION_STRING:
        raise RuntimeError("Telegram credentials missing!")
    
    client = Client(
        "vercel_7anime_bot",
        api_id=API_ID,
        api_hash=API_HASH,
        session_string=SESSION_STRING,
        in_memory=True
    )
    await client.start()
    return client

@app.get("/")
async def root():
    return {"status": "online", "platform": "Vercel 302 Redirect Proxy (Zero Bandwidth)"}

@app.get("/download/{chat_id}/{message_id}")
async def proxy_download(request: Request, chat_id: str, message_id: int):
    client = None
    try:
        # Handle chat ID format
        if chat_id.lstrip("-").isdigit():
            target_chat = int(chat_id)
        else:
            target_chat = chat_id if chat_id.startswith("@") else f"@{chat_id}"

        client = await get_userbot()

        # Fetch message from Telegram
        msg = await client.get_messages(target_chat, message_id)
        if not msg or msg.empty:
            raise HTTPException(status_code=404, detail="Telegram message not found!")

        media = msg.document or msg.video or msg.audio
        if not media:
            raise HTTPException(status_code=404, detail="No media found in this message!")

        # Get file details from Telegram
        file_info = await client.get_file(media.file_id)
        file_path = file_info.file_path

        if not BOT_TOKEN:
            raise HTTPException(status_code=500, detail="BOT_TOKEN environment variable is missing for direct CDN redirect!")

        # Telegram's official high-speed direct CDN link format
        telegram_cdn_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

        if client and client.is_connected:
            await client.stop()

        # 302 Redirect: Vercel se ek bhi byte nahi guzrega, user seedha Telegram se download karega!
        return RedirectResponse(url=telegram_cdn_url, status_code=302)

    except Exception as e:
        if client and client.is_connected:
            await client.stop()
        raise HTTPException(status_code=500, detail=str(e))
        
