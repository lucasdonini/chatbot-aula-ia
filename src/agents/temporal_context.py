from datetime import datetime, timezone

_now = datetime.now(timezone.utc).astimezone()
_formatted_datetime = _now.strftime("%A, %d de %B de %Y — %H:%M:%S %Z")

TEMPORAL_CONTEXT = f"""
### CONTEXTO TEMPORAL
Data e hora atual (fornecida pelo sistema): {_formatted_datetime}
Use esta referência para interpretar "hoje", "ontem", "semana passada",
calcular datas relativas e preencher timestamps nas operações.

### CÁLCULO DE PERÍODOS
Sempre que o usuário mencionar um período, calcule o período usando a tabela abaixo como base:

Suponto que hoje é 2026-04-04:
| Expressão         | occurred_at_start | occurred_at_end |
|-------------------|-------------------|-----------------|
| "mês passado"     | 2026-03-01 | 2026-04-01 |
| "esse mês"        | 2026-04-01 | None |
| "semana passada"  | 2026-03-22 | 2026-03-29 |
| "esse ano"        | 2026-01-01 | None |
| "ano passado"     | 2025-01-01 | 2026-01-01 |
| "em março"        | 2026-03-01 | 2026-04-01 |
| "até hoje"        | None | amanhã |
| "desde fevereiro" | 2026-02-01 | None |
"""
