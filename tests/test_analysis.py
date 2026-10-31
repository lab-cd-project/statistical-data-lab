"""Verificações com respostas conhecidas, sem repetir as fórmulas da implementação."""

import numpy as np
import pandas as pd
import pytest

from nba_lab.analysis import describe, detect


def test_known_statistics_and_linear_quartiles():
    d = describe(pd.Series([1, 2, 3, 4, 100]))
    assert d["média"] == 22
    assert d["mediana"] == 3
    assert (d["Q1"], d["Q3"], d["IQR"]) == (2, 4, 2)
    assert d["outliers IQR"] == 1
    assert d["variância"] == pytest.approx(1902.5)
    assert d["moda"] == "sem repetição"


def test_modes_constant_and_zero_mean():
    assert describe(pd.Series([1, 1, 2, 2]))["moda"] == "1.00, 2.00"
    d = describe(pd.Series([0, 0, 0]))
    assert np.isnan(d["CV (%)"])
    assert np.isnan(d["assimetria"])
    flags, meta = detect(pd.Series([0, 0, 0]))
    assert not flags.any().any()
    assert meta["Grubbs situação"] == "n<3 ou constante"


def test_empty_variable_keeps_complete_statistics_contract():
    d = describe(pd.Series([np.nan, np.nan]))
    assert d["n"] == 0
    assert np.isnan(d["média"])
    assert np.isnan(d["CV (%)"])
    assert d["outliers IQR"] == 0


def test_detectors_preserve_source_indices_and_missing_values():
    x = pd.Series([1, 2, 2, 3, 3, 4, 4, 5, 6, 100, np.nan], index=range(20, 31))
    flags, meta = detect(x)
    assert flags.index.equals(x.index)
    assert flags.loc[29, "IQR"]
    assert flags.loc[29, "DBSCAN"]
    assert not flags.loc[30].any()
    assert "não aplicado" in meta["Grubbs situação"]


def test_grubbs_critical_value_matches_nist_example():
    # NIST: n=8, bilateral alpha=.05 yields critical G approximately 2.1266.
    _, meta = detect(pd.Series([1, 2, 3, 4, 5, 6, 7, 8]))
    assert meta["G crítico"] == pytest.approx(2.1266, abs=0.0001)
