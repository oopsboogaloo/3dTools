"""Helpers for loading and patching ComfyUI API-format workflow JSON."""
from __future__ import annotations

import json
import random
import re
import unicodedata
from pathlib import Path
from typing import Any

Workflow = dict[str, Any]


def load_workflow(path: Path) -> Workflow:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_node_by_title(workflow: Workflow, title: str) -> str:
    """Find a node id by its `_meta.title` (the name set via ComfyUI's node title
    field). Raises with a helpful message if it's missing or duplicated, since a
    stale/hand-edited workflow export is the most likely cause of a silent bug.
    """
    matches = [
        node_id
        for node_id, node in workflow.items()
        if node.get("_meta", {}).get("title") == title
    ]
    if not matches:
        raise KeyError(
            f"No node titled {title!r} in this workflow. Open it in ComfyUI, "
            f"double-click the node's title bar to rename it, then re-export "
            f"(Save (API Format))."
        )
    if len(matches) > 1:
        raise KeyError(f"Multiple nodes titled {title!r}: {matches}. Titles must be unique.")
    return matches[0]


def find_nodes_by_class(workflow: Workflow, class_type: str) -> list[str]:
    return [node_id for node_id, node in workflow.items() if node.get("class_type") == class_type]


def set_text(workflow: Workflow, title: str, text: str) -> None:
    node_id = find_node_by_title(workflow, title)
    workflow[node_id]["inputs"]["text"] = text


def random_seed() -> int:
    return random.randint(0, 2**32 - 1)


def slugify(text: str, max_len: int = 60) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return text[:max_len] or "prompt"
