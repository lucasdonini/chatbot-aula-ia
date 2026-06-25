# ruff: noqa: E501

# Padrões regex para detecção de Informações Pessoalmente Identificáveis (PII)
# Tuplas de (tipo, padrão_regex) usadas para anonimização de entrada e saída
PII = [
    ("CPF", r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}"),
    ("CNPJ", r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}"),
    ("TELEFONE", r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}"),
    ("EMAIL", r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    ("CONTA", r"\d{4,6}-\d{1}"),
    ("CARTAO", r"\d{4}\s?\d{4}\s?\d{4}\s?\d{4}"),
]
