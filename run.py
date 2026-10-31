"""Ponto de entrada local: usa exclusivamente o ambiente virtual do projeto."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if sys.prefix == sys.base_prefix:
    if not VENV.exists():
        raise SystemExit("Crie o ambiente: python -m venv .venv; consulte README.md.")
    os.execv(str(VENV), [str(VENV), str(Path(__file__).resolve()), *sys.argv[1:]])

sys.path.insert(0, str(ROOT / "src"))
from nba_lab import create_app  # noqa: E402

if __name__ == "__main__":
    from waitress import serve

    print("Relatório disponível em http://127.0.0.1:5000", flush=True)
    serve(create_app(), host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")))
