# Validação da entrega

Ambiente: Windows, Python 3.10.0 de 64 bits, dependências em `.venv`.

- Nove testes automatizados aprovados, sem avisos: estatísticas com resultados
  conhecidos, quartis, modas, séries constantes/ausentes, alinhamento de índices,
  Grubbs, tratamento da fonte real, exclusão de vazamento e rotas/exportação.
- Ruff: nenhuma ocorrência e todos os arquivos Python formatados.
- `pip check`: nenhuma dependência incompatível.
- Relatório restrito a Los Angeles Clippers e Miami Heat. Testes confirmam que
  URLs e exportações rejeitam times de fora do grupo e que o CSV padrão contém
  exclusivamente os dois times.
- As sete variáveis e as seis modalidades de CSV: HTTP 200.
- Navegador: conferidos carregamento, boxplot, rolagem em tela estreita e
  atualização após mudar times e variável.

As verificações numéricas não substituem a revisão metodológica da equipe.
Os detectores são exploratórios; não foram validados com rótulos de anomalias
reais e não há estimativas de precisão/recall. A fonte original não foi editada.
