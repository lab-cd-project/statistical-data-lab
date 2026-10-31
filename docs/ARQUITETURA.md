# Arquitetura e evolução

## Fluxo de dados

```text
Excel original → data.load_dataset → Dataset
                                      ├ raw: evidência original
                                      ├ clean: nomes e tipos canônicos
                                      ├ quality: auditoria por coluna
                                      └ changes: taxas reconstruídas
clean → recorte por time → analysis → tabelas e interpretações
                       └ charts   → gráficos
project1 Blueprint → template Jinja → navegador e CSV
```

No Projeto 1, `GROUP_TEAMS` define Los Angeles Clippers e Miami Heat. A leitura
recebe esse escopo antes de calcular a auditoria; índices originais são mantidos
para rastreabilidade. A função de leitura continua aceitando outros escopos para
as próximas etapas, sem disponibilizá-los nas rotas do Projeto 1.

Flask foi escolhido porque é a sugestão do enunciado, exige pouca infraestrutura
e oferece Blueprints para organizar os próximos projetos. Não é necessário
um frontend separado, banco ou framework assíncrono para 2.238 observações.
Plotly permite zoom, legenda e exportação de imagens sem serviço externo.

## Responsabilidades

`schema.py` é o contrato comum, sem dependência do Flask. `data.py` não conhece
rotas nem gráficos. `analysis.py` recebe séries ou DataFrames e devolve valores
ou tabelas. `charts.py` utiliza as mesmas estatísticas, incluindo quartis e
limites, para evitar diferenças entre desenho e tabela. `project1.py` valida
parâmetros, seleciona dados e compõe resultados, sem recalcular fórmulas.
`create_app` permite configuração isolada para testes e implantação.

Não há estado de usuário em variáveis globais. Os filtros ficam na URL e podem
ser compartilhados. A fonte não é escolhida pelo visitante; `NBA_DATA_PATH` é
configuração do operador. Jinja e a geração de tabelas escapam os textos da fonte.
O servidor não recebe uploads nem escreve na planilha.

## Cache e escalabilidade

São mantidas até duas leituras de fonte e oito análises de combinações de times
em memória, usando caminho e data de modificação como chave. A variável do gráfico
não altera os detectores do recorte, por isso trocar de variável reutiliza o ajuste.
DataFrames retornados do cache devem ser tratados como somente leitura; use `.copy()`
quando precisar alterar. Reiniciar o processo esvazia o cache.

É uma arquitetura modular, com escala adequada ao dataset atual, não um sistema
distribuído. Cada processo mantém seu próprio cache. Milhões de linhas pediriam:

1. Leitura e validação em uma etapa de ingestão separada, com dados versionados
   em Parquet/banco e identificador do contrato.
2. Pré-cálculo por time/variável e armazenamento compartilhado de resultados;
   invalidação por hash da fonte, não somente data de modificação.
3. Paginação no servidor, filtros temporais e tarefas de análise fora das requisições.
4. Medição de latência/memória antes de adotar filas, múltiplos processos ou infraestrutura adicional.

O DBSCAN pode ter custo quadrático em certas configurações; sua aplicação aqui
é a séries unidimensionais com cerca de 75 jogos. Não estender esse ajuste
indiscriminadamente a bases grandes.

## Como adicionar Projeto 2

1. Crie `src/nba_lab/project2.py` ou um pacote `project2/` se houver várias páginas.
2. Defina um Blueprint com nome único, por exemplo `project2`, e prefixo `/projeto-2`.
3. Registre-o em `create_app`, ao lado do Projeto 1; mantenha `/projeto-1/` funcionando.
4. Reutilize `schema`, `load_dataset` e as funções estatísticas. Extraia um serviço
   compartilhado para leitura/cache se o segundo módulo precisar da mesma política;
   não importe funções privadas de rotas como `_analysis`.
5. Adicione seus próprios templates e testes. Só altere o contrato comum com migração
   documentada e verificação dos dois projetos.

Exemplo mínimo:

```python
from flask import Blueprint

bp = Blueprint("project2", __name__, url_prefix="/projeto-2")


@bp.get("/")
def index():
    return "Resultados do Projeto 2"
```

Registro dentro de `create_app`:

```python
from .project2 import bp as project2_bp

app.register_blueprint(project2_bp)
```

Não existe um módulo vazio de Projeto 2 no código: a extensão será feita quando
seu enunciado estiver disponível, sem antecipar requisitos desconhecidos.

## Modelagem futura

`model_features` demonstra uma seleção coerente para prever pontos antes do jogo.
Não é uma matriz final pronta para treinamento. IDs e alvo devem ser guardados
separadamente para rastreabilidade e associação das linhas. Em versões futuras,
retorne um objeto com X, y e metadados, defina o corte temporal e teste que cada
lag usa exclusivamente datas anteriores. Para jogos no mesmo dia, não confie
na ordem de linhas como ordem temporal. W/L acumulados nesta fonte incluem o
jogo atual e não podem ser usados diretamente.
