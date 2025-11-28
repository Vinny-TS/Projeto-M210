import math
from typing import Dict, List, Optional

import numpy as np

from .model import SimplexResult
from .solver import TOL


def compute_shadow_prices(result: SimplexResult, num_vars: int) -> Optional[np.ndarray]:
    """Calcula y = c_B * B^{-1}. Retorna None se a base estiver singular."""
    m = result.a_std.shape[0]
    if len(result.basis) != m:
        return None

    # Extrai matriz basica B e tenta invertê-la
    B = result.a_std[:, result.basis]
    try:
        B_inv = np.linalg.inv(B)
    except np.linalg.LinAlgError:
        return None

    c_B = result.c_extended[result.basis]
    y = c_B @ B_inv
    return y


def sensitivity_ranges(result: SimplexResult, variations: List[float], num_vars: int) -> List[Dict[str, object]]:
    """Analisa se delta b em cada restricao e viavel e calcula novo lucro via preco-sombra."""
    shadow = compute_shadow_prices(result, num_vars)
    if shadow is None:
        return []

    m = result.a_std.shape[0]
    B = result.a_std[:, result.basis]
    try:
        B_inv = np.linalg.inv(B)
    except np.linalg.LinAlgError:
        return []

    # Solucao basica atual (valores das variaveis basicas)
    xB = B_inv @ result.b_std
    rows = []

    for i in range(m):
        # Coluna i de B^{-1} indica como xB varia com delta b_i
        direction = B_inv[:, i]
        incr_bounds = []
        decr_bounds = []
        for xb_j, d_j in zip(xB, direction):
            if abs(d_j) <= TOL:
                continue
            if d_j > 0:
                decr_bounds.append(xb_j / d_j)
            elif d_j < 0:
                incr_bounds.append(-xb_j / d_j)

        # Menor razao define quanto e possivel diminuir/aumentar b_i antes de violar não-negatividade
        allowable_decrease = min(decr_bounds) if decr_bounds else math.inf
        allowable_increase = min(incr_bounds) if incr_bounds else math.inf
        delta = variations[i]

        feasible = (-allowable_decrease - TOL) <= delta <= (allowable_increase + TOL)
        shadow_price = shadow[i]

        # Se viavel, ajusta lucro otimo pelo preco-sombra e delta
        new_profit = result.optimal_value + shadow_price * delta if feasible else None

        lower_limit = -allowable_decrease
        upper_limit = allowable_increase

        rows.append(
            {
                "constraint": f"Restricao {i+1}",
                "shadow_price": shadow_price,
                "delta": delta,
                "feasible": feasible,
                "new_profit": new_profit,
                "valid_range": (lower_limit, upper_limit),
            }
        )

    return rows
