#!/usr/bin/env python3
"""
Anthropic Messages API → OpenAI Chat Completions API proxy.

Translates requests from Anthropic format (used by the evaluation framework)
to OpenAI format (supported by gpugeek.com), and translates responses back.

Usage:
    python proxy_anthropic_to_openai.py --port 8444 --target-url https://api.gpugeek.com
    export ANTHROPIC_BASE_URL=http://localhost:8444
    export ANTHROPIC_API_KEY=<any-dummy-value>  # proxy will use the real key below
"""

import argparse
import http.server
import json
import logging
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
import ssl
from typing import Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("anthropic-proxy")

# Target API key - will be set from command line
TARGET_API_KEY: str = ""
TARGET_BASE_URL: str = ""
TARGET_MODEL: str = ""
TARGET_CHAT_PATH: str = "/v1/chat/completions"


def anthropic_to_openai(anthropic_body: dict) -> dict:
    """Convert Anthropic Messages API request to OpenAI Chat Completions format."""
    messages: list[dict] = []
    system_prompt = anthropic_body.get("system", "")

    # Track tool call IDs for tool_result messages
    tool_call_ids = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    for msg in anthropic_body.get("messages", []):
        role = msg["role"]
        content = msg.get("content", "")

        # Handle content blocks format (Anthropic)
        if isinstance(content, list):
            tool_calls_for_msg = []
            text_parts = []
            for block in content:
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    tool_calls_for_msg.append({
                        "id": block.get("id", f"toolu_{id(block)}"),
                        "type": "function",
                        "function": {
                            "name": block.get("name", ""),
                            "arguments": json.dumps(block.get("input", {})),
                        },
                    })
                elif block.get("type") == "tool_result":
                    tool_result_content = block.get("content", "")
                    if isinstance(tool_result_content, list):
                        texts = [b.get("text", "") for b in tool_result_content if isinstance(b, dict) and b.get("type") == "text"]
                        tool_result_content = "\n".join(texts)
                    tool_call_id = block.get("tool_use_id", "")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": str(tool_result_content),
                    })
                else:
                    text_parts.append(str(block))

            content = "\n".join(text_parts) if text_parts else ""

            if tool_calls_for_msg:
                mapped_role = role if role in ("user", "assistant", "system") else "user"
                msg_entry = {"role": mapped_role}
                if content:
                    msg_entry["content"] = content
                else:
                    msg_entry["content"] = None
                msg_entry["tool_calls"] = tool_calls_for_msg
                messages.append(msg_entry)
                continue

        mapped_role = role if role in ("user", "assistant", "system", "tool") else "user"
        messages.append({"role": mapped_role, "content": content})

    openai_body: dict[str, Any] = {
        "model": anthropic_body.get("model", TARGET_MODEL),
        "messages": messages,
        "max_tokens": anthropic_body.get("max_tokens", 4096),
        "temperature": anthropic_body.get("temperature", 1.0),
        "stream": anthropic_body.get("stream", False),
    }

    # Convert tools (Anthropic → OpenAI, same JSON Schema format)
    if "tools" in anthropic_body:
        openai_tools = []
        for tool in anthropic_body["tools"]:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {}),
                },
            })
        openai_body["tools"] = openai_tools

    # tool_choice
    if "tool_choice" in anthropic_body:
        tc = anthropic_body["tool_choice"]
        if tc.get("type") == "auto":
            openai_body["tool_choice"] = "auto"
        elif tc.get("type") == "any":
            openai_body["tool_choice"] = "required"
        elif tc.get("type") == "tool":
            openai_body["tool_choice"] = {"type": "function", "function": {"name": tc.get("name", "")}}
        else:
            openai_body["tool_choice"] = "auto"

    # Copy optional parameters
    for key in ("top_p", "stop", "presence_penalty", "frequency_penalty"):
        if key in anthropic_body:
            openai_body[key] = anthropic_body[key]

    log.info(
        "Converted request: model=%s messages=%d max_tokens=%s system=%s tools=%s",
        openai_body["model"], len(messages), openai_body["max_tokens"], bool(system_prompt),
        len(openai_body.get("tools", [])),
    )
    return openai_body


def openai_to_anthropic(openai_response: dict, openai_request: dict) -> dict:
    """Convert OpenAI Chat Completions response to Anthropic Messages API format."""
    choice = openai_response.get("choices", [{}])[0]
    message = choice.get("message", {})
    content_text = message.get("content", "")

    # Build content blocks
    content_blocks = []

    # Handle tool calls
    tool_calls = message.get("tool_calls", [])
    if tool_calls:
        if content_text:
            content_blocks.append({"type": "text", "text": content_text})
        for tc in tool_calls:
            try:
                args = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                args = {}
            content_blocks.append({
                "type": "tool_use",
                "id": tc.get("id", f"toolu_{id(tc)}"),
                "name": tc["function"]["name"],
                "input": args,
            })
    elif content_text:
        content_blocks.append({"type": "text", "text": content_text})

    # Map finish reason
    finish_reason = choice.get("finish_reason", "stop")
    stop_reason_map = {
        "stop": "end_turn",
        "length": "max_tokens",
        "tool_calls": "tool_use",
        "content_filter": "end_turn",
    }
    stop_reason = stop_reason_map.get(finish_reason, "end_turn")

    usage = openai_response.get("usage", {})
    anthropic_response: dict[str, Any] = {
        "id": openai_response.get("id", f"msg_proxy_{id(openai_response)}"),
        "type": "message",
        "role": "assistant",
        "content": content_blocks,
        "model": openai_response.get("model", TARGET_MODEL),
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": usage.get("prompt_tokens", 0) if usage else 0,
            "output_tokens": usage.get("completion_tokens", 0) if usage else 0,
        },
    }
    return anthropic_response


