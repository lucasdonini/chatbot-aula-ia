# Plano de Migração: CLI → API

> Documento operacional. Feito para que outros agentes (e o mantenedor) executem
> a migração **em etapas independentes**, cada uma com critérios de aceite e
> comandos de verificação. Leia também o `AGENTS.md` (regras de engajamento) e o
> `TODO.md` (dívida auditada) antes de começar.
>
> Status: **em andamento** — Fase 0.2 concluída em 2026-08-12.

---

## 1. Contexto

O projeto hoje é um chatbot multiagente (LangGraph) executado via **CLI**
(`src/main.py`). A meta é expô-lo como **API REST (FastAPI)** para alimentar uma
interface de chat com: chat atual, lista de chats anteriores (com título) e
mensagens de um chat específico.

Pontos de partida verificados:

- `src/main.py` — loop de CLI; concentra `setup_logger`, sessão e finalização.
- `src/agents/graph.py` — grafo compilado com `MemorySaver` (thread_id = session_id).
- `src/services/chat_session_service.py` — persistência das sessões no MongoDB (Beanie).
- `src/services/chat_history_service.py` — leitura de histórico (contém bugs, ver Fase 0.2).
- MongoDB guarda mensagens (`ChatSession.entries`); PostgreSQL guarda transações.

## 2. Decisões registradas (não reabrir sem forte motivo)

| Tema | Decisão | Motivo |
|---|---|---|
| Framework | **FastAPI** | Async nativo (LangGraph), schemas Pydantic já em uso, docs automáticas |
| Escopo inicial | **Chat + histórico** | `POST /chat`, `GET /sessions`, `GET /sessions/{id}/messages` |
| Streaming | **Não** (resposta completa) | Menor complexidade nesta etapa |
| Persistência de sessão | **MemorySaver in-memory** + fixes | Sem dependência nova; ideal p/ dev/aula. Upgrade p/ `AsyncPostgresSaver` documentado p/ depois |
| Concorrência | **`asyncio.Lock` por `session_id`** + `contextvars` p/ logs | `MemorySaver` sobrescreve checkpoint em turnos concorrentes da mesma sessão; globals de log cruzam requests |
| Estado de sessão na API | **Fim do `_active_sessions`**; lookup por `session_id` direto no Mongo | Dict em memória não sobrevive a restart e vaza memória |
| Títulos de chat | Gerados na **1ª mensagem** via `fast_llm` (campo novo `title` no `ChatSession`) | UI precisa de título curto |
| Resumos | **Manter como memória do router** (`search_history`), gerados **continuamente** (não só no fechamento) | Sem resumo, a memória entre chats morre |
| Fuso horário | `Clock` provider + setting `APP_TIMEZONE` (default `America/Sao_Paulo`) | `temporal_context` hoje depende do timezone do servidor |
| Loggers | ENVVAR `LOG_LEVEL`/`LOG_TO_FILE`/`LOG_FILE`; terminal estilo FastAPI; arquivo com formato atual | Ver Fase 0.5 |
| Dívida técnica neste round | Somente Fase 3 priorizada | Restante fica documentado no TODO.md |

### Persistência — por que não as outras opções (registro para o futuro)

- **AsyncPostgresSaver**: sobrevive a restart e multi-worker, mas exige dependência
  nova + tabelas + migração agora. Caminho de upgrade quando subir com `--workers > 1`.
- **Stateless via Mongo**: sem checkpointer, grafo reconstruído por request. Mais
  rework em `graph.py` (semântica de `RemoveMessage` e dedup de tool-calls muda).
  Não recomendado neste round.

## 3. Convenções e comandos de verificação

- Lint/format: `uv run ruff check .` e `uv run ruff format .` (Ruff conf no `pyproject.toml`).
- Type check: `uv run mypy .` (exclui `tests/` e `migrations/`).
- Testes unitários: `uv run pytest` (default roda `-m 'not integration'`).
- Testes de integração: `uv run pytest -m integration` (sobe PostgreSQL via testcontainers).
- Rodar API em dev: `uv run uvicorn src.api.app:app --reload`.
- Padrões do projeto: type hints estritos, logs em PT-BR via `extra={"details": {...}}`,
  injeção de dependência por construtor, separação `model`/`service`/`infrastructure`/`agents`.
