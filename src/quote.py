import time
import requests
from datetime import datetime, timezone, date


def _get_json_with_retries(url: str, timeout: int = 20, retries: int = 4) -> dict:
    """
    GET com retries e backoff exponencial.
    - Se der 429 ou 5xx, tenta de novo.
    - Se der 4xx (exceto 429), falha direto.
    """
    last_exc = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "usd-piggybank/1.0"})
            if resp.status_code == 429 or 500 <= resp.status_code <= 599:
                # backoff: 1s, 2s, 4s, 8s...
                wait = 2 ** attempt
                time.sleep(wait)
                continue

            resp.raise_for_status()
            return resp.json()

        except Exception as exc:
            last_exc = exc
            # backoff também em exceções de rede
            wait = 2 ** attempt
            time.sleep(wait)

    raise RuntimeError(f"Falha ao buscar dados após retries. Último erro: {last_exc}")


def fetch_usd_brl() -> dict:
    """
    Tenta AwesomeAPI primeiro; se falhar (ex: 429), cai pro PTAX (Banco Central).
    Retorna um dict padronizado.
    """
    now_utc = datetime.now(timezone.utc).isoformat()

    # 1) AwesomeAPI (pode dar 429)
    awesome_url = "https://economia.awesomeapi.com.br/json/last/USD-BRL"
    try:
        data = _get_json_with_retries(awesome_url, retries=2)
        usdbrl = data.get("USDBRL")
        if not usdbrl:
            raise RuntimeError("Resposta inesperada da AwesomeAPI (USDBRL ausente).")

        bid = float(usdbrl["bid"])
        ask = float(usdbrl["ask"]) if usdbrl.get("ask") else None

        return {
            "pair": "USD/BRL",
            "bid": bid,
            "ask": ask,
            "timestamp_iso": now_utc,
            "source": "AwesomeAPI",
            "raw": {"create_date": usdbrl.get("create_date"), "high": usdbrl.get("high"), "low": usdbrl.get("low")},
        }
    except Exception:
        # 2) Fallback: PTAX (Banco Central)
        # Endpoint OData do BCB. A forma mais simples: pegar o último valor disponível para o dia.
        # Usamos a data de hoje (UTC) mas PTAX é BR; em fins de semana pode não ter -> pega o último disponível via orderby desc/top 1.
        today = date.today().strftime("%m-%d-%Y")

        # Pega o último registro disponível (mais recente), sem ficar dependente do dia ter cotação.
        # cotacaoVenda ~ bid (aproximação pra nosso uso)
        ptax_url = (
            "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            "CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao="
            f"'{today}'&$format=json"
        )

        ptax_data = _get_json_with_retries(ptax_url, retries=4)
        values = ptax_data.get("value", [])
        if not values:
            # Se não houver no dia (fim de semana/feriado), tenta “última cotação disponível” via series diárias (fallback extra)
            # Aqui fazemos uma busca de uma janela curta (7 dias) e pegamos o último.
            # (mantém robusto sem complicar demais)
            from datetime import timedelta

            start = (date.today() - timedelta(days=7)).strftime("%m-%d-%Y")
            end = date.today().strftime("%m-%d-%Y")

            ptax_range_url = (
                "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
                "CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)?"
                f"@dataInicial='{start}'&@dataFinalCotacao='{end}'&$format=json"
            )

            rng = _get_json_with_retries(ptax_range_url, retries=4)
            values = rng.get("value", [])
            if not values:
                raise RuntimeError("PTAX sem valores retornados (nem hoje, nem na última semana).")

        last = values[-1]
        bid = float(last["cotacaoVenda"])

        return {
            "pair": "USD/BRL",
            "bid": bid,
            "ask": None,
            "timestamp_iso": now_utc,
            "source": "BCB PTAX",
            "raw": {"dataHoraCotacao": last.get("dataHoraCotacao"), "cotacaoCompra": last.get("cotacaoCompra")},
        }
