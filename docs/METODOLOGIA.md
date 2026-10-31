# Decisões metodológicas

## Unidade observacional e tratamento

Cada linha é um time em uma partida. O mesmo Game_ID pode estar presente para
os dois adversários. A chave de negócio é Team_ID + Game_ID; duas linhas de
times diferentes não são duplicação. Os índices de pandas são preservados;
linha no Excel = índice + 2 (cabeçalho e contagem a partir de um).

Datas reconhecidas pelo leitor Excel são mantidas; seriais numéricos usam origem
1899-12-30. Strings devem seguir ISO AAAA-MM-DD, evitando adivinhação entre dia
e mês. Valores impossíveis viram NaT. Identificadores são texto; medidas são
numéricas. A fonte atual já traz W, L e WL numéricos, mas a conversão é explícita
e WL textual W/L também é aceito.

Taxas são reconstruídas com FGM/FGA, FG3M/FG3A, FTM/FTA e W/(W+L). Isso corrige
a mistura de casas decimais sem supor que todo valor precisa ser dividido por
mil. A comparação de divergências usa tolerância absoluta 0,00051 e relativa
zero, admitindo arredondamento a três casas. O dataset tratado usa o quociente
completo, não o valor arredondado. Contagens inválidas não são recuperadas
automaticamente; sinais de inconsistência não informam qual lado está errado.

Na base fornecida não há ausentes, negativos, duplicatas nem divergências nas
identidades de pontos e rebotes. Existem zeros legítimos e taxas inconsistentes.
Os testes Little, Jamshidian–Jalal, Listing–Schlittgen e a abordagem logística
de Fairclough são explicados no relatório, não simulados para produzir p-valores.
Sem ausências, não há grupos de padrões de missingness a comparar. Uma futura
base com missing exigirá implementação validada conforme seus pressupostos.

## Medidas descritivas

- Desvio e variância **amostrais**, denominador n−1. N<2: indefinidos.
- Q1, mediana e Q3: quantis lineares tipo 7, consistentes em todas as saídas.
- Moda: todas as contagens empatadas na frequência máxima, desde que haja
  repetição; sem repetição é apresentado “sem repetição”.
- CV em percentual = 100s/média, somente para média positiva. O alerta de média
  menor que 5 é uma decisão operacional, não um limite estatístico universal.
- Assimetria ajustada de Fisher–Pearson, scipy `skew(bias=False)`; direção pelo
  sinal e intensidade pelos cortes absolutos 0,5 e 1. Constantes e n<3: N/A.
- IQR = Q3−Q1 e outliers estritamente fora de [Q1−1,5IQR, Q3+1,5IQR]. Bigodes
  são observações existentes; os limites teóricos também aparecem no desenho.
- IQR/mediana em %: indicador robusto de dispersão relativa, não o mesmo CV.
- DP sem extremos IQR: sensibilidade, não substitui o DP original.

## Detecção

Todos os métodos rodam por coluna numérica e por time. Excluem identificadores,
datas, texto e WL binário. Não há modelo de alta dimensionalidade. Os valores
ausentes são ignorados; n<3 ou série constante não recebem flags. A contagem zero
nesses casos significa regra não aplicável, conforme o diagnóstico da tabela.

IQR e |Z|>3 usam os dados na escala original e s amostral. Grubbs bilateral
usa α=0,05 e uma única aplicação; só marca quando Shapiro–Wilk p≥0,05 e G supera
o valor crítico. Não aplicar Grubbs iterativamente sem controle de erro.
Shapiro é uma verificação auxiliar, não prova de normalidade. Não há correção
global entre as muitas colunas/times: a análise é exploratória.

ECOD (PyOD, contamination 0,05), kNN (k=min(5,n−1), distância ao k-ésimo vizinho,
limiar p95), DBSCAN (eps 0,5; min_samples 5) e LOF (contamination 0,05) usam
StandardScaler na série. Seu DP populacional é convenção de escalonamento,
não mudança nas medidas descritivas. LOF usa k=min(max(20, frequência máxima
de um valor),n−1), para evitar vizinhanças compostas somente por empates.
O k efetivo está na auditoria. Empates podem produzir menos de 5% de sinais.
Não se deve interpretar contamination como prevalência comprovada de erros.

ECOD implementa a combinação das caudas e ajuste de assimetria da biblioteca;
não substituímos o algoritmo por um simples ranking bilateral. As versões
estão fixadas para manter esse comportamento reproduzível.

## Leitura dos gráficos

KDE de SciPy usa banda de Scott; só é calculada com pelo menos dois valores
distintos. Histograma normalizado em densidade, eixos e legendas com unidades.
KDE suaviza contagens inteiras; efeitos de borda e escolha de classes podem
contrastar com a assimetria de momento. A interpretação dinâmica compara a
posição da mediana na caixa (Bowley) com Fisher–Pearson, explicando divergências
entre forma central e caudas, sem alegar inspeção visual automática da KDE.

Nas barras, z médio = (média do time−média do conjunto selecionado)/s do conjunto.
O conjunto é ponderado pelo número de observações. Se s=0, z=0 por convenção.
Não padronizar cada time separadamente e depois comparar médias, que seriam zero.

## Referências

- [NIST, Grubbs](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h1.htm).
- [ECOD, artigo original](https://arxiv.org/abs/2201.00382) e
  [implementação PyOD](https://pyod.readthedocs.io/en/latest/_modules/pyod/models/ecod.html).
- [scikit-learn, detecção de anomalias](https://scikit-learn.org/stable/modules/outlier_detection.html).
- [Little, 1988](https://doi.org/10.1080/01621459.1988.10478722).
- [Jamshidian e Jalal, 2010](https://pubmed.ncbi.nlm.nih.gov/21720450/).
- [Estudo de mecanismos de ausência, LS e Fairclough](https://pmc.ncbi.nlm.nih.gov/articles/PMC2711047/).
