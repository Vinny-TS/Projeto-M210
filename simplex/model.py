from dataclasses import dataclass
from typing import Dict, List

import numpy as np


@dataclass
class ConstraintInput:
    """Entrada de uma restricao: coeficientes, sentido, RHS e variacao (Delta b) para analise de sensibilidade."""

    coefficients: List[float]
    sense: str  # "<=", ">=", "="
    rhs: float
    variation: float


@dataclass
class SimplexResult:
    """Resultado completo do Simplex em tableau, incluindo artefatos para analise de sensibilidade."""

    status: str
    message: str
    optimal_value: float
    solution: Dict[str, float]
    basis: List[int]  # indices das variaveis na base final
    tableau: List[List[float]]  # tableau final como lista para serializacao
    a_std: np.ndarray  # matriz A na forma padrao
    b_std: np.ndarray  # RHS apos normalizacao
    c_extended: np.ndarray  # custos extendidos (inclui folgas/excedentes/artificiais)
    artificial_in_basis: bool  # indica se alguma artificial permanece positiva na base
