from typing import Optional


def percent_change(current: float, previous: Optional[float]) -> Optional[float]:
    if previous is None:
        return None
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100.0


def should_notify_always() -> bool:
    # MVP: sempre notifica
    return True


def should_notify_threshold(current: float, below: Optional[float] = None, above: Optional[float] = None) -> bool:
    """
    Regras opcionais (não vamos ligar agora, mas fica pronto).
    """
    if below is not None and current < below:
        return True
    if above is not None and current > above:
        return True
    return False
