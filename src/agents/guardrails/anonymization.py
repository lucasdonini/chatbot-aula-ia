import logging
import re
from typing import Tuple
from uuid import uuid4

from .anonymization_config import PII

logger = logging.getLogger(__name__)


def anonymize_input(text: str) -> Tuple[str, dict]:
    logger.info(
        "Anonymizing input",
        extra={"details": {"input_len": len(text)}},
    )
    pii_map = {}

    for type, pattern in PII:
        matches = re.findall(pattern, text)
        for value in matches:
            token = f"[PII_{type}_{uuid4().hex[:6]}]"
            pii_map[token] = value
            text = text.replace(value, token, 1)

    logger.info(
        "Input anonymized",
        extra={"details": {"pii_count": len(pii_map)}},
    )
    return text, pii_map


__all__ = ["anonymize_input", "deanonymize_output"]


def deanonymize_output(text: str, pii_map: dict, restore: bool = False) -> str:
    """Resolve PII tokens from output.
    By default, ommits: does not repeat personal data."""
    logger.info(
        "Deanonymizing output",
        extra={"details": {"pii_tokens": len(pii_map)}},
    )
    for token, value in pii_map.items():
        if token in text:
            replacement = value if restore else f"[{token.split('_')[1]} OMITIDO]"
            text = text.replace(token, replacement)
    return text