- **Não** gerar código sem pedido explícito (ver `AGENTS.md`). Em dúvida, perguntar.

## 4. Visão geral das fases

| Fase | Conteúdo | Dependente de |
|---|---|---|
| 0 | Pré-migração (settings, bugs, guardrails, env) | — |
| 0.5 | Refatoração dos loggers (terminal estilo FastAPI) | Fase 0 (settings) |
| 0.6 | Clock centralizado | Fase 0 (settings) |
| 1 | Núcleo da API (`src/api/`, `POST /chat`) | 0, 0.5, 0.6 |
| 2 | Endpoints de histórico (UI) | Fase 1 |
| 3 | Dívida técnica priorizada | Fase 0 (opcional, pode paralelizar) |
| 4 | Testes de API + CI | Fase 1 e 2 |
| 5 | Documentação (README, context.md, TODO.md) | todas |

Cada fase termina com: `ruff check .` limpo, testes verdes e critérios de aceite da fase atendidos.

---

## Fase 0 — Correções pré-migração

### 0.1 `src/infrastructure/settings.py`

**Implementado (2026-08-12):**

- `Settings` agora lê exclusivamente `.env.app`, rejeita variáveis desconhecidas e
  expõe `log_level`, `log_to_file`, `log_file` e `app_timezone`.
- `validate_llm_api_keys()` é chamado no boot da CLI e deve ser reutilizado no
  lifespan da futura API. A validação não ocorre no import para não bloquear
  migrations, testes de domínio e comandos administrativos.
- O ambiente foi separado: `.env.app` é da aplicação e `.env.compose` é do
  PostgreSQL no Docker Compose. Os modelos versionados são
  `.env.app.example` e `.env.compose.example`.
- Credenciais não foram migradas automaticamente. Configure `GEMINI_API_KEY` e
  `GROQ_API_KEY` em `.env.app` por canal seguro antes de iniciar a aplicação.

- Adicionar campos:
  - `log_level` (default `"INFO"`, validado p/ `INFO`/`DEBUG`).
  - `log_to_file` (bool, default `False`).
  - `log_file` (default `"logs/app.log"`).
  - `app_timezone` (default `"America/Sao_Paulo"`).
- Validar no boot que `gemini_api_key` e `groq_api_key` **não** são o valor dummy
  (`"No key provided"`) — falha clara e cedo em vez de erro enigmático em runtime.
- Trocar `model_config.extra` de `"ignore"` para `"forbid"` (typos em env param a falhar).
- **Arquivos tocados:** `src/infrastructure/settings.py`, `.env`, `.env.example`.
- **Aceite:** `uv run python -c "from src.infrastructure.settings import settings; print(settings.log_level)"`
  respeita o `.env`; env desconhecida levanta `ValidationError`.

### 0.2 Bug `src/services/chat_history_service.py::fetch_history`

**Implementado (2026-08-12):**

- A query agora ordena por `updated_at` em ordem decrescente e aplica o `limit`
  recebido antes de materializar os resultados.
- Os testes unitários cobrem a direção da ordenação e o limite padrão usado pelo
  `SearchHistoryTool`.

Hoje `limit` é **ignorado** (`.to_list()` sem `.limit(limit)`) e a ordenação é
**ascendente** por `started_at` (contradiz "most recent first" da docstring).
Consequência: `search_history` (router) puxa todo o histórico.

- Aplicar `.limit(limit)` na query.
- Ordenar `desc` por `updated_at` (mais recentes primeiro).
- **Arquivos tocados:** `chat_history_service.py` + testes afetados.
- **Aceite:** teste unitário provando `limit` aplicado e ordem descendente.

### 0.3 Guardrails fail-closed

`src/agents/guardrails/input_guardrail.py` define `category = "APROVADO"` por default:
classificação desconhecida/vazia é aprovada, e exceção do LLM propaga sem bloqueio.

- Categoria desconhecida ou ausente → `GuardrailResult.block(...)`.
- Exceção do `fast_llm.ainvoke` → bloquear (fail-closed) e logar; **não** deixar propagar.
- **Arquivos tocados:** `input_guardrail.py`, `guardrails_prompts.py` (ajuste de instrução se preciso).
- **Aceite:** mock de LLM devolvendo `"sem categoria"` resulta em bloqueio.

### 0.4 Configuração e ambiente