def anthropic_error_to_openai_format(status_code: int, error_body: dict) -> dict:
    """Convert an OpenAI error to Anthropic error format."""
    error_msg = error_body.get("error", {}).get("message", str(error_body))
    return {
        "type": "error",
        "error": {
            "type": {
                400: "invalid_request_error",
                401: "authentication_error",
                403: "permission_error",
                404: "not_found_error",
                429: "rate_limit_error",
                500: "api_error",
                502: "api_error",
                503: "overloaded_error",
            }.get(status_code, "api_error"),
            "message": error_msg,
        },
    }


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler that proxies Anthropic → OpenAI."""

    def _clean_path(self) -> str:
        """Extract URL path without query parameters."""
        return urllib.parse.urlparse(self.path).path

    def do_GET(self):
        path = self._clean_path()
        if path in ("/health", "/v1/health"):
            self._send_json(200, {"status": "ok", "proxy": "anthropic-to-openai"})
        elif path == "/v1/models":
            self._handle_models()
        else:
            self._send_json(404, {"error": "not_found"})

    def _handle_models(self):
        """Handle GET /v1/models - return available models list."""
        # Return a model list that includes our target model
        models = [
            {
                "id": TARGET_MODEL,
                "object": "model",
                "created": 1700000000,
                "owned_by": "proxy",
            },
            {
                "id": "claude-sonnet-4-20250514",
                "object": "model",
                "created": 1700000001,
                "owned_by": "proxy",
            },
            {
                "id": "claude-3-5-sonnet-20241022",
                "object": "model",
                "created": 1700000002,
                "owned_by": "proxy",
            },
        ]
        self._send_json(200, {"data": models, "object": "list"})

    def do_POST(self):
        path = self._clean_path()
        if path == "/v1/messages":
            self._handle_messages()
        else:
            self._send_json(404, {"error": "not_found"})

    def _handle_messages(self):
        """Handle POST /v1/messages - the Anthropic Messages API endpoint."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            anthropic_request = json.loads(body)
        except json.JSONDecodeError as e:
            self._send_json(400, anthropic_error_to_openai_format(400, {"error": {"message": f"Invalid JSON: {e}"}}))
            return

        # Convert to OpenAI format
        try:
            openai_request = anthropic_to_openai(anthropic_request)
        except Exception as e:
            log.error("Conversion error: %s", e)
            self._send_json(400, anthropic_error_to_openai_format(400, {"error": {"message": str(e)}}))
            return

        is_stream = openai_request.get("stream", False)
        target_url = f"{TARGET_BASE_URL.rstrip('/')}{TARGET_CHAT_PATH}"

        # Forward to OpenAI-compatible API
        req_data = json.dumps(openai_request).encode("utf-8")
        req = urllib.request.Request(
            target_url,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TARGET_API_KEY}",
            },
            method="POST",
        )

        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = True
            ctx.verify_mode = ssl.CERT_REQUIRED

            if is_stream:
                self._handle_streaming(req, ctx, openai_request)
            else:
                self._handle_non_streaming(req, ctx, openai_request)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="replace")
            try:
                error_json = json.loads(error_body)
            except json.JSONDecodeError:
                error_json = {"error": {"message": error_body}}
            log.error("Upstream HTTP %d: %s", e.code, error_body[:200])
            self._send_json(e.code, anthropic_error_to_openai_format(e.code, error_json))
        except urllib.error.URLError as e:
            log.error("Upstream connection error: %s", e.reason)
            self._send_json(502, anthropic_error_to_openai_format(502, {"error": {"message": str(e.reason)}}))

    def _handle_non_streaming(self, req: urllib.request.Request, ctx: ssl.SSLContext, openai_request: dict):
        """Handle non-streaming response."""
        with urllib.request.urlopen(req, context=ctx, timeout=300) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            openai_response = json.loads(raw)

        anthropic_response = openai_to_anthropic(openai_response, openai_request)
        log.info(
            "Response: %s %s (in=%d out=%d)",
            anthropic_response.get("stop_reason", "?"),
            anthropic_response.get("model", "?"),
            anthropic_response.get("usage", {}).get("input_tokens", 0),
            anthropic_response.get("usage", {}).get("output_tokens", 0),
        )
        self._send_json(200, anthropic_response)

    def _handle_streaming(self, req: urllib.request.Request, ctx: ssl.SSLContext, openai_request: dict):
        """Handle streaming (SSE) response - translate on-the-fly."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        with urllib.request.urlopen(req, context=ctx, timeout=300) as upstream:
            buffer = ""
            while True:
                chunk = upstream.read(4096)
                if not chunk:
                    break
                text = chunk.decode("utf-8", errors="replace")
                buffer += text
                # Process complete SSE lines
                lines = buffer.split("\n")
                buffer = lines.pop() if not text.endswith("\n") else ""
                for line in lines:
                    translated = self._translate_sse_line(line.strip(), openai_request)
                    if translated is not None:
                        try:
                            self.wfile.write(f"data: {json.dumps(translated)}\n\n".encode("utf-8"))
                            self.wfile.flush()
                        except BrokenPipeError:
                            return

        # Send done event
        try:
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except BrokenPipeError:
            pass

    _sse_buffer: dict = {}

    def _translate_sse_line(self, line: str, openai_request: dict) -> Optional[dict]:
        """Translate one SSE data line from OpenAI format to Anthropic format."""
        if not line.startswith("data: "):
            return None
        data_str = line[6:]
        if data_str == "[DONE]":
            return None

        try:
            openai_chunk = json.loads(data_str)
        except json.JSONDecodeError:
            return None

        choices = openai_chunk.get("choices", [])
        if not choices:
            return None

        delta = choices[0].get("delta", {})
        finish_reason = choices[0].get("finish_reason")
        index = choices[0].get("index", 0)

        # Handle tool_calls in delta
        tool_calls = delta.get("tool_calls", [])
        if tool_calls:
            for tc in tool_calls:
                func = tc.get("function", {})
                idx = tc.get("index", 0)
                if func.get("name"):
                    # Start of tool call
                    self._sse_buffer[f"tool_{idx}"] = tc.get("id", "")
                    return {
                        "type": "content_block_start",
                        "index": 1000 + idx,
                        "content_block": {
                            "type": "tool_use",
                            "id": tc.get("id", f"toolu_{idx}"),
                            "name": func.get("name", ""),
                            "input": {},
                        },
                    }
                elif func.get("arguments"):
                    # Input delta
                    return {
                        "type": "content_block_delta",
                        "index": 1000 + idx,
                        "delta": {
                            "type": "input_json_delta",
                            "partial_json": func.get("arguments", ""),
                        },
                    }
            return None

        # Build Anthropic streaming event
        if finish_reason is not None:
            stop_reason_map = {
                "stop": "end_turn",
                "length": "max_tokens",
                "tool_calls": "tool_use",
            }
            usage = openai_chunk.get("usage", {})
            return {
                "type": "message_delta",
                "delta": {
                    "stop_reason": stop_reason_map.get(finish_reason, "end_turn"),
                    "stop_sequence": None,
                },
                "usage": {
                    "input_tokens": usage.get("prompt_tokens", 0) if usage else 0,
                    "output_tokens": usage.get("completion_tokens", 0) if usage else 0,
                },
            }

        content_delta = delta.get("content", "")
        if content_delta:
            return {
                "type": "content_block_delta",
                "index": index,
                "delta": {
                    "type": "text_delta",
                    "text": content_delta,
                },
            }

        # First chunk with role
        if delta.get("role"):
            return {
                "type": "content_block_start",
                "index": index,
                "content_block": {"type": "text", "text": ""},
            }

        return None

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        log.info("Request: %s", format % args)


def main():
    parser = argparse.ArgumentParser(description="Anthropic → OpenAI API proxy")
    parser.add_argument("--port", type=int, default=8444, help="Port to listen on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--target-url", default="https://api.gpugeek.com", help="Target OpenAI-compatible API base URL")
    parser.add_argument(
        "--target-api-key",
        default=os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"),
        help="API key (prefer OPENAI_API_KEY/ANTHROPIC_API_KEY environment variables)",
    )
    parser.add_argument("--target-model", default="Vendor3/DeepSeek-V4-Flash", help="Default model name")
    parser.add_argument("--target-chat-path", default="/v1/chat/completions", help="Target chat completions path")
    args = parser.parse_args()
    if not args.target_api_key:
        parser.error("Set OPENAI_API_KEY or ANTHROPIC_API_KEY, or pass --target-api-key")

    global TARGET_API_KEY, TARGET_BASE_URL, TARGET_MODEL, TARGET_CHAT_PATH
    TARGET_API_KEY = args.target_api_key
    TARGET_BASE_URL = args.target_url.rstrip("/")
    TARGET_MODEL = args.target_model
    TARGET_CHAT_PATH = "/" + args.target_chat_path.lstrip("/")

    server = http.server.HTTPServer((args.host, args.port), ProxyHandler)
    log.info(
        "Proxy listening on http://%s:%d → %s%s",
        args.host, args.port, TARGET_BASE_URL, TARGET_CHAT_PATH,
    )
    log.info("Default model: %s", TARGET_MODEL)
    log.info('Configure your framework with: ANTHROPIC_BASE_URL="http://%s:%d"', args.host, args.port)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()