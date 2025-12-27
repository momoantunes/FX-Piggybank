import requests
from datetime import datetime, timezone


def fetch_usd_brl() -> dict:
    """
    Busca USD/BRL usando AwesomeAPI:
    https://economia.awesomeapi.com.br/json/last/USD-BRL

    Retorna um dicionário padronizado com:
    - pair
    - bid (float)
    - ask (float | None)
    - timestamp_iso (UTC)
    - source
    """
    url = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()

    data = resp.json()
    usdbrl = data.get("USDBRL")
    if not usdbrl:
        raise RuntimeError("Resposta inesperada da API (campo USDBRL não encontrado).")

    bid = float(usdbrl["bid"])
    ask = float(usdbrl["ask"]) if "ask" in usdbrl and usdbrl["ask"] else None

    # A API traz create_date, mas a gente salva um timestamp nosso também (UTC) pra padronizar.
    now_utc = datetime.now(timezone.utc).isoformat()

    return {
        "pair": "USD/BRL",
        "bid": bid,
        "ask": ask,
        "timestamp_iso": now_utc,
        "source": "AwesomeAPI",
        "raw": {
            "create_date": usdbrl.get("create_date"),
            "high": usdbrl.get("high"),
            "low": usdbrl.get("low"),
        },
    }
