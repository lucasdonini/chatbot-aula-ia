from typing import Tuple
from uuid import uuid4
import re

# Default PII both for input and output
PII = [
    ("CPF", r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}"),
    ("CNPJ", r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}"),
    ("TELEFONE", r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}"),
    ("EMAIL", r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    ("CONTA", r"\d{4,6}-\d{1}"),
    ("CARTAO", r"\d{4}\s?\d{4}\s?\d{4}\s?\d{4}"),
]


def anonymize_input(text: str) -> Tuple[str, dict]:
    pii_map = {}

    for type, pattern in PII:
        matches = re.findall(pattern, text)
        for value in matches:
            token = f"[PII_{type}_{uuid4().hex[:6]}]"
            pii_map[token] = value
            text = text.replace(value, token, 1)

    return text, pii_map


def deanonymize_output(text: str, pii_map: dict, restore: bool = False) -> str:
    """Resolve PII tokens from output. By default, ommits: does not repeat personal data."""
    for token, value in pii_map.items():
        if token in text:
            replacement = value if restore else f"[{token.split('_')[1]} OMITIDO]"
            text = text.replace(token, replacement)
    return text
