from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data"
SRC = ROOT / "app"
FRONTEND = ROOT / "frontend" / "dist"

FAQ_PDF = DATA_DIR / "faq" / "FAQ_assessor_v1.1.pdf"
