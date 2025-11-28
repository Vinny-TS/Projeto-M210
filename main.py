import numpy as np
import streamlit as st

from simplex import (
    ConstraintInput,
    SimplexResult,
    format_value,
    sensitivity_ranges,
    simplex_tableau,
)
from simplex.solver import normalize_constraint
from simplex.variables import aggregate_solution, expand_problem


def parse_float(text: str) -> float | None:
    """Converte texto para float; retorna None se vazio ou invalido."""
    cleaned = text.strip()
    if cleaned == "":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def build_objective_inputs(num_vars: int, title: str, key_prefix: str):
    """Renderiza inputs da funcao objetivo e coleta coeficientes com validacao simples."""
    st.subheader(title)
    cols = st.columns(num_vars)
    objective = []
    errors = []
    for i in range(num_vars):
        raw = cols[i].text_input(
            f"Coeficiente de x{i+1}",
            value="",
            placeholder="",
            key=f"{key_prefix}_obj_x{i+1}",
        )
        val = parse_float(raw)
        if val is None:
            errors.append(f"Coeficiente de x{i+1}")
            val = 0.0
        objective.append(val)
    return objective, errors


def build_constraints(num_vars: int, num_constraints: int, key_prefix: str):
    """Renderiza inputs das restricoes, coletando coeficientes, sinal, RHS e Delta b."""
    st.subheader("Restricoes")
    constraints = []
    errors = []
    for r in range(num_constraints):
        cols = st.columns(num_vars + 3)
        coeffs = []
        for c in range(num_vars):
            raw = cols[c].text_input(
                f"r{r+1} - coef x{c+1}",
                value="",
                placeholder="",
                key=f"{key_prefix}_r{r+1}_x{c+1}",
            )
            val = parse_float(raw)
            if val is None:
                errors.append(f"r{r+1} coef x{c+1}")
                val = 0.0
            coeffs.append(val)
        sense = cols[num_vars].selectbox(
            f"r{r+1} sinal",
            options=["<=", ">=", "="],
            index=0,
            key=f"{key_prefix}_sense_{r}",
        )
        rhs_raw = cols[num_vars + 1].text_input(
            f"r{r+1} lado direito",
            value="",
            placeholder="",
            key=f"{key_prefix}_rhs_{r}",
        )
        rhs_val = parse_float(rhs_raw)
        if rhs_val is None:
            errors.append(f"r{r+1} lado direito")
            rhs_val = 0.0

        var_raw = cols[num_vars + 2].text_input(
            f"r{r+1} variacao desejada (Delta b)",
            value="",
            placeholder="",
            key=f"{key_prefix}_var_{r}",
        )
        var_val = parse_float(var_raw)
        if var_val is None:
            errors.append(f"r{r+1} Delta b")
            var_val = 0.0

        constraints.append(ConstraintInput(coeffs, sense, rhs_val, var_val))
    return constraints, errors


def show_solution(opt_value: float, values: list):
    """Exibe valor otimo e tabela de variaveis de decisao."""
    st.write(f"Valor otimo: **{format_value(opt_value, 6)}**")
    sol_table = [{"Variavel": f"x{i+1}", "Valor otimo": format_value(val, 6)} for i, val in enumerate(values)]
    st.table(sol_table)


def show_shadow_prices(constraints, result, num_vars):
    """Calcula e mostra precos-sombra e viabilidade de variacoes em b."""
    st.subheader("Precos-sombra e analise de variacoes")
    variations = [normalize_constraint(c.coefficients, c.sense, c.rhs, c.variation)[3] for c in constraints]
    rows = sensitivity_ranges(result, variations, num_vars)
    if not rows:
        st.info("Nao foi possivel calcular precos-sombra (base invalida ou matriz singular).")
        return

    data = []
    for row in rows:
        low, high = row["valid_range"]
        data.append(
            {
                "Restricao": row["constraint"],
                "Preco-sombra": format_value(row["shadow_price"], 6),
                "Delta b desejado": format_value(row["delta"], 6),
                "Alteracao viavel?": "Sim" if row["feasible"] else "Nao",
                "Novo lucro (se viavel)": format_value(row["new_profit"], 6) if row["new_profit"] is not None else "-",
                "Faixa valida de Delta b": f"[{format_value(low, 6)}, {format_value(high, 6)}]",
            }
        )
    st.table(data)


def show_tableau(result: SimplexResult):
    """Mostra o tableau final para referencia."""
    st.subheader("Tableau final")
    st.dataframe(np.array(result.tableau))


def main():
    st.set_page_config(page_title="Simplex Tableau (PPL ate 4 variaveis)", layout="wide")
    st.title("Simplex Tableau para PPL (ate 4 variaveis)")
    st.write(
        "Informe a funcao objetivo e as restricoes. Metodo: Tableau Simplex com Big-M, sem uso de bibliotecas de PPL."
    )

    st.sidebar.header("Configuracoes")
    num_vars = st.sidebar.slider("Numero de variaveis (x)", min_value=2, max_value=4, value=3)
    num_constraints = st.sidebar.slider("Numero de restricoes", min_value=2, max_value=6, value=3)
    st.sidebar.subheader("Sinal das variaveis")
    nonneg_flags = []
    for i in range(num_vars):
        choice = st.sidebar.selectbox(
            f"x{i+1}",
            options=["x >= 0", "x livre"],
            index=0,
            key=f"var_sign_{i}",
        )
        nonneg_flags.append(choice == "x >= 0")

    st.subheader("Maximizacao")
    objective, errors_obj = build_objective_inputs(num_vars, "Funcao objetivo (maximizar)", key_prefix="max")
    constraints, errors_cons = build_constraints(num_vars, num_constraints, key_prefix="max")
    if st.button("Resolver", key="solve_max"):
        errors = errors_obj + errors_cons
        if errors:
            st.error("Preencha valores numericos validos: " + ", ".join(errors))
            st.stop()
        with st.spinner("Executando Simplex (maximizacao)..."):
            exp_c, exp_constraints, mapping = expand_problem(objective, constraints, nonneg_flags)
            result = simplex_tableau(exp_c, exp_constraints, maximize=True)
        orig_values = aggregate_solution(result.solution, mapping)
        st.subheader("Resultado")
        st.write(result.message)
        if result.status == "optimal":
            st.success("Solucao otima encontrada.")
            show_solution(result.optimal_value, orig_values)
            show_shadow_prices(constraints, result, num_vars)
            show_tableau(result)
        elif result.status == "unbounded":
            st.error("Problema ilimitado.")
        elif result.status == "infeasible":
            st.error("Problema inviavel.")
        else:
            st.warning("Algoritmo nao convergiu dentro do limite de iteracoes.")
            if result.artificial_in_basis:
                st.info("Variavel artificial permaneceu positiva; ajuste os dados do problema.")


if __name__ == "__main__":
    main()
