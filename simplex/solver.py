import math
from typing import List, Tuple

import numpy as np

from .model import ConstraintInput, SimplexResult

TOL = 1e-8  # tolerancia numerica para comparacoes em ponto flutuante
BIG_M = 1e6  # penalidade Big-M atribuida a variaveis artificiais


def normalize_constraint(coeffs: List[float], sense: str, rhs: float, variation: float) -> Tuple[List[float], str, float, float]:
    """Garante rhs >= 0. Se rhs for negativo, multiplica a linha por -1 e inverte o sentido."""
    if rhs >= 0:
        return coeffs, sense, rhs, variation

    new_coeffs = [-c for c in coeffs]
    new_rhs = -rhs
    new_variation = -variation

    if sense == "<=":
        new_sense = ">="
    elif sense == ">=":
        new_sense = "<="
    else:
        new_sense = "="

    return new_coeffs, new_sense, new_rhs, new_variation


def build_standard_form(num_vars: int, constraints: List[ConstraintInput]) -> Tuple[np.ndarray, np.ndarray, List[str], List[int], int, int]:
    """Constroi A_std (folgas, excedentes e artificiais), vetor b, nomes das variaveis e base inicial."""
    normalized = [normalize_constraint(c.coefficients, c.sense, c.rhs, c.variation) for c in constraints]

    senses = [s for _, s, _, _ in normalized]
    b = np.array([rhs for _, _, rhs, _ in normalized], dtype=float)

    # Contabiliza quantas colunas extras serao adicionadas
    slack_count = sum(1 for s in senses if s in ("<=", ">="))  # folgas/excedentes
    artificial_count = sum(1 for s in senses if s in (">=", "="))  # artificiais

    total_cols = num_vars + slack_count + artificial_count
    a_std = np.zeros((len(constraints), total_cols), dtype=float)
    var_names = [f"x{idx+1}" for idx in range(num_vars)]
    basis: List[int] = []

    slack_idx = 0
    artificial_idx = 0

    for i, (coeffs, sense, _, _) in enumerate(normalized):
        a_std[i, :num_vars] = coeffs

        if sense == "<=":
            # Restricao de menor igual recebe variavel de folga (+1) que entra na base
            a_std[i, num_vars + slack_idx] = 1.0
            var_names.append(f"s{slack_idx+1}")
            basis.append(num_vars + slack_idx)
            slack_idx += 1
        elif sense == ">=":
            # Restricao de maior igual recebe excedente (-1) e artificial (+1) para viabilizar a base
            a_std[i, num_vars + slack_idx] = -1.0
            var_names.append(f"s{slack_idx+1}")
            slack_idx += 1
            a_std[i, num_vars + slack_count + artificial_idx] = 1.0
            var_names.append(f"a{artificial_idx+1}")
            basis.append(num_vars + slack_count + artificial_idx)
            artificial_idx += 1
        else:  # "="
            a_std[i, num_vars + slack_count + artificial_idx] = 1.0
            var_names.append(f"a{artificial_idx+1}")
            basis.append(num_vars + slack_count + artificial_idx)
            artificial_idx += 1

    return a_std, b, var_names, basis, slack_count, artificial_count


def simplex_tableau(c: List[float], constraints: List[ConstraintInput], maximize: bool = True) -> SimplexResult:
    """Executa o Simplex com Big-M em forma de tableau. Se minimize, converte para max."""
    num_vars = len(c)
    c = list(c)  # copia defensiva
    if not maximize:
        c = [-coef for coef in c]  # min -> max
    a_std, b_std, var_names, basis, slack_count, artificial_count = build_standard_form(num_vars, constraints)

    m, total_cols = a_std.shape
    # Tableau tem m linhas de restricao + 1 de objetivo e ultima coluna para RHS
    tableau = np.zeros((m + 1, total_cols + 1), dtype=float)
    tableau[:m, :total_cols] = a_std
    tableau[:m, -1] = b_std

    c_extended = np.concatenate([np.array(c, dtype=float), np.zeros(total_cols - num_vars)])
    obj_row = np.concatenate([-c_extended, [0.0]])

    if artificial_count > 0:
        # Penaliza artificiais no objetivo (metodo Big-M)
        art_start = num_vars + slack_count
        for j in range(artificial_count):
            obj_row[art_start + j] = -BIG_M  # penaliza artificiais (max)

    tableau[-1, :] = obj_row

    # Ajusta objetivo para artificiais basicas (remove penalidade ja presente no RHS)
    for row_idx, var_idx in enumerate(basis):
        if var_idx >= num_vars + slack_count:  # artificial na base
            tableau[-1, :] += BIG_M * tableau[row_idx, :]  # zera custo e move constante

    iteration = 0
    max_iter = 200

    def pivot(pivot_row: int, pivot_col: int) -> None:
        nonlocal tableau
        pivot_val = tableau[pivot_row, pivot_col]
        # Normaliza linha pivot e elimina coluna pivot das demais linhas
        tableau[pivot_row, :] /= pivot_val
        for r in range(tableau.shape[0]):
            if r == pivot_row:
                continue
            factor = tableau[r, pivot_col]
            tableau[r, :] -= factor * tableau[pivot_row, :]

    status = "optimal"
    message = "Otimo encontrado."

    while True:
        iteration += 1
        if iteration > max_iter:
            status = "iteration_limit"
            message = "Limite de iteracoes atingido."
            break

        reduced_costs = tableau[-1, :-1]
        # Colunas com custo reduzido negativo sao candidatas a entrar na base
        negative_cols = [idx for idx, val in enumerate(reduced_costs) if val < -TOL]
        if not negative_cols:
            break  # otimo

        entering = None
        for idx in negative_cols:
            col_vals = tableau[:m, idx]
            if np.any(col_vals > TOL):
                entering = idx
                break

        if entering is None:
            status = "unbounded"
            message = "Problema ilimitado (nenhuma coluna negativa com entrada positiva)."
            break

        ratios = []
        for i in range(m):
            col_val = tableau[i, entering]
            if col_val > TOL:
                ratios.append(tableau[i, -1] / col_val)
            else:
                ratios.append(math.inf)

        min_ratio = min(ratios)
        if math.isinf(min_ratio):
            status = "unbounded"
            message = "Problema ilimitado."
            break

        pivot_row = ratios.index(min_ratio)
        pivot(pivot_row, entering)
        basis[pivot_row] = entering

    # Constroi a solucao basica a partir da base final
    solution = {name: 0.0 for name in var_names}
    for i, var_idx in enumerate(basis):
        if var_idx < len(var_names):
            solution[var_names[var_idx]] = tableau[i, -1]

    optimal_value = tableau[-1, -1]

    # Sinaliza inviabilidade se alguma artificial permanece positiva na base
    artificial_in_basis = any(
        var_names[idx].startswith("a") and tableau[i, -1] > TOL for i, idx in enumerate(basis)
    )
    if artificial_in_basis and status == "optimal":
        status = "infeasible"
        message = "Solucao inviavel (variavel artificial positiva na base)."

    return SimplexResult(
        status=status,
        message=message,
        optimal_value=optimal_value,
        solution=solution,
        basis=basis,
        tableau=tableau.tolist(),
        a_std=a_std,
        b_std=b_std,
        c_extended=c_extended,
        artificial_in_basis=artificial_in_basis,
    )
