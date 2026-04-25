"""LINE AI Chatbot - powered by Claude API."""
import os, json, requests, hashlib, hmac, base64
from flask import Flask, request, abort

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

SYSTEM_PROMPT = """你是一個專業但親切的信用卡顧問，專門服務持有以下信用卡的用戶：
1. Chase Sapphire Preferred（年費 $95）
2. Bank of America Atmos Rewards（前身是 Alaska Airlines Visa）

規則：
- 全部用繁體中文回答
- 語氣像朋友在聊天，不要太正式
- 回答要具體實用，不要空泛
- 如果用戶問的問題跟信用卡無關，你也可以回答，但你的專長是信用卡
- 回答控制在 LINE 好閱讀的長度（不超過 800 字）
- 如果不確定的資訊，要誠實說你不確定，建議用戶去官網確認"""


def verify_signature(body, signature):
    hash_value = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).digest()
    return hmac.compare_digest(
        base64.b64encode(hash_value).decode("utf-8"),
        signature
    
