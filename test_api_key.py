#!/usr/bin/env python3
"""Test gpugeek API key validity."""
import requests
import json

url = "https://api.gpugeek.com/v1/models"
headers = {"Authorization": "Bearer gpugeek_sk_mDx3cn5MCqDo3DIqJXqPyQ"}

print(f"Testing: GET {url}")
try:
    resp = requests.get(url, headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    body = resp.json()
    print(f"Body: {json.dumps(body, indent=2)[:1000]}")
except Exception as e:
    print(f"Error: {e}")

# Also test the chat endpoint
print("\n--- Testing chat endpoint ---")
chat_url = "https://api.gpugeek.com/v1/chat/completions"
payload = {
    "model": "Vendor3/DeepSeek-V4-Flash",
    "messages": [{"role": "user", "content": "Say hello"}],
    "max_tokens": 10
}
try:
    resp = requests.post(chat_url, headers=headers, json=payload, timeout=30)
    print(f"Status: {resp.status_code}")
    body = resp.json()
    print(f"Body: {json.dumps(body, indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")