- `.env` precisa definir `POSTGRES_URL` correto (hoje ausente → usa default
  `postgres:postgres@localhost:5432`, mas o container expõe `5433` com senha
  `germinare`). `make build-db` + `make run` hoje **não conecta**.
- `.env.example`: corrigir/remover `LANGGRAPH_ALLOWED_MSGPACK_MODULES` (config morta:
  `graph.py:70` hardcoda `src.model.graph_state`); adicionar `LOG_LEVEL`, `LOG_TO_FILE`,
  `LOG_FILE`, `APP_TIMEZONE`.
- `.gitignore`: adicionar `**/.env`.
- README/makefile: `make build` não existe (target é `build-db`); banco é
  `assessoriadb` (README escreve `acessoriadb`).
- **Aceite:** `make build-db && make upgrade-db && make run` conecta sem erro.

### 0.5 Loggers (terminal estilo FastAPI) — `src/infrastructure/logger.py`

Comportamento alvo:

- **Nível:** root level = `settings.log_level` (remover `DEBUG` hardcoded de `setup_logger`).
- **Arquivo (`.log`):** habilitado **somente** se `settings.log_to_file`. Manter o
  formato atual (`StructuredFormatter`: data · nível · agente · session · int · trace ·
  details JSON · traceback).
- **Terminal:** novo formatter estilo uvicorn, prefixo colorido `{LEVEL}:` (ANSI):
  - `INFO+`: `INFO: mensagem` puro — sem details, sem módulo, sem data/sessão.
    Intercala naturalmente com os requests do uvicorn.
  - `DEBUG`: `[nome_reduzido] INFO: mensagem | {details_json}` — reusar
    `_short_module_name` (remove `src.`, `_agent/_service/_repository`, etc.).
  - **Traceback: nunca suprimir** no console (remover `HideConsoleTracebackFilter`).
- `ContextFilter` continua preenchendo `agent/session/trace/interaction`.
- Não silenciar `uvicorn`, `uvicorn.error`, `uvicorn.access`.
- Substituir globals `_current_session_id`/`_current_trace_id`/`_INTERACTION_COUNTER`
  por **`contextvars.ContextVar`** (ver Fase 0.5.1).
- **Arquivos tocados:** `logger.py`, `settings.py` (já na 0.1), `.env`/`.env.example`.
- **Aceite:** `LOG_LEVEL=DEBUG uv run ...` mostra módulo reduzido + details; `INFO`
  mostra só `LEVEL: mensagem`; `LOG_TO_FILE=false` não cria `logs/`; exceção exibe
  stack no terminal.

#### 0.5.1 contextvars (correlação de logs em concorrência)

Os três globals viram `ContextVar`. O `ContextFilter` lê as contextvars. A Fase 1
seta os valores por request (middleware/dependency). Sem isso, requests concorrentes
cruzam `session/trace/int`.

### 0.6 Clock centralizado — novo `src/infrastructure/clock.py`

Analogia ao `Clock` do Spring Boot: um provider único de "agora".

- **`Clock` (protocol)**: `now() -> datetime` (UTC tz-aware, persistência),
  `local_now() -> datetime` (`settings.app_timezone`), `today() -> date` (data local).
- **`SystemClock`**: implementação default.
- **`FixedClock(fixed)`: para testes determinísticos.**
- **Provider singleton:** `get_clock()` / `set_clock()` (padrão do `settings`/`get_db`).
- Aplicar:
  - `chat_session_service.py:28,52,104` — `datetime.now()` naive → `clock.now()`
    (Mongo passa a gravar tz-aware; corrige TODO "ChatMessage sem timezone").
  - `temporal_context.py:5` — `_now = datetime.now(timezone.utc).astimezone()` →
    função `build_temporal_context()` usando `clock.local_now()` (corrige fuso do
    servidor e a data congelada no import — crítico p/ API de longa duração).
- `occurred_at`/`updated_at` de transações seguem com `func.now()` do banco (intencional).
- **Arquivos tocados:** `clock.py` (novo), `chat_session_service.py`,
  `temporal_context.py`, quem consumir `build_temporal_context` (nós do grafo).
- **Aceite:** teste com `FixedClock` fixa `started_at`/`updated_at`/contexto temporal.

### 0.7 Pacote de código fonte — `src/ -> app/`

Renomear o pacote `src/` para `app/` com cuidado para manter a coerência de nomes 
e imports em todo o projeto.

