#!/usr/bin/env python3
"""Test gpugeek API key with ANTHROPIC env var credentials."""
import requests
import json

API_KEY = "00gcclg9l39y9p01000dhjzolag1q2hk00901kh1"
BASE_URL = "https://api.gpugeek.com"

# Test 1: OpenAI-compatible chat completion (standard Bearer auth)
print("=" * 60)
print("Test 1: OpenAI-compatible chat (Bearer auth)")
print("=" * 60)
url = f"{BASE_URL}/v1/chat/completions"
payload = {
    "model": "Vendor3/DeepSeek-V4-Flash",
    "messages": [{"role": "user", "content": "Say hello in one word"}],
    "max_tokens": 10
}
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
try:
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"Status: {resp.status_code}")
    print(f"Body: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: Try with x-api-key header
print("\n" + "=" * 60)
print("Test 2: x-api-key header")
print("=" * 60)
headers2 = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}
try:
    resp = requests.post(url, headers=headers2, json=payload, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Body: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 3: Models list
print("\n" + "=" * 60)
print("Test 3: Models list (Bearer)")
print("=" * 60)
try:
    resp = requests.get(f"{BASE_URL}/v1/models", headers=headers, timeout=15)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        models = resp.json()
        print(f"Models count: {len(models.get('data', []))}")
        for m in models.get('data', [])[:10]:
            print(f"  - {m.get('id')}")
    else:
        print(f"Body: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Try with api-key header
print("\n" + "=" * 60)
print("Test 4: api-key header")
print("=" * 60)
headers3 = {
    "api-key": API_KEY,
    "Content-Type": "application/json"
}
try:
    resp = requests.post(url, headers=headers3, json=payload, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Body: {json.dumps(resp.json(), indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")

# Test 5: Test with old key side by side
print("\n" + "=" * 60)
print("Test 5: Old key (for comparison)")
print("=" * 60)
old_key = "gpugeek_sk_mDx3cn5MCqDo3DIqJXqPyQ"
headers_old = {
    "Authorization": f"Bearer {old_key}",
    "Content-Type": "application/json"
}
try:
    resp = requests.post(url, headers=headers_old, json=payload, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Body: {json.dumps(resp.json(), indent=2)[:200]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"New key (first 20): {API_KEY[:20]}...")
print(f"Old key (first 20): {old_key[:20]}...")