from dataclasses import dataclass
from typing import Dict, List

import numpy as np


@dataclass
class ConstraintInput:
    coefficients: List[float]
    sense: str  # "<=", ">=", "="
    rhs: float
    variation: float


@dataclass
class SimplexResult:
    status: str
    message: str
    optimal_value: float
    solution: Dict[str, float]
    basis: List[int]
    tableau: List[List[float]]
    a_std: np.ndarray
    b_std: np.ndarray
    c_extended: np.ndarray
    artificial_in_basis: bool
