# Contexto do Projeto: Assessor.IA

## 1. Visão Geral
Este projeto contém um sistema de assistente multiagencial com acesso via CLI. A migração gradual para uma API REST com FastAPI está planejada em `MIGRATION_API.md`; a Fase 0.1 foi concluída. O objetivo principal do assistente é ajudar na organização, tanto financeira como do dia a dia (tarefas, compromissos, etc.).
Este projeto é o principal objeto de estudo das aulas de IA do meu curso de desenvolvimento de sistema, usado para introduzir tecnicas e ferramentas na prática ao invés de só na teoria. Cada aluno tem seu projeto, assim como o professor. Este é o meu, mas ele está versionado num repositório público no GitHub para que meus colegas tenham acesso.
Outros colegas que acessam o repositório não necessariamente têm conhecimento sobre todas as funcionalidades extra que eu adicionei, além da arquitetura e stack que está diferente do que o professor usa em aula.


## 2.1. Stack Tecnológica (deste projeto)
- **Sistema Multiagentes:** LangGraph
- **Banco de Dados:**
    - PostgreSQL: Dados do usuário (Transações registradas, compromissos, etc.)
    - MongoDB: Dados de sessão (Mensagens, resumo da sessão, etc.)
- **Migrations:** Alembic
- **Acesso a Dados:**
    - PostgreSQL: SQLAchemy 2.0
    - MongoDB: Beanie
- **Infraestrutura:** Docker, Docker Compose, Make e UV

## 2.2. Stack Tecnológica (do professor)
- **Sistema Multiagentes:** LangGraph
- **Banco de Dados:**
    - PostgreSQL: Dados do usuário (Transações registradas, compromissos, etc.)
    - MongoDB: Dados de sessão (Mensagens, resumo da sessão, etc.)
- **Migrations:** Inicialização manual via script SQL
- **Acesso a Dados:**
    - PostgreSQL: Psycopg 2
    - MongoDB: PyMongo
- **Infraestrutura:** Pip


## 3.1. Arquitetura e Organização de Pastas (deste projeto)
O projeto segue os princípios de Arquitetura em Camadas e Domain-Driven Design (DDD).
Estou aprendendo ainda, então a rigorosidade da arquitetura está em aprimoramento:
- `/src`: Código fonte da aplicação
    - `/model`: Entidades (não todas puras, alguns ORMs) e regras de negócio.
    - `/services`: Utilização direta ou indireta via repository a ferramentas externas; lógica de negócio complexa
    - `/infrastructure`: Implementações técnicas como repositories, alguns ORMs, loggers personalizados, variáveis de ambiente, etc.
    - `/agents`: Grafo, agentes e tools do sistema e seus prompts
- `/migrations`: Migrações Alembic autogeradas e configurações.
- `/data`: Assets estáticos da applicação, como PDFs
- `/sql`: Scripts SQL de configuração do banco local
- `/logs`: Logs de execução do app
- `/tests`: Testes unitários (173) e de integração (62)

## 3.2. Arquitetura e Organização de Pastas (do professor)
Projeto praticamente monolítico, contendo apenas arquivos soltos na raiz dividos por funcionalidade no nível mais macro possível, como `main.py` para o grafo, agentes e interação com usuário; `pg_tools.py` com conexão e interação com banco PostgreSQL e tools de agentes; `faq_tools.py` para tools do agente leitor de FAQ contendo toda a lógica desde a criação da tool até os embeddings; e assim por diante.


## 4. Comandos Frequentes (Para uso do Agente)
Podem ser consultadas no `makefile`, mas para contexto:
- Gerir dependências: `uv [add|remove|sync]`
- Rodar o linter: `ruff check [--fix]; ruff format`
- Gerar migrações: `alembic revision --autogenerate -m "mensagem"`
- Rodar testes unitários: `pytest`
- Rodar testes de integração: `pytest -m integration`
- Rodar todos os testes: `pytest && pytest -m integration`
- Workflow CI: `.github/workflows/ci.yml` — roda em PRs para `main` e pushes para `dev`

## 5. Estado Atual

