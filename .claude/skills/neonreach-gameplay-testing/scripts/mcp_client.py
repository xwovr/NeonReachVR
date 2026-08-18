#!/usr/bin/env python3
"""
Minimal MCP clients for the two servers this project uses, so a plain Python
process can drive the game without going through an agent turn.

Measured round-trip latency:
    operator (stdio)        1-3 ms
    unity bridge (http)     ~10 ms
versus ~10-15 s for one agent turn. That 1000x gap is what makes a real-time
observe -> decide -> throw loop possible at all.
"""

import json
import subprocess
import urllib.request

OPERATOR_BIN = "/Users/xw0/meta-xr-operator/meta-xr-operator-mcp-proxy"
BRIDGE_URL = "http://127.0.0.1:48736/mcpbridge/"
BRIDGE_TOKEN = "ea9c1d7a29cc4642b81c0052f3d64ca3"


class McpError(RuntimeError):
    pass


def _unwrap(result):
    """MCP tool results arrive as a content list; pull out the text payload."""
    if result is None:
        return None
    if isinstance(result, dict) and "content" in result:
        parts = [c.get("text", "") for c in result["content"] if c.get("type") == "text"]
        text = "\n".join(parts)
        try:
            return json.loads(text)
        except (ValueError, TypeError):
            return text
    return result


class OperatorClient:
    """Meta XR Operator over stdio.

    Auto-reconnects. A long run with several concurrent proxy processes will
    occasionally lose one - a 260 s session died at 114 s with the pipe closed -
    and dropping the whole test because one connection blinked is not
    acceptable, so `call` transparently respawns and retries once.
    """

    def __init__(self, binary=OPERATOR_BIN):
        self.binary = binary
        self._connect()

    def _connect(self):
        self.proc = subprocess.Popen(
            [self.binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self._id = 0
        self._rpc("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "neonreach-player", "version": "1"}})
        self._notify("notifications/initialized", {})
        self.reconnects = getattr(self, "reconnects", -1) + 1

    def _next_id(self):
        self._id += 1
        return self._id

    def _notify(self, method, params):
        self.proc.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
        self.proc.stdin.flush()

    def _rpc(self, method, params):
        rid = self._next_id()
        self.proc.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "id": rid, "method": method, "params": params}) + "\n")
        self.proc.stdin.flush()
        for line in self.proc.stdout:
            line = line.strip()
            if not line.startswith("{"):
                continue                      # proxy prints banner lines on stdout
            msg = json.loads(line)
            if msg.get("id") == rid:
                if "error" in msg:
                    raise McpError(msg["error"])
                return msg.get("result")
        raise McpError("operator closed the pipe")

    def call(self, tool, **args):
        try:
            return _unwrap(self._rpc("tools/call",
                                     {"name": tool, "arguments": args}))
        except (McpError, BrokenPipeError, OSError, ValueError):
            try:
                self.proc.kill()
            except Exception:
                pass
            self._connect()
            return _unwrap(self._rpc("tools/call",
                                     {"name": tool, "arguments": args}))

    def close(self):
        try:
            self.proc.terminate()
        except Exception:
            pass


class BridgeClient:
    """Meta Unity MCP Extensions over streamable HTTP."""

    def __init__(self, url=BRIDGE_URL, token=BRIDGE_TOKEN):
        self.url, self.token, self._id = url, token, 0
        self._rpc("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "neonreach-player", "version": "1"}})

    def _rpc(self, method, params):
        self._id += 1
        body = json.dumps({"jsonrpc": "2.0", "id": self._id,
                           "method": method, "params": params}).encode()
        req = urllib.request.Request(self.url, data=body, method="POST", headers={
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode()
        for chunk in raw.strip().split("\n"):
            chunk = chunk.strip()
            if chunk.startswith("data:"):
                chunk = chunk[5:].strip()
            if not chunk.startswith("{"):
                continue
            msg = json.loads(chunk)
            if "error" in msg:
                raise McpError(msg["error"])
            if "result" in msg:
                return msg["result"]
        raise McpError(f"no result in bridge response: {raw[:200]}")

    def call(self, tool, **args):
        return _unwrap(self._rpc("tools/call", {"name": tool, "arguments": args}))

    def scene(self, method, **args):
        return self.call("SceneObjectsTools", method=method, **args)

    def set_time_scale(self, value):
        return self.call("IReflectionService", method="InvokeStaticMethodFromJson",
                         typeName="UnityEngine.Time", methodName="set_timeScale",
                         arguments=json.dumps({"value": value}))

    def close(self):
        pass
