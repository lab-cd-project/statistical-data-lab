"""Contrato de dados compartilhado. Novas etapas reutilizam os nomes canônicos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    description: str
    kind: str = "numérica discreta"
    unit: str = "contagem"


SCHEMA = {
    "Team_ID": Column(
        "time_id", "Identificador do time; não é medida quantitativa", "identificador", "—"
    ),
    "Game_ID": Column(
        "jogo_id", "Identificador da partida, compartilhado pelos adversários", "identificador", "—"
    ),
    "GAME_DATE": Column("data_jogo", "Data da partida", "data", "AAAA-MM-DD"),
    "MATCHUP": Column(
        "confronto", "Siglas dos adversários; vs. indica casa e @ indica fora", "texto", "—"
    ),
    "WL": Column("venceu", "Resultado: vitória=1, derrota=0", "binária", "0 ou 1"),
    "W": Column("vitorias_acumuladas", "Vitórias acumuladas na temporada, incluindo o jogo"),
    "L": Column("derrotas_acumuladas", "Derrotas acumuladas na temporada, incluindo o jogo"),
    "W_PCT": Column(
        "taxa_vitorias", "Vitórias / (vitórias + derrotas)", "numérica contínua", "fração [0,1]"
    ),
    "MIN": Column(
        "minutos",
        "Soma de minutos dos jogadores; 240 no tempo regulamentar",
        unit="minutos de jogadores",
    ),
    "FGM": Column("arremessos_convertidos", "Arremessos de quadra convertidos"),
    "FGA": Column("arremessos_tentados", "Arremessos de quadra tentados"),
    "FG_PCT": Column(
        "taxa_arremessos", "Arremessos convertidos / tentados", "numérica contínua", "fração [0,1]"
    ),
    "FG3M": Column("cestas_tres", "Cestas de três pontos convertidas"),
    "FG3A": Column("tentativas_tres", "Arremessos de três pontos tentados"),
    "FG3_PCT": Column(
        "taxa_tres", "Cestas de três / tentativas de três", "numérica contínua", "fração [0,1]"
    ),
    "FTM": Column("lances_livres_convertidos", "Lances livres convertidos"),
    "FTA": Column("lances_livres_tentados", "Lances livres tentados"),
    "FT_PCT": Column(
        "taxa_lances_livres",
        "Lances livres convertidos / tentados",
        "numérica contínua",
        "fração [0,1]",
    ),
    "OREB": Column("rebotes_ofensivos", "Rebotes no ataque"),
    "DREB": Column("rebotes_defensivos", "Rebotes na defesa"),
    "REB": Column("rebotes", "Rebotes totais"),
    "AST": Column("assistencias", "Passes que resultaram em cestas"),
    "STL": Column("roubos", "Roubos de bola"),
    "BLK": Column("bloqueios", "Bloqueios de arremesso (tocos)"),
    "TOV": Column("erros", "Perdas de posse de bola"),
    "PF": Column("faltas", "Faltas pessoais cometidas"),
    "PTS": Column("pontos", "Pontos marcados pelo time", unit="pontos"),
    "TEAM_NAME": Column("time", "Nome do time", "categórica nominal", "—"),
}
VARIABLES = {
    "pontos": "Pontos",
    "rebotes": "Rebotes",
    "assistencias": "Assistências",
    "roubos": "Roubos de bola (STL)",
    "bloqueios": "Bloqueios (BLK)",
    "faltas": "Faltas pessoais (PF)",
    "cestas_tres": "Cestas de três (FG3M)",
}
RATIOS = {
    "taxa_vitorias": ("vitorias_acumuladas", None),
    "taxa_arremessos": ("arremessos_convertidos", "arremessos_tentados"),
    "taxa_tres": ("cestas_tres", "tentativas_tres"),
    "taxa_lances_livres": ("lances_livres_convertidos", "lances_livres_tentados"),
}