### Problemas por implementação errada (ainda pendentes)
1. **Paradigmas de Arquitetura mal aplicados:** Por estar aprendendo, muitas vezes eu não consigo organizar o código da forma correta, e com o tempo esses erros começam a ficar perceptíveis.
2. **Falta de padronização de logs e comentários:** Comentários excessivos em certos lugares, faltantes em outros. Logs foram reorganizados recentemente, mas podem precisar de mais ajustes.

### Problemas resolvidos
1. ~~**Falta de testes:**~~ Agora existem **235 testes** (173 unitários + 62 de integração). Testes unitários rodam sem Docker; testes de integração sobem PostgreSQL via testcontainers. CI no GitHub Actions executa ambos em jobs paralelos.
2. ~~**Chamadas síncronas a LLMs:**~~ Guardrails e serviços de sumarização agora usam `ainvoke` (assíncrono), eliminando bloqueios e permitindo mocks via `AsyncMock`.
3. ~~**Vazamento de PII em logs:**~~ Output guardrail só loga o texto após sanitização. Input guardrail recebe texto anônimo.
4. ~~**Configuração permissiva e ambiente compartilhado:**~~ A aplicação agora lê `.env.app` com `extra="forbid"`; o Compose lê `.env.compose`. Os exemplos versionados são `.env.app.example` e `.env.compose.example`.

### Migração para API
- O plano operacional está em `MIGRATION_API.md`.
- Fase 0.1 concluída: novos settings de logging/timezone, validação explícita das chaves LLM no boot da CLI e separação entre configuração da aplicação e do Compose.
- Fase 0.2 concluída: o histórico usado pelo router respeita o limite solicitado e retorna sessões por atualização mais recente.
- Fase 0.3 concluída: o input guardrail bloqueia falhas, formatos inválidos e categorias desconhecidas do classificador LLM.
- Fase 0.4 concluída: README e Makefile usam o fluxo `uv`, os ambientes da aplicação e do Compose são separados e a URL PostgreSQL local usa a porta publicada correta.
- Fase 0.5 concluída: logs usam settings, arquivo opcional, saída de console no estilo da API e `ContextVar` para isolar sessão, trace e interação entre tasks.
- Fase 0.6 concluída: Clock centralizado fornece UTC para persistência e timezone local para contexto temporal; prompts recebem contexto atualizado a cada execução.
- Para executar localmente, preencher `GEMINI_API_KEY` e `GROQ_API_KEY` em `.env.app`. Credenciais nunca devem ser versionadas.
- Próximo passo: Fase 0.7, refatorações menores.

## 6. Funcionalidades Implementadas Recentemente

### Logging
- Logs multi-linha permitidos (removido `InlineMessageFormatter`)
- Prefixo `[INT N]` para correlacionar logs de uma mesma interação do usuário
- Bloco visual `─── NODE ─── Input / Output` para cada agente no grafo
- Logs rotineiros de tools e services rebaixados para `debug` (menos ruído)
- Filtro `HideConsoleTracebackFilter` para não expor tracebacks no console
- MongoDB `saslStart`/`saslContinue` silenciados

### CI/CD
- Workflow GitHub Actions com dois jobs paralelos: `lint-and-unit` e `integration`
- Lint com Ruff, testes unitários sem dependências externas
- Testes de integração sobem PostgreSQL via testcontainers (Docker built-in no runner)
- `.env.example` copiado para `.env` durante o CI

### Isolamento de Testes
- Testes de integração marcados com `@pytest.mark.integration`
- `apply_migrations` não é mais `autouse` — apenas testes que explicitamente usam a fixture disparam o container
- `pytest` padrão roda só unitários; `pytest -m integration` roda os de integração

### Router
- Filtro de `tool_calls` de outros agentes para evitar que o router tente chamar tools que não possui

### Async LLM
- Guardrails (`input_guardrail.py`, `output_guardrail.py`) convertidos de `invoke` para `ainvoke`
- `SessionSummaryService.sumarize` convertido para `async def`

## 7. Próximos Passos
- Add transaction category 'SALARY'
- Pass errors during the session to the summary agent so the session history understands some operations went wrong
- Fix layer separation
- Improve type safety
