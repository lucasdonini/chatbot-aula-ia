"""
=================
Modelagem
---------
Um documento por acesso (sessão = uma conversa completa).
O _id é um UUID gerado internamente — a main.py só conhece o session_id.
O session_id identifica o usuário.

Documento
---------
{
    "_id":           "uuid-gerado-internamente",
    "session_id":    "id_usuario",
    "iniciada_em":   datetime,
    "atualizada_em": datetime,
    "resumo":        "Usuário registrou Pix de R$50...",
    "mensagens":     [
        {"role": "usuario",     "content": "oi"},
        {"role": "assistente", "content": "Olá!"}
    ]
}
"""

from datetime import datetime
from typing import Annotated, List, Literal, Optional

from beanie import Document, Indexed
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["human", "assistant"]
    content: str


class ChatSession(Document):
    """ODM for mongodb collection"""

    session_id: Annotated[str, Indexed(unique=True)]
    started_at: Annotated[datetime, Indexed()]
    updated_at: Optional[datetime] = None
    summary: Optional[str] = None
    messages: List[ChatMessage]

    class Settings:
        name = "sessions"


class ChatSessionSummarized(BaseModel):
    """Beanie projection"""

    session_id: str
    summary: Optional[str]
    started_at: datetime
