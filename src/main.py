import os
from pathlib import Path
from datetime import datetime

from quote import fetch_quote
from history import load_history, save_history, append_entry, last_bid
from rules import percent_change, should_notify
from notify import notify_discord


def _get_float_env(name: str) -> float | None:
    v = os.getenv(name, "").strip()
    if not v:
        return None
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return None


def _get_bool_env(name: str, default: bool = False) -> bool:
    v = os.getenv(name, "").strip().lower()
    if not v:
        return default
    return v in ("1", "true", "yes", "y", "on")


def _flag_for(pair: str) -> str:
    if pair.startswith("USD"):
        return "🇺🇸"
    if pair.startswith("EUR"):
        return "🇪🇺"
    return "💱"


def _format_pair_block(entry: dict, prev_bid: float | None, reasons: list[str]) -> str:
    pair = entry["pair"]
    bid = float(entry["bid"])
    ts = entry["timestamp_iso"]
    chg = percent_change(bid, prev_bid)

    chg_txt = "N/A"
    if chg is not None:
        arrow = "⬆️" if chg > 0 else ("⬇️" if chg < 0 else "➡️")
        chg_txt = f"{arrow} {chg:+.2f}%"

    reasons_txt = "\n".join([f"  - {r}" for r in reasons]) if reasons else "  - (always_notify)"

    return (
        f"{_flag_for(pair)} **{pair}**\n"
        f"- bid: **R$ {bid:.4f}**\n"
        f"- vs último: **{chg_txt}**\n"
        f"- UTC: `{ts}`\n"
        f"- fonte: {entry.get('source')}\n"
        f"- motivos:\n{reasons_txt}\n"
    )


def main() -> int:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    # thresholds globais
    alert_drop_pct = _get_float_env("ALERT_DROP_PCT")
    alert_rise_pct = _get_float_env("ALERT_RISE_PCT")
    always_notify = _get_bool_env("ALWAYS_NOTIFY", default=False)

    # thresholds por moeda (opcional)
    buy_below_usd = _get_float_env("BUY_BELOW_USD")
    buy_below_eur = _get_float_env("BUY_BELOW_EUR")

    pairs = [
        ("USD", "BRL", Path("data/usdbrl.json"), buy_below_usd),
        ("EUR", "BRL", Path("data/eurbrl.json"), buy_below_eur),
    ]

    blocks_to_send: list[str] = []
    total_updated: list[str] = []

    for base, quote, path, buy_below in pairs:
        history = load_history(path)
        prev = last_bid(history)

        entry = fetch_quote(base, quote)

        history = append_entry(history, entry)
        save_history(path, history)

        total_updated.append(entry["pair"])

        if webhook_url:
            notify, reasons = should_notify(
                current=float(entry["bid"]),
                previous=prev,
                buy_below=buy_below,
                alert_drop_pct=alert_drop_pct,
                alert_rise_pct=alert_rise_pct,
                always_notify=always_notify,
            )
            if notify:
                blocks_to_send.append(_format_pair_block(entry, prev, reasons))
        else:
            print(f"[{entry['pair']}] DISCORD_WEBHOOK_URL não configurado; histórico atualizado sem notificação.")

    if webhook_url and blocks_to_send:
        header = " **FX Piggybank alert (USD + EUR)**\n"
        footer = " decisão *HUMANA* sempre — o bot só te dá sinal "
        message = header + "\n".join(blocks_to_send) + "\n" + footer
        notify_discord(webhook_url, message)
    else:
        if webhook_url:
            print("Sem gatilho de alerta. Histórico atualizado.")
        # se não tem webhook, já foi logado acima

    print(f"OK - updated: {', '.join(total_updated)} at {datetime.utcnow().isoformat()}Z")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
