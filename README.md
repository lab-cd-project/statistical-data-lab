# Laboratório de Ciência de Dados

Sistema web em Python/Flask que apresenta o relatório com base no arquivo
`stats_times_regular_final.xlsx`.

## Executar local

Recomendação para reproduzir o ambiente validado: **Python 3.10, 64 bits**.
O código usa Python 3.10 ou superior; outras versões exigem verificar a
disponibilidade das versões fixadas das bibliotecas. Use a pasta do projeto
como diretório atual e mantenha a planilha original na raiz.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
python run.py
```

No Linux/macOS, o segundo comando é:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Abra **http://127.0.0.1:5000**. Para encerrar, pressione `Ctrl+C` no terminal.
`run.py` encaminha a execução ao Python da `.venv`, mesmo quando iniciado pelo
Python global. Não é necessário ativar o ambiente nem alterar a política do PowerShell.
O servidor utilizado é Waitress, com modo de depuração desativado.

`requirements.txt` fixa as dependências diretas. `requirements-lock.txt` registra
também as transitivas do ambiente validado (incluindo ferramentas de desenvolvimento).
Para reproduzir esse ambiente completo, instale o arquivo lock em vez do requirements
principal. O lock foi gerado no Windows/Python 3.10; não é uma garantia entre plataformas.

## Usar o relatório

1. Os times da equipe, **Los Angeles Clippers e Miami Heat**, já aparecem
   selecionados inicialmente. Somente esses dois times estão disponíveis no relatório.
2. Escolha uma das sete variáveis e a medida das barras. Clique em **Atualizar relatório**.
3. Navegue por base/dicionário, qualidade, estatísticas, gráficos, síntese e métodos.
4. Expanda as tabelas de auditoria e a lista de jogos sinalizados. As tabelas largas
   têm rolagem horizontal e vertical. Em telas pequenas, os gráficos têm rolagem horizontal.
5. Exporte CSV no final da página. Dados e estatísticas respeitam os times selecionados;
   a auditoria de qualidade sempre cobre os dois times do grupo. O CSV detalhado contém todos
   os campos/métodos, enquanto a listagem da tela mostra a variável selecionada.

Os gráficos são servidos localmente, sem CDN; após instalar as bibliotecas, o
relatório funciona sem internet. A primeira consulta pode demorar mais por carregar
as bibliotecas e calcular os detectores; consultas do mesmo recorte usam cache.

## Conteúdo implementado

- Dicionário de 28 colunas com nomes intuitivos, tipos, significados e unidades.
- Tratamento de datas, identificadores e W/L; resultado WL binário.
- Auditoria de ausentes, zeros, negativos, duplicatas, domínios e relações aritméticas.
- Reconstrução rastreável das quatro taxas cuja origem mistura escalas.
- Média, mediana, todas as modas repetidas, mínimo, máximo, amplitude, desvio e
  variância amostrais, quartis, IQR, CV e assimetria por variável e time.
- Boxplot com quartis, média, mediana, modas, limites e extremos; histograma/KDE;
  barras comparativas, inclusive médias padronizadas em z-score.
- IQR, Z-score, Grubbs, ECOD, K-NN, DBSCAN e LOF, com contagem por coluna
  numérica/time e rastreamento dos jogos pela linha original do Excel.
- Quadros de CV e IQR, interpretação dinâmica e análise de sensibilidade do DP.
- Discussão de MCAR, MAR, MNAR, Little, Jamshidian–Jalal, LS e Fairclough.
- Matriz de atributos separada para um cenário futuro de previsão pré-jogo,
  excluindo colunas com vazamento do resultado da partida atual.

A fonte contém **2.238 registros, 28 colunas, 30 times**, de **21/10/2025 a
29/03/2026**. Não há ausentes nem duplicatas na fonte. As contagens que
divergem do quociente por mais de 0,00051 são: W_PCT 1.788, FG_PCT 1.983,
FG3_PCT 1.913 e FT_PCT 1.768 células. Todas as taxas são recalculadas;
essas contagens medem divergências, não apenas o número de atribuições feitas.
Os arquivos originais permanecem intactos.

Essas dimensões e contagens descrevem o arquivo original inteiro. A aplicação
restringe a leitura analítica a **Los Angeles Clippers e Miami Heat**, incluindo
os diagnósticos de qualidade. Por isso, as contagens exibidas no relatório são
as do grupo, sem registros dos demais times.

## Estrutura e leitura recomendada

```text
run.py                       # entrada local que usa a .venv
src/nba_lab/
  __init__.py                # cria o Flask e registra os módulos
  schema.py                  # contrato, nomes e unidades dos dados
  data.py                    # leitura, tratamento, auditoria e atributos futuros
  analysis.py                # cálculos puros e detecção de outliers
  charts.py                  # gráficos Plotly usando as mesmas convenções
  project1.py                # rotas e composição do relatório
  templates/report.html     # relatório, interpretações e metodologia
  static/style.css          # apresentação responsiva
tests/                       # resultados conhecidos, dados reais e rotas
docs/
  ARQUITETURA.md             # fluxo, responsabilidades e como integrar Projeto 2
  METODOLOGIA.md             # convenções, limites e fontes
  REQUISITOS.md              # correspondência com o enunciado

```

Comece por `schema.py`, depois `data.py` e `analysis.py`. A interface não contém
fórmulas estatísticas. Essa separação permite corrigir ou reutilizar uma regra
sem editar o HTML ou criar cópias para cada novo projeto.

## Verificar alterações

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
```

Consulte [CONTRIBUTING.md](CONTRIBUTING.md) antes de contribuir.

## Configuração

Configurações opcionais no PowerShell:

```powershell
$env:NBA_DATA_PATH = 'C:\caminho\stats_times_regular_final.xlsx'
$env:PORT = '5001'
python run.py
```

## Limites metodológicos

Os detectores são **univariados e exploratórios**, por time. Não há previsão,
inferência causal, exclusão automática de jogos nem imputação. Grubbs depende
de normalidade aproximada e avalia um único extremo por aplicação. Testes de
missingness são discutidos, não executados: não há ausências nesta fonte.
Selecionar muitos times aumenta o volume de tabelas e a primeira execução.
Para bases maiores, evolua o processamento conforme `docs/ARQUITETURA.md`.
