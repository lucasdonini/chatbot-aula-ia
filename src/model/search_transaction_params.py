from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class SearchTransactionParams(BaseModel):
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
            "Data de início do intervalo de datas de transações alvo. "
            "Inclua quando quiser limitar um intervalo de datas."
        ),
    )

    occurred_at_end: Optional[date] = Field(
        default=None,
        description=(
            "Data de término do intervalo (excludente). "
            "OBRIGATÓRIO SE o usuário mencionar um período com fim definido "
            "(ex: 'mês passado', 'semana passada', 'em março', 'no ano passado'). "
            "Exemplo: para 'mês passado' em abril/2026, passe 2026-04-01."
        ),
    )

    transaction_type: Optional[str] = Field(
        default=None,
        description=(
            "Nome do tipo: INCOME | EXPENSES | TRANSFER. "
            "Inclua quando estiver buscando um tipo de transação específico."
        ),
    )

    category: Optional[str] = Field(
        default=None,
        description=(
            "Nome da categoria: comida | besteira | estudo | "
            "férias | transporte | moradia | saúde | lazer | "
            "contas | investimento | presente | outros. Inclua "
            "quando estiver buscando uma categoria específica."
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
            "Número máximo de transações. Use 0 para sem limite. "
            "Para perguntas sobre 'maior' ou 'menor', use 0 ou um valor alto."
        ),
    )
