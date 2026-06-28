# TODO — Melhorias do Projeto

> Auditoria realizada em 2026-06-28 cobrindo segurança, bugs, arquitetura,
> qualidade de código, testes e configuração.

---

## 🔴 Segurança

- [ ] **Fail-open nos guardrails**: Se o LLM classificador (`input_guardrail`) ou de compliance (`output_guardrail`) estiver indisponível, a mensagem é aprovada por default — deveria ser fail-closed (bloquear e registrar).
- [ ] **FAQ bypassa output guardrail**: O nó FAQ vai direto para `END` sem passar pelo `output_guardrail` nem pelo `orquestrator` — respostas do FAQ não passam por sanitização de PII nem revisão de compliance.
- [ ] **ReDoS via regex**: `chat_history_service.py` usa `re.compile(search, re.IGNORECASE)` com input do usuário sem qualquer sanitização ou limite de complexidade.
- [ ] **FAISS `allow_dangerous_deserialization=True`**: `faiss_store.py` permite execução de código arbitrário se o índice `.faiss/` for adulterado por alguém com acesso ao filesystem.
- [ ] **PII vazando em logs**: `ChatSessionService`, `MongoManager` (listener de queries) e `TransactionRepository` logam dados sensíveis (mensagens, parâmetros de busca) **antes** dos guardrails sanitizarem.
- [ ] **Log level DEBUG por default**: `logger.py` configura `DEBUG` como padrão — grava tudo, incluindo PII. Deveria ser `INFO` com configuração runtime via variável de ambiente.
- [ ] **Regex de PII incompletos**: Faltam RG, passaporte, IP, CEP, endereços. Padrão `CONTA` (`\d{4,6}-\d{1}`) é muito genérico e gera falsos positivos.
- [ ] **`.env.example` com path inválido**: `LANGGRAPH_ALLOWED_MSGPACK_MODULES` referencia `src.model.common.graph_state` — o módulo real é `src.model.graph_state`.
- [ ] **`INTERN_DATA_KEYWORDS` incompleta**: Falta "credentials" (inglês), "connection string", "environment variable", ".env", "database password".
- [ ] **Colisão de tokens de anonimização**: `uuid4().hex[:6]` em `anonymization.py` — 1 em ~16M de colisão. Remota mas possível.

---

## 🐛 Bugs

- [ ] **`limit=0` em `TransactionQueryParams`**: Documentado como "sem limite" mas o repositório retorna lista vazia quando `limit <= 0`.
- [ ] **`UpdateTransactionTool` não registrada**: Instanciada em `financial_agent.py` mas não incluída na lista `TOOLS` — o LLM nunca consegue usá-la.
- [ ] **Fuso horário errado em `temporal_context.py`**: `datetime.now(timezone.utc).astimezone()` depende do timezone do servidor (geralmente UTC em containers), não de `America/Sao_Paulo`.
- [ ] **Datas fixas hardcoded em `temporal_context.py`**: Tabela de períodos usa 2026-04-04 fixo — o código quebrará conceitualmente em 2027+.
- [ ] **`os.system("cls")` em `main.py`**: Só funciona no Windows. Linux/Mac precisam de `clear`.
- [ ] **Typos no código**:
  - `GuardrailResult.input_aproved` / `output_aproved` → `approved`
  - `search_history.py`: `"stricktly assyncronal"` → `"strictly asynchronous"`
  - `main.py`: `"Unknow error ocurred"` → `"Unknown error occurred"`
  - `session_summary_service.py`: `sumarize` → `summarize`
  - `update_transaction_params.py`: `coerce_datetime` → `coerce_datetime`, mensagem `"Espected"` → `"Expected"`
- [ ] **`logger.exception()` mal usado em `search_history.py`**: `exc_info=e` não passado como argumento nomeado.
- [ ] **`output_guardrail.py` — potencial `IndexError`**: `result.split("RESPOSTA:", 1)[1]` lança exceção se o LLM não retornar o formato esperado.

---

## 🏗️ Arquitetura & Design

