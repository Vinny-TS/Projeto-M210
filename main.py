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


def build_objective_inputs(num_vars: int):
    st.subheader("Funcao objetivo (maximizar)")
    cols = st.columns(num_vars)
    objective = []
    for i in range(num_vars):
        objective.append(cols[i].number_input(f"Coeficiente de x{i+1}", value=0.0, format="%.6f"))
    return objective


def build_constraints(num_vars: int, num_constraints: int):
    st.subheader("Restricoes")
    constraints = []
    for r in range(num_constraints):
        cols = st.columns(num_vars + 3)
        coeffs = [cols[c].number_input(f"r{r+1} - coef x{c+1}", value=0.0, format="%.6f") for c in range(num_vars)]
        sense = cols[num_vars].selectbox(f"r{r+1} sinal", options=["<=", ">=", "="], index=0, key=f"sense_{r}")
        rhs = cols[num_vars + 1].number_input(f"r{r+1} lado direito", value=0.0, format="%.6f")
        variation = cols[num_vars + 2].number_input(f"r{r+1} variacao desejada (Delta b)", value=0.0, format="%.6f")
        constraints.append(ConstraintInput(coeffs, sense, rhs, variation))
    return constraints


def show_solution(result: SimplexResult, num_vars: int):
    st.write(f"Lucro otimo: **{format_value(result.optimal_value, 6)}**")
    sol_table = [{"Variavel": f"x{i+1}", "Valor otimo": format_value(result.solution.get(f"x{i+1}", 0.0), 6)} for i in range(num_vars)]
    st.table(sol_table)


def show_shadow_prices(constraints, result, num_vars):
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

    objective = build_objective_inputs(num_vars)
    constraints = build_constraints(num_vars, num_constraints)

    if st.button("Resolver"):
        with st.spinner("Executando Simplex..."):
            result = simplex_tableau(objective, constraints)

        st.subheader("Resultado")
        st.write(result.message)

        if result.status == "optimal":
            st.success("Solucao otima encontrada.")
            show_solution(result, num_vars)
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
