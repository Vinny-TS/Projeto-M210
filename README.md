# Simplex Tableau (PPL ate 4 variaveis)

Aplicacao Streamlit para resolver problemas de programacao linear (maximizacao) com 2 a 4 variaveis usando o metodo Simplex em forma de tableau, sem bibliotecas especificas de PPL.

## Requisitos
- Python 3.9+ (recomendado)
- Dependencias listadas em `requirements.txt`

Instale-as com:
```bash
python -m pip install -r requirements.txt
```

## Como executar
1. Abra um terminal na pasta do projeto.
2. Rode o app:
   ```bash
   streamlit run main.py
   ```
3. O navegador abrirah a interface; se nao abrir, acesse o endereco indicado no terminal (geralmente http://localhost:8501).

## Fluxo de uso
1. Na barra lateral, escolha o numero de variaveis (2 a 4) e de restricoes.
2. Preencha os coeficientes da funcao objetivo (maximizacao) e das restricoes:
   - Selecione o sinal de cada restricao (`<=`, `>=` ou `=`).
   - Informe o lado direito (b).
   - Informe a variacao desejada em b (Delta b) para analisar viabilidade e novo lucro via preco-sombra.
3. Clique em **Resolver**.
4. A interface mostra:
   - Mensagem de status (otimo, ilimitado, inviavel ou limite de iteracoes).
   - Lucro otimo e valores das variaveis de decisao.
   - Precos-sombra de cada restricao, se a alteracao Delta b e viavel, novo lucro (quando viavel) e a faixa de Delta b onde o preco-sombra permanece valido.
   - Tableau final para referencia.

## Como funciona (resumo tecnico)
- A entrada eh normalizada para garantir rhs >= 0; sinais de restricoes sao ajustados conforme necessario.
- A forma padrao inclui variaveis de folga/excedente e artificiais. Artificiais recebem penalidade Big-M na funcao objetivo.
- O tableau e pivotado escolhendo a coluna com menor custo reduzido (maximizacao) e aplicando a razao minima para a linha pivot.
- Quando uma variavel artificial permanece positiva na base na otimalidade, o problema eh marcado como inviavel.
- Precos-sombra sao calculados como `y = c_B * B^{-1}` a partir da base otima; a faixa de Delta b usa B^{-1} para encontrar limites de viabilidade.

## Estrutura de pastas
- `main.py`: interface Streamlit e orquestracao.
- `simplex/solver.py`: normalizacao das restricoes, construcao da forma padrao e algoritmo Simplex com Big-M.
- `simplex/sensitivity.py`: precos-sombra, viabilidade de Delta b e novo lucro.
- `simplex/formatting.py`: formatacao numerica sem notacao cientifica.
- `simplex/model.py`: dataclasses para entrada e resultado.
