from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from .transaction import Category, TransactionType


class TransactionQueryParams(BaseModel):
    source_text: Optional[str] = Field(
        default=None,
        description=(
            "Texto original da mensagem do usuário que gerou o registro. "
            "Inclua apenas quando tiver certeza de qual prompt gerou a transação."
        ),
    )

    occurred_at_start: Optional[date] = Field(
        default=None,
        description=(
            "Data de início do intervalo de datas de ocorrência de transações alvo. "
            "Inclua quando quiser limitar um intervalo de quando a transação ocorreu."
        ),
    )

    occurred_at_end: Optional[date] = Field(
        default=None,
        description=(
            "Data de término do intervalo de datas de ocorrência de transações "
            "alvo (excludente). OBRIGATÓRIO SE o usuário mencionar um período "
            "de ocorrência com fim definido (ex: 'mês passado', 'semana passada', "
            "'em março', 'no ano passado'). Exemplo: para 'mês passado' em "
            "abril/2026, passe 2026-04-01."
        ),
    )

    updated_at_start: Optional[date] = Field(
        default=None,
        description=(
            "Data de início do intervalo de datas de atualizção de transações alvo. "
            "Inclua quando quiser limitar um intervalo de quando o registro "
            "foi atualizado."
        ),
    )

    updated_at_end: Optional[date] = Field(
        default=None,
        description=(
            "Data de término do intervalo de datas de atualização de transações "
            "alvo (excludente). OBRIGATÓRIO SE o usuário mencionar um período de "
            "atualização com fim definido (ex: 'mês passado', 'semana passada', "
            "'em março', 'no ano passado'). Exemplo: para 'mês passado' em "
            "abril/2026, passe 2026-04-01."
        ),
    )

    transaction_type: Optional[TransactionType] = Field(
        default=None,
        description=(
            f"Tipo da transação: {' | '.join(TransactionType)}. "
            "Inclua quando estiver buscando um tipo de transação específico."
        ),
    )

    category: Optional[Category] = Field(
        default=None,
        description=(
            f"Nome da categoria: {' | '.join(Category)}"
            "Inclua quando estiver buscando uma categoria específica."
        ),
    )

    description: Optional[str] = Field(
        default=None,
        description=(
            "Descrição da transação. Pode ser necessário pesquisar várias vezes "
            "pois não é um parâmetro objetivo."
        ),
    )

    limit: Optional[int] = Field(
        default=50,
        description=(
            "Número máximo de transações. None para sem limite. "
            "Para perguntas sobre 'maior' ou 'menor', use None ou um valor alto."
        ),
    )
