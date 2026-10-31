from io import StringIO
from pathlib import Path

import pandas as pd
import pytest

from nba_lab import create_app
from nba_lab.data import load_dataset, model_features
from nba_lab.schema import SCHEMA

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def dataset():
    return load_dataset(ROOT / "stats_times_regular_final.xlsx")


def test_real_source_is_preserved_and_ratios_repaired(dataset):
    assert dataset.raw.shape == (2238, 28)
    assert dataset.clean.shape == dataset.raw.shape
    assert dataset.raw.loc[0, "FG_PCT"] == 506
    assert dataset.clean.loc[0, "taxa_arremessos"] == pytest.approx(45 / 89)
    assert str(dataset.clean.data_jogo.dtype) == "datetime64[ns]"
    assert dataset.clean.data_jogo.min() == pd.Timestamp("2025-10-21")
    assert dataset.clean.time_id.dtype.name == "string"
    assert len(SCHEMA) == 28


def test_features_exclude_current_game_and_target(dataset):
    features = model_features(dataset.clean)
    assert set(features) == {"em_casa", "dia_semana", "mes"}
    assert features.loc[0, "em_casa"] == 1
    assert features.loc[1, "em_casa"] == 0
    assert not features.isna().any().any()


def test_report_filters_validation_and_exports():
    client = create_app({"TESTING": True}).test_client()
    assert client.get("/").status_code == 302
    assert client.get("/health").json == {"status": "ok"}
    response = client.get("/projeto-1/?time=Boston+CEltics")
    assert response.status_code == 400
    response = client.get("/projeto-1/?time=Miami+Heat&variavel=bloqueios&medida=CV+(%25)")
    assert response.status_code == 200
    assert "Não há ausências na fonte" in response.text
    assert "Bloqueios (BLK)" in response.text
    assert "plotly" in response.text
    csv = client.get("/projeto-1/exportar/estatisticas.csv?time=Miami+Heat")
    assert csv.status_code == 200
    assert "Miami Heat" in csv.text
    assert "Boston Celtics" not in csv.text
    assert client.get("/projeto-1/?variavel=inexistente").status_code == 400
    assert client.get("/projeto-1/exportar/inexistente.csv?time=Miami+Heat").status_code == 404
    # Restringir só o formulário não basta: URLs e exportações também respeitam o escopo.
    assert client.get("/projeto-1/?time=Atlanta+Hawks").status_code == 400
    assert client.get("/projeto-1/exportar/dados.csv?time=Atlanta+Hawks").status_code == 400
    csv = client.get("/projeto-1/exportar/dados.csv")
    exported = pd.read_csv(StringIO(csv.text), sep=";")
    assert set(exported.time) == {"Los Angeles Clippers", "Miami Heat"}
    assert exported.shape[0] < 2238


def test_missing_file_has_clear_message(tmp_path):
    client = create_app(
        {"TESTING": True, "DATA_PATH": str(tmp_path / "missing.xlsx")}
    ).test_client()
    assert client.get("/projeto-1/").status_code == 503