- [ ] **Auto-import dinâmico em `__init__.py`**: `model/__init__.py` e `entities/__init__.py` importam qualquer `.py` no diretório — frágil, sem tratamento de erro, propenso a dependências circulares.
- [ ] **Monkey-patching de `ainvoke` nos agentes**: `agent.ainvoke = log_execution_time(...)` — frágil, obscuro, quebra se o LangChain mudar a implementação interna.
- [ ] **`create_agent` (API legada)**: Agentes usam `langchain.agents.create_agent` em vez de `create_react_agent` (API moderna do LangGraph).
- [ ] **`_active_sessions` como estado global mutável**: Dicionário em memória em `chat_session_service.py` — não escala, não é thread-safe, perdido em restart do processo.
- [ ] **Type hint errado em `get_active_sessions`**: Retorna `dict[str, str]` mas os valores são `ObjectId`.
- [ ] **`md_console.py` sombreia `print` builtin**: Importar `from md_console import print` substitui a builtin — causa confusão e bugs difíceis de rastrear.
- [ ] **Separação de camadas violada**: `model/__init__.py` importa `infrastructure.postgres.entities.base` — domínio não deveria depender de infraestrutura.
- [ ] **`Transaction.amount: float`**: Perde precisão em valores monetários — deveria ser `Decimal`.
- [ ] **`ChatMessage` sem timezone**: `datetime` sem timezone no MongoDB — inconsistente com o PostgreSQL que usa `timezone=True`.
- [ ] **`TransactionQueryParams` compara `date` com `datetime`**: Campos `occurred_at_start/end` são `date` mas o banco armazena `datetime` — comparação no SQLAlchemy pode dar resultados inesperados.
- [ ] **`source_text` obrigatório em `Transaction`**: Campo marcado como `...` (obrigatório) mas não é relevante em cenários de update — validação Pydantic pode quebrar usos parciais.

---

## 🧪 Testes

- [ ] **Testes de repositório inspecionam SQL interno**: Acessam `stmt._limit`, `stmt._order_by_clauses` (atributos privados) — quebram com upgrade do SQLAlchemy sem mudança de comportamento.
- [ ] **Tool tests usam construção insegura**: `TransactionService.__new__()` + `object.__setattr__()` + lambdas — pulam `__init__` e injeção de dependência.
- [ ] **Nenhum teste unitário para agentes**: `tests/test_agents/` tem apenas `__init__.py` vazio. Só existem testes de integração (que requerem PostgreSQL).
- [ ] **Caminhos de erro não testados**: Timeout de LLM, falha de conexão com banco, payloads muito grandes, concorrência em `_active_sessions`.
- [ ] **Testes de `ChatSessionService` acoplados à implementação**: Manipulam `_active_sessions` diretamente e patcheam `ChatSession` no módulo — quebram se a implementação interna mudar.
- [ ] **`tests/integration/conftest.py` vazio**: Arquivo morto — pode ser removido.
- [ ] **Typos propagados nos testes**: `input_aproved` / `output_aproved` aparecem também nos testes — precisam ser atualizados em conjunto com a correção no código.

---

## ⚙️ Configuração & Ambiente

- [ ] **`POSTGRES_PASSWORD` definido mas nunca consumido**: Variável no `.env` nunca é lida pelo código — a senha está embutida em `POSTGRES_URL`. Inconsistente.
- [ ] **`settings.extra="ignore"`**: Ignora silenciosamente typos em variáveis de ambiente — deveria ser `"forbid"` para detectar configuração incorreta.
- [ ] **Nenhuma validação de chaves de API presentes antes do uso**: Se `GEMINI_API_KEY` ou `GROQ_API_KEY` não estiverem configuradas, o erro é enigmático em runtime.
- [ ] **`.gitignore` sem `**/.env`**: Só ignora `.env` na raiz — subdiretórios com `.env` vazariam.
- [ ] **Engine PostgreSQL criado no nível de módulo**: `pg_connection.py` cria `engine` e `SessionLocal` no import — se `postgres_url` for inválido, o erro acontece na inicialização, não no primeiro uso.
- [ ] **Singleton `MongoManager._client` frágil**: Sem proteção contra inicialização concorrente — duas chamadas simultâneas a `init_database` criam duas conexões.

---

## 👷 Manutenção Geral

- [ ] **Migrations documentam limitações de ENUM**: Docstring de `Category` alerta que mudanças no enum Python requerem migração manual — considerar automatizar ou documentar no `README`.
- [ ] **`payment_method` com `String(32)`**: Pode ser curto demais para alguns métodos de pagamento.
- [ ] **Recarregar FAISS a cada chamada**: `get_faq_db()` é chamado em toda invocação do FAQ — cache singleton reduziria latência.
