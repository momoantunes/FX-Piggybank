import requests


def notify_discord(webhook_url: str, message: str) -> None:
    """
    Envia mensagem simples via Discord Webhook.
    """
    payload = {"content": message}
    resp = requests.post(webhook_url, json=payload, timeout=20)
    resp.raise_for_status()
