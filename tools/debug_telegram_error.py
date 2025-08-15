#!/usr/bin/env python3
import os, json, redis, requests

TG_TOKEN = "8103700393:AAEK3RjTGHHYyy_X1Uc9FUuUoRcLuzYZe4k"
CHAT_ID = "-1002581996861"

# Try simple message without button
url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
simple_msg = {
    "chat_id": CHAT_ID,
    "text": "Test message - debugging stuck alerts",
    "disable_web_page_preview": True
}

print("Sending simple message...")
r = requests.post(url, json=simple_msg)
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")

if r.status_code == 200:
    print("\nNow trying with button...")
    # Try with inline keyboard
    button_msg = {
        "chat_id": CHAT_ID,
        "text": "Test with button",
        "disable_web_page_preview": True,
        "reply_markup": json.dumps({
            "inline_keyboard": [[{
                "text": "Test Button",
                "login_url": {
                    "url": "https://joinbitten.com/tg_login?state=%7B%22sid%22%3A%22test%22%7D",
                    "request_write_access": True,
                    "forward_text": "Authorize to view mission"
                }
            }]]
        })
    }
    
    r2 = requests.post(url, data=button_msg)
    print(f"Button Status: {r2.status_code}")
    print(f"Button Response: {r2.text}")