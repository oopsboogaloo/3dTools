"""Minimal ComfyUI HTTP + websocket client.

Talks directly to a running ComfyUI server (/prompt, /history, /view, /upload/image,
/ws) rather than depending on a third-party wrapper library, so behaviour is fully
visible and easy to debug.

The important bit the build spec calls out: ComfyUI reports OOM and other node
failures as an `execution_error` message on the websocket, not as an HTTP error.
A script that only checks the HTTP response to /prompt will queue the job
successfully and then hang forever waiting for outputs that never arrive.
`ComfyClient.run()` listens on the websocket for exactly this and raises
`ComfyExecutionError` as soon as it sees one, instead of hanging.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import websocket  # from websocket-client


class ComfyClientError(RuntimeError):
    """Base class for errors talking to ComfyUI."""


class ComfyExecutionError(ComfyClientError):
    """Raised when ComfyUI reports an execution_error over the websocket.

    This is how OOMs and other node-level failures surface -- there is no HTTP
    error, the job just fails mid-graph. `node_type` / `exception_message` are
    pulled straight out of the websocket payload when available.
    """

    def __init__(self, message: str, payload: dict[str, Any] | None = None):
        super().__init__(message)
        self.payload = payload or {}


@dataclass
class ComfyClient:
    host: str = "127.0.0.1"
    port: int = 8188
    client_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def ws_url(self) -> str:
        return f"ws://{self.host}:{self.port}/ws?clientId={self.client_id}"

    # -- basic HTTP helpers --------------------------------------------------

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read())

    def _post(self, path: str, payload: dict[str, Any]) -> Any:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}", data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise ComfyClientError(f"POST {path} failed ({e.code}): {body}") from e

    def system_stats(self) -> dict[str, Any]:
        return self._get("/system_stats")

    # -- queueing / running ---------------------------------------------------

    def queue_prompt(self, workflow: dict[str, Any]) -> str:
        """Submit a workflow (API-format node graph). Returns the prompt_id."""
        result = self._post("/prompt", {"prompt": workflow, "client_id": self.client_id})
        if "error" in result:
            raise ComfyClientError(f"ComfyUI rejected the workflow: {result['error']}")
        return result["prompt_id"]

    def run(self, workflow: dict[str, Any], on_progress=None) -> dict[str, Any]:
        """Queue a workflow and block until it finishes (success or error).

        Returns the /history entry for the prompt on success. Raises
        ComfyExecutionError on failure -- including OOM, which ComfyUI only
        reports via the websocket.
        """
        prompt_id = self.queue_prompt(workflow)

        ws = websocket.WebSocket()
        ws.connect(self.ws_url)
        try:
            while True:
                raw = ws.recv()
                if isinstance(raw, bytes):
                    # binary frames are preview JPEGs, not relevant here
                    continue
                msg = json.loads(raw)
                msg_type = msg.get("type")
                data = msg.get("data", {})

                if data.get("prompt_id") not in (None, prompt_id):
                    continue

                if msg_type == "execution_error":
                    raise ComfyExecutionError(
                        f"ComfyUI execution_error in node "
                        f"{data.get('node_type', '?')} (id {data.get('node_id', '?')}): "
                        f"{data.get('exception_message', 'no message')}",
                        payload=data,
                    )

                if msg_type == "progress" and on_progress:
                    on_progress(data)

                if msg_type == "executing" and data.get("node") is None and data.get("prompt_id") == prompt_id:
                    # node == None signals this prompt_id is fully done
                    break
        finally:
            ws.close()

        history = self._get(f"/history/{prompt_id}")
        entry = history.get(prompt_id)
        if entry is None:
            raise ComfyClientError(f"No history entry for prompt_id {prompt_id} after completion")

        status = entry.get("status", {})
        if status.get("status_str") == "error":
            raise ComfyExecutionError(f"Prompt {prompt_id} finished with error status: {status}", payload=status)

        return entry

    # -- images -----------------------------------------------------------

    def get_image(self, filename: str, subfolder: str, folder_type: str) -> bytes:
        url = (
            f"{self.base_url}/view?"
            + urllib.parse.urlencode({"filename": filename, "subfolder": subfolder, "type": folder_type})
        )
        with urllib.request.urlopen(url) as resp:
            return resp.read()

    def download_outputs(self, history_entry: dict[str, Any], dest_dir: Path, prefix: str) -> list[Path]:
        """Save every SaveImage output in a history entry to dest_dir.

        Files are named `{prefix}_{index}.png`; callers should already have
        baked prompt text + timestamp into `prefix`.
        """
        dest_dir.mkdir(parents=True, exist_ok=True)
        saved: list[Path] = []
        outputs = history_entry.get("outputs", {})
        index = 0
        for node_output in outputs.values():
            for image in node_output.get("images", []):
                data = self.get_image(image["filename"], image.get("subfolder", ""), image.get("type", "output"))
                suffix = Path(image["filename"]).suffix or ".png"
                out_path = dest_dir / f"{prefix}_{index}{suffix}"
                out_path.write_bytes(data)
                saved.append(out_path)
                index += 1
        return saved

    def upload_image(self, path: Path, subfolder: str = "", overwrite: bool = True) -> str:
        """Upload a local image into ComfyUI's input/ dir. Returns the filename to
        reference from a LoadImage node's `image` input."""
        boundary = uuid.uuid4().hex
        fields = {
            "type": "input",
            "subfolder": subfolder,
            "overwrite": "true" if overwrite else "false",
        }
        body = bytearray()
        for key, value in fields.items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n".encode()
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{path.name}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n"
        ).encode()
        body += path.read_bytes()
        body += f"\r\n--{boundary}--\r\n".encode()

        req = urllib.request.Request(
            f"{self.base_url}/upload/image",
            data=bytes(body),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            raise ComfyClientError(f"Image upload failed ({e.code}): {body_text}") from e
        return result["name"]