### ✅ Fase 0 — Definição de pronto

`uv run ruff check .` limpo; `uv run pytest` verde; `make build-db && make upgrade-db`
ok; `.env`/`.env.example` consistentes; bug do `limit` coberto por teste.

---

## Fase 1 — Núcleo da API (novo pacote `src/api/`)

### 1.1 `src/api/app.py` — aplicação e lifespan

- Criar `FastAPI` com `lifespan`:
  - Startup: `setup_logger()`, `MongoManager.init_database()` (com `asyncio.Lock`
    contra dupla inicialização), validação de chaves de API.
  - Shutdown: fechar `AsyncMongoClient` (adicionar método de close no `MongoManager`).
- Título/descrição da API; sem dependência do `src.main` CLI.

### 1.2 `POST /chat` — `src/api/routers/chat.py`

Request: `{session_id?: str, message: str}`. Fluxo:

1. Normalizar `session_id` (criar `uuid4` se ausente; responder com ele).
2. **Título na 1ª mensagem:** se o `ChatSession` ainda não tem `title`, gerar via
   `fast_llm` (curto, < 60 chars) e salvar.
3. Adquirir `asyncio.Lock` por `session_id` (serializa turnos do mesmo chat).
4. Salvar mensagem do usuário (Mongo), executar `execute_agent_flux(...)`, salvar
   resposta (Mongo).
5. Retornar `{session_id, title, response, trace_id}`.

Response model Pydantic em `src/api/schemas.py`.

### 1.3 Refatorar `ChatSessionService`

- **Remover `_active_sessions`:** `_save_entry`/`finalize_session` passam a localizar
  o documento por `ChatSession.session_id` (não pelo dict).
- **TTL/expurgo:** sessões inativas (configurável, ex.: > 1h) deixam de participar
  do fluxo ativo; decisão de limite a confirmar com o mantenedor.
- **Resumo contínuo:** em vez de só no fechamento, gerar `summary` a cada N mensagens
  (ex.: 10) ou após inatividade — mantém o `search_history` do router útil.
- Criar método de reabertura: `get_or_create_session(session_id)`.

### 1.4 Erros e segurança

- Exceções não tratadas → `500` genérico + log interno com traceback + registro via
  `save_error` (comportamento atual do `main.py`).
- **Nunca** devolver `str(e)`/stack ao usuário. Corrigir já nesta fase
  `search_history.py:61` (`f"Erro ao buscar as mensagens: {str(e)}"`).

### ✅ Fase 1 — Definição de pronto

`uv run uvicorn src.api.app:app --reload` sobe; `POST /chat` cria sessão, persiste
mensagens, responde; dois `POST /chat` na mesma sessão preservam contexto;
dois requests em sessões diferentes não se interferem (logs com `session/trace`
corretos via contextvars).

---

## Fase 2 — Histórico (UI)

### 2.1 `GET /sessions`

- Lista de chats com `title`, `updated_at`, prévia da última mensagem.
- Novo método em `ChatHistoryService` (ex.: `list_sessions(limit)`), sem vazar PII crua
  (previews curtas/truncadas).
- Ordenação `desc` por `updated_at`.

### 2.2 `GET /sessions/{id}/messages`

- Mensagens na ordem de ocorrência (reusa `fetch_entries` já corrigido na 0.2).
- Retorna entradas mapeadas p/ um schema simples `{role, content, type, created_at?}`.

### 2.3 `search_history` do router

- Confirmar que continua consumindo `summary` (resumos contínuos da Fase 1).

### ✅ Fase 2 — Definição de pronto

Os 3 endpoints atendem a UI de chat (lista, mensagens, conversa em andamento);
`GET /sessions` respeita limite e ordem; testes de rota com `TestClient`.

---

## Fase 3 — Dívida técnica priorizada

- **Typos:** `input_aproved`/`output_aproved` (`guardrail_result.py` + testes),
  `stricktly assyncronal` (`search_history.py:40`), `Unknow error ocurred`
  (`main.py:33`), `Espected` (`update_transaction_params.py:88`).
- **`GuardrailResult`:** remover campo morto `_allow_direct` e o `model_validator`
  que bloqueia instanciação direta (hack desnecessário).
