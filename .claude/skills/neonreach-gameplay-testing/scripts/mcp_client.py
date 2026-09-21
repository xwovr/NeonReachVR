#!/usr/bin/env python3
"""
Minimal MCP clients for the two servers this project uses, so a plain Python
process can drive the game without going through an agent turn.

Measured round-trip latency:
    operator (stdio)        1-3 ms
    unity bridge (http)     ~10 ms
    unity pipeline (http)   ~30 ms (direct POST to the pipeline server,
                            same channel the `unity` CLI uses, without its
                            ~900 ms process-spawn overhead)
versus ~10-15 s for one agent turn. That 1000x gap is what makes a real-time
observe -> decide -> throw loop possible at all.

Unity side: PipelineClient (Unity Pipeline package, com.unity.pipeline) is the
default - it speaks HTTP to the editor's pipeline server using the token from
Library/Pipeline/.unity-pipeline-port. BridgeClient (Meta Unity MCP Extensions,
port 48736) is the legacy macOS path, kept for backwards compatibility.
"""

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path


def _default_operator_bin():
    """Locate the Meta XR Operator MCP proxy for this platform.

    Override with NEONREACH_OPERATOR_BIN. On Windows the proxy ships via
    `metavr tools install meta-xr-operator` under %APPDATA%; on macOS it is
    the historical standalone path (also overridable).
    """
    override = os.environ.get("NEONREACH_OPERATOR_BIN")
    if override:
        return override
    if os.name == "nt":
        return str(Path(os.environ.get("APPDATA", "")) / "metavr" / "tools"
                   / "meta-xr-operator" / "meta-xr-operator-standalone-public"
                   / "windows" / "meta-xr-operator-mcp-proxy.exe")
    found = shutil.which("meta-xr-operator-mcp-proxy")
    if found:
        return found
    return "/Users/xw0/meta-xr-operator/meta-xr-operator-mcp-proxy"


OPERATOR_BIN = _default_operator_bin()
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
        # Close stdin first so the proxy sees EOF and shuts itself down,
        # then terminate and reap. Without the explicit closes, the pipe
        # wrappers are finalized at GC time and CPython prints "Exception
        # ignored in TextIOWrapper ... OSError: EINVAL" shutdown noise
        # (observed on Windows).
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.terminate()
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
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


def _find_project_root():
    """Locate the Unity project root (parent of Assets/).

    NEONREACH_PROJECT wins; otherwise walk up from this file looking for
    Library/Pipeline/.unity-pipeline-port (these scripts live inside the
    project under .claude/skills/.../scripts/).
    """
    override = os.environ.get("NEONREACH_PROJECT")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        if (parent / "Library" / "Pipeline" / ".unity-pipeline-port").exists():
            return parent
    # Fall back to historical layout: scripts/ -> ... -> project root.
    return here.parents[4]


class PipelineClient:
    """Unity Pipeline package (com.unity.pipeline) over direct HTTP.

    Same channel the `unity` CLI uses - POST /api/exec on the editor's
    pipeline server with the Bearer token from the port descriptor file -
    but without the CLI's ~900 ms process-spawn overhead per call. Measured
    eval latency: ~120 ms cold, ~30 ms warm.

    No MCP involved: this replaces BridgeClient where the Meta Unity MCP
    Extensions bridge is unavailable (Windows).
    """

    def __init__(self, project_path=None, timeout=30):
        self.project = Path(project_path) if project_path else _find_project_root()
        self.descriptor = self.project / "Library" / "Pipeline" / ".unity-pipeline-port"
        self.timeout = timeout
        self._load_descriptor()

    def _load_descriptor(self):
        try:
            desc = json.loads(self.descriptor.read_text())
        except (OSError, ValueError) as exc:
            raise McpError(f"pipeline descriptor unreadable at {self.descriptor} "
                           f"- is the editor running with com.unity.pipeline? {exc}")
        self.port = desc["port"]
        self.token = desc["evalToken"]
        self.url = f"http://127.0.0.1:{self.port}/api/exec"

    def exec(self, command, _retried=False, **params):
        body = json.dumps({"command": command, "parameters": params}).encode()
        req = urllib.request.Request(self.url, data=body, method="POST", headers={
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                msg = json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and not _retried:
                self._load_descriptor()  # token rotated (editor restart)
                return self.exec(command, True, **params)
            raise McpError(f"pipeline {command} HTTP {exc.code}: {exc.read()[:200]}")
        if not msg.get("success", False):
            raise McpError(f"pipeline {command} failed: {str(msg)[:300]}")
        return msg.get("result")

    def eval(self, code):
        """Run C# in the editor; returns the snippet's return value as a string."""
        res = self.exec("eval", code=code)
        if isinstance(res, dict) and res.get("success") is False:
            raise McpError(f"eval diagnostics: {res.get('diagnostics')}")
        return res["result"] if isinstance(res, dict) else res

    def set_time_scale(self, value):
        return self.eval(f"UnityEngine.Time.timeScale = {float(value)}f; "
                        f"return UnityEngine.Time.timeScale.ToString();")

    def game_state(self):
        """(score, missed, is_game_over) in a single round trip."""
        raw = self.eval("return GameManager.Instance.Score + \"/\" "
                        "+ GameManager.Instance.MissedRings + \"/\" "
                        "+ GameManager.Instance.IsGameOver;")
        score, missed, over = str(raw).split("/")
        return int(score), int(missed), over.strip().lower() == "true"

    def restart(self):
        return self.eval("GameManager.Instance.Restart(); return \"restarted\";")

    def close(self):
        pass
