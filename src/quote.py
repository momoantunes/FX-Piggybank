import time
import requests
from datetime import datetime, timezone, date
from urllib.parse import quote as urlquote


def _get_json_with_retries(url: str, timeout: int = 20, retries: int = 4) -> dict:
    last_exc = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "fx-piggybank/1.0"})
            if resp.status_code == 429 or 500 <= resp.status_code <= 599:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            last_exc = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Falha ao buscar dados após retries. Último erro: {last_exc}")


def _fetch_awesome(base: str, quote: str) -> dict:
    # ex: EUR-BRL
    pair = f"{base}-{quote}"
    url = f"https://economia.awesomeapi.com.br/json/last/{pair}"
    data = _get_json_with_retries(url, retries=2)

    # A API retorna chave "USDBRL", "EURBRL", etc.
    key = f"{base}{quote}".upper()
    payload = data.get(key)
    if not payload:
        raise RuntimeError(f"Resposta inesperada da AwesomeAPI (campo {key} não encontrado).")

    bid = float(payload["bid"])
    ask = float(payload["ask"]) if payload.get("ask") else None

    return {
        "bid": bid,
        "ask": ask,
        "source": "AwesomeAPI",
        "raw": {
            "create_date": payload.get("create_date"),
            "high": payload.get("high"),
            "low": payload.get("low"),
        },
    }


def _fetch_bcb_ptax(base: str, quote: str) -> dict:
    """
    Fallback oficial: BCB PTAX via Olinda OData.
    Para moedas diferentes de USD, usa CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)
    (o próprio BCB dá exemplo com EUR). :contentReference[oaicite:2]{index=2}
    """
    if quote.upper() != "BRL":
        raise RuntimeError("Fallback BCB PTAX implementado apenas para *-BRL neste projeto.")

    today = date.today().strftime("%m-%d-%Y")
    moeda = base.upper()

    # Exemplo do BCB (EUR): CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?@moeda='EUR'&@dataCotacao='01-31-2017'&$format=json
    # :contentReference[oaicite:3]{index=3}
    ptax_url = (
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
        "CotacaoMoedaDia(moeda=@moeda,dataCotacao=@dataCotacao)?"
        f"%40moeda='{urlquote(moeda)}'&%40dataCotacao='{urlquote(today)}'&$format=json"
    )

    ptax_data = _get_json_with_retries(ptax_url, retries=4)
    values = ptax_data.get("value", [])
    if not values:
        # Em fins de semana/feriado pode vir vazio. Aí tentamos 7 dias pra trás e pegamos o último.
        from datetime import timedelta

        start = (date.today() - timedelta(days=7)).strftime("%m-%d-%Y")
        end = date.today().strftime("%m-%d-%Y")

        ptax_range_url = (
            "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            "CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?"
            f"%40moeda='{urlquote(moeda)}'&%40dataInicial='{urlquote(start)}'&%40dataFinalCotacao='{urlquote(end)}'"
            "&$format=json"
        )

        rng = _get_json_with_retries(ptax_range_url, retries=4)
        values = rng.get("value", [])
        if not values:
            raise RuntimeError("PTAX sem valores retornados (nem hoje, nem na última semana).")

    last = values[-1]
    bid = float(last["cotacaoVenda"])
    ask = None  # PTAX já é referência; mantemos ask None

    return {
        "bid": bid,
        "ask": ask,
        "source": "BCB PTAX",
        "raw": {
            "dataHoraCotacao": last.get("dataHoraCotacao"),
            "cotacaoCompra": last.get("cotacaoCompra"),
            "tipoBoletim": last.get("tipoBoletim"),
        },
    }


def fetch_quote(base: str, quote: str) -> dict:
    """
    Retorna um dict padronizado para o par base/quote:
    - pair
    - bid
    - ask
    - timestamp_iso (UTC)
    - source
    - raw (metadados)
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    base = base.upper()
    quote = quote.upper()

    # 1) Tenta spot (AwesomeAPI)
    try:
        got = _fetch_awesome(base, quote)
        return {
            "pair": f"{base}/{quote}",
            "bid": got["bid"],
            "ask": got["ask"],
            "timestamp_iso": now_utc,
            "source": got["source"],
            "raw": got["raw"],
        }
    except Exception:
        # 2) Fallback oficial (BCB PTAX)
        got = _fetch_bcb_ptax(base, quote)
        return {
            "pair": f"{base}/{quote}",
            "bid": got["bid"],
            "ask": got["ask"],
            "timestamp_iso": now_utc,
            "source": got["source"],
            "raw": got["raw"],
        }
