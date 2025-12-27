import json
from pathlib import Path
from typing import Optional


DATA_PATH = Path("data/usdbrl.json")


def load_history() -> list:
    if not DATA_PATH.exists():
        return []

    try:
        content = DATA_PATH.read_text(encoding="utf-8").strip()
        if not content:
            return []
        return json.loads(content)
    except Exception:
        # Se o arquivo ficar corrompido por algum motivo, melhor não quebrar tudo.
        return []


def save_history(items: list) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def last_bid(history: list) -> Optional[float]:
    if not history:
        return None
    last = history[-1]
    return float(last.get("bid")) if last.get("bid") is not None else None


def append_entry(history: list, entry: dict, max_items: int = 365 * 2) -> list:
    """
    Mantém histórico limitado (padrão: ~2 anos se rodar 1x/dia; aqui roda 2x/dia,
    então na prática dá uns ~1 ano. Ajusta se quiser.)
    """
    history.append(entry)
    if len(history) > max_items:
        history = history[-max_items:]
    return history
