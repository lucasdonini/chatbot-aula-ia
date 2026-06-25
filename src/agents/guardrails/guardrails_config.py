# ruff: noqa: E501

# Padrões regex para detecção de tentativas de injeção de prompt
INJECTION_PATTERNS = [
    r"ignore\s+(as\s+)?instru[çc][oõ]es",
    r"ignore\s+previous\s+instructions",
    r"forget\s+your\s+instructions",
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if\s+)?",
    r"pretend\s+(you\s+are|to\s+be)",
    r"jailbreak",
    r"dan\s+mode",
    r"modo\s+irrestrito",
    r"system\s*prompt",
    r"<\s*system\s*>",
    r"\[INST\]",
    r"###\s*instruction",
    r"override\s+(your\s+)?instructions",
    r"desconsider[ea]\s+(suas\s+)?instru[çc][oõ]es",
]

# Palavras-chave para detectar tentativas de acesso a dados internos do sistema
INTERN_DATA_KEYWORDS = [
    "prompt do sistema",
    "system prompt",
    "suas instruções",
    "your instructions",
    "variável de ambiente",
    "chave de api",
    "api key",
    "senha do sistema",
    "token de acesso",
    "banco de dados interno",
    "tabela interna",
    "dados de outros clientes",
    "lista de clientes",
    "credenciais",
]

# Mapeamento de categorias bloqueadas para (motivo, mensagem)
BLOCK_RESPONSES = {
    "OFENSIVO": (
        "conteudo_ofensivo",
        "Por favor, mantenha um tom respeitoso para que eu possa te ajudar.",
    ),
    "PERIGOSO": ("pedido_perigoso", "Não posso ajudar com esse tipo de solicitação."),
    "ILICITO": (
        "pedido_ilicito",
        "Não posso auxiliar com atividades ilegais ou irregulares.",
    ),
    "POLITICO": (
        "pergunta_politica",
        "Não me envolvo em temas políticos. Posso ajudar com finanças ou sua agenda.",
    ),
    "INDICACAO_INVEST": (
        "indicacao_investimento",
        "Por regulação, não forneço indicações diretas de ativos. Posso explicar classes de investimento ou agendar uma reunião com seu assessor.",
    ),
}
