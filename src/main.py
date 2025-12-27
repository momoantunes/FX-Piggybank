import os
from datetime import datetime

from quote import fetch_usd_brl
from history import load_history, save_history, append_entry, last_bid
from rules import percent_change, should_notify_always
from notify import notify_discord


def format_message(entry: dict, prev_bid: float | None) -> str:
    bid = entry["bid"]
    ts = entry["timestamp_iso"]
    chg = percent_change(bid, prev_bid)

    chg_txt = "N/A"
    if chg is not None:
        arrow = "⬆️" if chg > 0 else ("⬇️" if chg < 0 else "➡️")
        chg_txt = f"{arrow} {chg:+.2f}%"

    # Mensagem enxuta, mas com cara de produto
    return (
        f"💵 **USD/BRL update**\n"
        f"- Cotação (bid): **R$ {bid:.4f}**\n"
        f"- Variação vs última: **{chg_txt}**\n"
        f"- Timestamp (UTC): `{ts}`\n"
        f"- Fonte: {entry.get('source')}\n"
        f"\n"
        f"🧠 Cofrinho: disciplina > timing perfeito 😌"
    )


def main() -> int:
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    history = load_history()
    prev = last_bid(history)

    entry = fetch_usd_brl()
    history = append_entry(history, entry)
    save_history(history)

    # Notificação
    if webhook_url and should_notify_always():
        msg = format_message(entry, prev)
        notify_discord(webhook_url, msg)
    else:
        # Sem webhook configurado, só loga
        print("DISCORD_WEBHOOK_URL não configurado; histórico atualizado sem notificação.")

    print(f"OK - saved quote: {entry['bid']} at {datetime.utcnow().isoformat()}Z")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
