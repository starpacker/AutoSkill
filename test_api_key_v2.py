#!/usr/bin/env python3
"""Test gpugeek API key with various methods."""
import requests
import json

API_KEY = "gpugeek_sk_mDx3cn5MCqDo3DIqJXqPyQ"
BASE_URL = "https://api.gpugeek.com"

# Test 1: Standard OpenAI-compatible chat completion
print("=" * 60)
print("Test 1: OpenAI-compatible chat completion")
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

# Test 2: OpenAI-compatible models list
print("\n" + "=" * 60)
print("Test 2: OpenAI-compatible models list")
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

# Test 3: Try with different auth header format
print("\n" + "=" * 60)
print("Test 3: Try different auth header")
print("=" * 60)
alt_headers = {
    "api-key": API_KEY,
    "Content-Type": "application/json"
}
try:
    resp = requests.post(url, headers=alt_headers, json=payload, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Body: {json.dumps(resp.json(), indent=2)[:300]}")
except Exception as e:
    print(f"Error: {e}")

# Test 4: Try with x-api-key header
print("\n" + "=" * 60)
print("Test 4: x-api-key header")
print("=" * 60)
alt_headers2 = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}
try:
    resp = requests.post(url, headers=alt_headers2, json=payload, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Body: json.dumps(resp.json(), indent=2)[:300]")
except Exception as e:
    print(f"Error: {e}")

# Test 5: Try with OPENAI_API_KEY format (no Bearer, just key in auth)
print("\n" + "=" * 60)
print("Test 5: No Bearer prefix")
print("=" * 60)
alt_headers3 = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}
try:
    resp = requests.post(url, headers=alt_headers3, json=payload, timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"Body: {json.dumps(resp.json(), indent=2)[:300]}")
except Exception as e:
    print(f"Error: {e}")

# Test 6: curl-like test
print("\n" + "=" * 60)
print("Test 6: Also test with gpugeek main domain")
print("=" * 60)
try:
    resp = requests.get("https://www.gpugeek.com", timeout=15)
    print(f"Status: {resp.status_code}")
    print(f"First 200 chars: {resp.text[:200]}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("API Key (first 20):", API_KEY[:20] + "...")
print("Base URL:", BASE_URL)