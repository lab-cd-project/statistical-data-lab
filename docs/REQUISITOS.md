# Correspondência com o enunciado

| Solicitação | Onde conferir |
| --- | --- |
| Sistema web Python navegável e interativo | Flask, `/projeto-1/`, filtros de times/variável/medida |
| Resultados e interpretação no próprio sistema | Seções 01–07; síntese muda com o recorte |
| Dimensão, colunas e contexto | Seção 01, cartões e dicionário expansível |
| Tipos originais e tratados | Seção 02, auditoria de qualidade |
| Datas, nomes intuitivos, conversões W/L | `schema.py`, `data.py` e seções 01–02 |
| Exclusão de atributos para modelos | Matriz exportável separada; cenário pré-jogo explicado na seção 07 |
| Zeros, negativos, duplicatas e domínios | Auditoria por coluna, checagens cruzadas, totais de duplicatas |
| Ausências e MCAR/MAR/MNAR | Seção 02; fonte sem ausentes, testes não aplicáveis |
| Little, Jamshidian–Jalal, LS, Fairclough | Discussão teórica de uso e pressupostos na seção 02 |
| Z-score, Grubbs, ECOD, K-NN, DBSCAN, LOF | Implementados em `analysis.py`; parâmetros e limites na seção 06 |
| Inconsistentes e outliers por coluna | Qualidade da base e contagens de detectores por time/coluna numérica |
| Média, mediana, moda, extremos e dispersão | Seção 03 para as sete variáveis de todos os times selecionados |
| Quantos e quais outliers | Contagens e listagem por variável; exportação detalhada com jogo e linha Excel |
| Boxplot com medidas e limites | Seção 04, mesmo quartil e limiar da tabela |
| Barras e participação do z-score | Seção 04, filtro de medida e explicação da referência conjunta |
| Assimetria, fórmula, direção e intensidade | Seções 03 e 05; scipy Fisher–Pearson ajustado |
| Histograma/KDE e comparação com boxplot | Seção 04 e diagnóstico dinâmico de posição central na síntese |
| CV, validade, comparação entre escalas e times | Quadro CV e síntese do recorte; alerta de média pequena |
| IQR, método, limites, quadros e comparação | Seção 03; sensibilidade DP sem extremos e interpretação na seção 05 |
| Títulos, eixos, unidades e legendas | `charts.py`; unidades das tabelas no relatório |
| Organização para colaboração e expansão | Camadas independentes, Blueprints, docs e CONTRIBUTING |
| Dependências isoladas | `.venv`, pins e inicializador que usa o ambiente local |
| Hospedagem ou execução local documentada | Alternativa local do enunciado, README com comando único após instalação |
| Entrega Classroom | Fonte preparada; envio e eventual link público ficam a cargo da equipe |

## Decisões que a equipe deve revisar

Os times do grupo são Los Angeles Clippers e Miami Heat, selecionados por padrão.
Somente esses dois times são disponibilizados na interface e nas exportações.
A auditoria também considera apenas o grupo; a planilha original é preservada.
Os limiares de detecção e a seleção de atributos são decisões explícitas e
revisáveis, não requisitos inventados para uma futura etapa. Antes de entregar,
a equipe deve selecionar seus times, ler as interpretações e confirmar com o
professor eventuais expectativas de inferência ou testes adicionais. O sistema
não inventa p-valores de missingness para uma base completa.
