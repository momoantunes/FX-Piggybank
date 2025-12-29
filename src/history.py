import json
from pathlib import Path
from typing import Optional


def load_history(path: Path) -> list:
    if not path.exists():
        return []
    try:
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            return []
        return json.loads(content)
    except Exception:
        return []


def save_history(path: Path, items: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def last_bid(history: list) -> Optional[float]:
    if not history:
        return None
    last = history[-1]
    return float(last.get("bid")) if last.get("bid") is not None else None


def append_entry(history: list, entry: dict, max_items: int = 365 * 2) -> list:
    history.append(entry)
    if len(history) > max_items:
        history = history[-max_items:]
    return history
