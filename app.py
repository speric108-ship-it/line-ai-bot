import os
import json
import requests
import hashlib
import hmac
import base64
from flask import Flask, request, abort

app = Flask(__name__)

SECRET = os.environ["LINE_CHANNEL_SECRET"]
TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
API_KEY = os.environ["ANTHROPIC_API_KEY"]

SYS = "你是專業但親切的信用卡顧問，熟悉美國所有主要銀行的信用卡（Chase、Amex、Citi、Capital One、Bank of America、Discover 等）。不管用戶問哪張卡，你都能回答。全部用繁體中文回答，語氣像朋友聊天，回答具體實用，不超過800字。不確定的資訊要誠實說，建議去官網確認。"


def check_sig(body, sig):
    h = hmac.new(SECRET.encode(), body.encode(), hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(h).decode(), sig)


def ask_claude(msg):
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-sonnet-4-6",
            "max_tokens": 1000,
            "system": SYS,
            "messages": [{"role": "user", "content": msg}],
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["content"][0]["text"]


def reply(token, text):
    requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={
            "Authorization": "Bearer " + TOKEN,
            "Content-Type": "application/json",
        },
        json={
            "replyToken": token,
            "messages": [{"type": "text", "text": text[:4900]}],
        },
        timeout=15,
    )


@app.route("/callback", methods=["POST"])
def callback():
    sig = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    if not check_sig(body, sig):
        abort(403)
    data = json.loads(body)
    for ev in data.get("events", []):
        if ev["type"] == "message" and ev["message"]["type"] == "text":
            try:
                ans = ask_claude(ev["message"]["text"])
            except Exception as e:
                ans = "抱歉暫時無法回答：" + str(e)[:100]
            reply(ev["replyToken"], ans)
    return "OK", 200


@app.route("/", methods=["GET"])
def health():
    return "Bot is running!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