- **`anonymize_input`** (`anonymization.py`): anonimizar **todas** as ocorrências do
  mesmo valor (hoje `replace(value, token, 1)` deixa a 2ª crua); word boundaries nos
  padrões de `anonymization_config.py` (ex.: `CONTA` casa dentro de CPF/telefone).
- **FAQ → output guardrail:** em `graph.py:66` `FAQ_NODE_NAME` vai direto a `END`;
  rotear p/ `OUTPUT_GUARDRAIL` e de-anonimizar a resposta (hoje tokens `[PII_*]`
  vazam na resposta do FAQ).
- **`.gitignore`:** `**/.env` (já na 0.4; confirmar).
- **`faq_store.py`:** cache do índice FAISS em memória (evitar `FAISS.load_local`
  por chamada); documentar o `allow_dangerous_deserialization=True`.
- **Fora do escopo (deixar no TODO.md):** `Decimal`, auto-imports dinâmicos,
  `create_react_agent`, `String(32)`, enum migrations manuais, engine module-level,
  singleton do Mongo, etc.

---

## Fase 4 — Testes e CI

- Testes de API com `TestClient` (FastAPI) mockando LLM (`fast_llm`, `specialist_llm`)
  e MongoDB (Beanie). Cobrir: criação de sessão, título na 1ª msg, lock por sessão,
  erro genérico, endpoints de histórico.
- Atualizar testes que usam `input_aproved`/`output_aproved` junto da correção (Fase 3).
- Atualizar testes afetados pelo `FixedClock` (Fase 0.6).
- CI (`.github/workflows/ci.yml`): incluir os novos testes de API no job unit
  (ou job próprio); manter ruff/mypy/integration.
- Corrigir testes acoplados a internals (`stmt._limit`, `_order_by_clauses`,
  `__new__` + `object.__setattr__`) **somente se** o refactor das Fases 1–2 exigir.

---

## Fase 5 — Documentação

- **README.md:** seção de API (rodar com `uvicorn src.api.app:app`, exemplos curl
  dos 3 endpoints), CLI vira legado, correções de `make`/nome do banco (0.4).
- **context.md:** "acesso via CLI" → CLI + API; atualizar "Estado Atual" e
  "Próximos Passos"; typos (`sumarize`).
- **TODO.md:**
  - Marcar como resolvidos: UpdateTransactionTool registrada, type hint de
    `get_active_sessions`, `os.system("cls")`/console_utils, `logger.exception` em
    `search_history`, IndexError do `output_guardrail`, monkey-patch de `ainvoke`,
    `sumarize` renomeado, "ChatMessage sem timezone" (via Clock).
  - Adicionar achados novos: `fetch_history` ignora limit, `temporal_context` stale
    no import, globals de logger → contextvars, `main()` não importável, config morta
    (`LOG_LEVEL`/`LOG_TO_FILE`/`LANGGRAPH_ALLOWED_MSGPACK_MODULES`), `POSTGRES_URL`
    ausente, tokens PII no FAQ, `str(e)` vazado ao usuário, `.gitignore` sem `**/.env`.
  - Nova seção "Migração API" apontando para este documento.

---

## Referências rápidas (arquivos-chave)

| Arquivo | Papel na migração |
|---|---|
| `src/main.py` | CLI a ser aposentado; contém `setup_logger`/sessão hoje |
| `src/agents/graph.py` | Grafo + `MemorySaver` (thread_id = session_id); FAQ→END (Fase 3) |
| `src/agents/temporal_context.py` | `_now` no import (Fase 0.6) |
| `src/services/chat_session_service.py` | Sessões/Mongo; `_active_sessions` (Fase 1) |
| `src/services/chat_history_service.py` | Bug do `limit` (Fase 0.2); endpoints (Fase 2) |
| `src/infrastructure/logger.py` | Refatoração console/arquivo + contextvars (Fase 0.5) |
| `src/infrastructure/settings.py` | Novos campos env (Fase 0.1) |
| `src/infrastructure/mongo_connection.py` | `init_database` + close no shutdown (Fase 1) |
| `src/agents/guardrails/input_guardrail.py` | Fail-closed (Fase 0.3) |
| `src/api/` | Novo pacote da API (Fases 1–2) |
| `.env` / `.env.example` | Correção de config (Fase 0.4) |
| `TODO.md` | Dívida auditada; atualizar ao longo da migração (Fase 5) |
