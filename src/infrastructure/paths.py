from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA_DIR = ROOT / "data"
FAISS_DIR = ROOT / ".faiss"

FAQ_PDF = DATA_DIR / "faq" / "FAQ_assessor_v1.1.pdf"
FAQ_INDEX = FAISS_DIR / "faq_index"
