from datetime import datetime, timedelta

from src.infrastructure.clock import get_clock


def _format_date(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")


def build_temporal_context() -> str:
    now = get_clock().local_now()
    current_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    previous_month = (current_month - timedelta(days=1)).replace(day=1)
    current_year = current_month.replace(month=1)
    previous_year = current_year.replace(year=current_year.year - 1)
    previous_week_end = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    previous_week_start = previous_week_end - timedelta(days=7)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    formatted_now = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    previous_week_period = (
        f"{_format_date(previous_week_start)} | {_format_date(previous_week_end)}"
    )

    return f"""
### CONTEXTO TEMPORAL
Data e hora atual (fornecida pelo sistema): {formatted_now}
Use esta referência para interpretar "hoje", "ontem", "semana passada",
calcular datas relativas e preencher timestamps nas operações.

### CÁLCULO DE PERÍODOS
Sempre que o usuário mencionar um período, calcule-o usando a tabela abaixo:

| Expressão         | occurred_at_start | occurred_at_end |
|-------------------|-------------------|-----------------|
| "mês passado"     | {_format_date(previous_month)} | {_format_date(current_month)} |
| "esse mês"        | {_format_date(current_month)} | None |
| "semana passada"  | {previous_week_period} |
| "esse ano"        | {_format_date(current_year)} | None |
| "ano passado"     | {_format_date(previous_year)} | {_format_date(current_year)} |
| "este mês"        | {_format_date(current_month)} | {_format_date(next_month)} |
| "até hoje"        | None | {_format_date(tomorrow)} |
| "desde o mês atual" | {_format_date(current_month)} | None |
"""
