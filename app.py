import os, json, requests, hashlib, hmac, base64
from flask import Flask, request, abort

app = Flask(__name__)

SECRET = os.environ["LINE_CHANNEL_SECRET"]
TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
API_KEY = os.environ["ANTHROPIC_API_KEY"]

SYS = ("你是專業但親切的信用卡顧問。用戶持有 Chase Sapphire Preferred 和 "
       "Bank of America Atmos Rewards。全部用繁體中文回答，語氣像朋友聊天，"
       "回答具體實用，不超過800字。不確定的資訊要誠實說。")

def check_sig(body, sig):
    h = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(h).decode(), sig)

def ask_claude(msg):
    r = requests.post("https://api.anthropic.com/v1/messages", headers={
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }, json={
        "model": "claude-sonnet-4-6",
        "max_tokens": 1000,
        "system": SYS,
        "messages": [{"role": "user", "content": msg}]
    }, timeout=30)
    r.raise_for_status()
    return r.json()["content"][0]["text"]

def reply(token, text):
    requests.post("https://api.line.me/v2/bot/message/reply", headers={
        "Authorization": "Bearer " + TOKEN,
        "Content-Type": "application/json"
    }, json={
        "replyToken": token,
        "messages": [{"type": "text", "text": text[:4900]}]
    }, timeout=15)

@app.route("/callback", m
