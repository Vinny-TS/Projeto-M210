import math
from typing import Optional


def format_value(val: Optional[float], decimals: int = 4) -> str:
    """Evita notacao cientifica usando formato fixo, lidando com None e infinito."""
    if val is None:
        return "-"
    if math.isinf(val):
        return "infinito"
    return f"{val:.{decimals}f}"
