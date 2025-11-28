from typing import List, Tuple

from .model import ConstraintInput


def expand_problem(
    c: List[float],
    constraints: List[ConstraintInput],
    nonneg_flags: List[bool],
) -> Tuple[List[float], List[ConstraintInput], List[Tuple[int, ...]]]:
    """
    Expande variaveis livres em diferenca de duas variaveis nao-negativas.
    Retorna coeficientes expandidos, restricoes ajustadas e um mapeamento
    de cada variavel original para indices das variaveis expandidas.
    """
    if len(nonneg_flags) != len(c):
        raise ValueError("Tamanho de nonneg_flags deve ser igual ao numero de variaveis.")

    expanded_c: List[float] = []  # coeficientes da funcao objetivo apos expandir variaveis livres
    mapping: List[Tuple[int, ...]] = []  # mapeia cada variavel original para indices expandidos

    # prepara listas para novos coeficientes por restricao
    new_coeffs_matrix = [[] for _ in constraints]

    next_idx = 0
    for j, (coef_obj, nonneg) in enumerate(zip(c, nonneg_flags)):
        if nonneg:
            # Variavel ja nao-negativa: apenas propaga coeficiente
            expanded_c.append(coef_obj)
            mapping.append((next_idx,))
            for row_idx, cons in enumerate(constraints):
                new_coeffs_matrix[row_idx].append(cons.coefficients[j])
            next_idx += 1
        else:
            # Variavel livre vira diferenca de duas nao-negativas: x_j = x_pos - x_neg
            expanded_c.extend([coef_obj, -coef_obj])
            mapping.append((next_idx, next_idx + 1))
            for row_idx, cons in enumerate(constraints):
                a_j = cons.coefficients[j]
                new_coeffs_matrix[row_idx].extend([a_j, -a_j])
            next_idx += 2

    expanded_constraints: List[ConstraintInput] = []
    for cons, new_coeffs in zip(constraints, new_coeffs_matrix):
        expanded_constraints.append(
            ConstraintInput(
                coefficients=new_coeffs,
                sense=cons.sense,
                rhs=cons.rhs,
                variation=cons.variation,
            )
        )

    return expanded_c, expanded_constraints, mapping


def aggregate_solution(solution: dict, mapping: List[Tuple[int, ...]]) -> List[float]:
    """
    Reconstroi valores das variaveis originais a partir do dicionario de solucao
    das variaveis expandidas (x1, x2, ...). Para variavel livre, faz pos - neg.
    """
    values = []
    for entry in mapping:
        if len(entry) == 1:
            idx = entry[0]
            values.append(float(solution.get(f"x{idx+1}", 0.0)))
        elif len(entry) == 2:
            pos_idx, neg_idx = entry
            pos = float(solution.get(f"x{pos_idx+1}", 0.0))
            neg = float(solution.get(f"x{neg_idx+1}", 0.0))
            values.append(pos - neg)
        else:
            raise ValueError("Entrada de mapeamento invalida.")
    return values
