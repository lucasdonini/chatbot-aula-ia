# Registro da Migração: CLI para API e Frontend

> Status: concluída no escopo entregue em 2026-08-23.
>
> Este arquivo é um registro histórico. Para instalar, executar e validar o
> projeto, consulte o [`README.md`](README.md). Para a arquitetura e o estado
> atual, consulte [`context.md`](context.md).

## 1. Objetivo original

O Assessor.IA era acessado por um loop de linha de comando. A migração buscou
transformá-lo em uma aplicação web, preservando o grafo multiagente, os serviços
de domínio e a persistência existente.

O plano inicial previa:

- uma API REST FastAPI;
- um endpoint de chat;
- sessões identificadas pelo cliente;
- listagem de conversas e consulta de mensagens anteriores;
- uma interface de chat;
- ciclo de vida seguro para bancos, loggers e agentes;
- testes e CI compatíveis com a nova arquitetura.

Durante a implementação, o escopo foi reduzido para uma primeira versão funcional
com uma sessão por processo e um único endpoint de chat. Os itens adiados estão
registrados ao final deste documento.

## 2. Resultado entregue

### Backend web

- `app/main.py` passou a expor a aplicação FastAPI em `app.main:app`;
- `app/lifespan.py` tornou-se responsável por montar dependências e controlar
  startup e shutdown;
- `POST /api/chat` recebe uma mensagem e devolve a resposta completa;
- `GET /health` fornece o health check;
- Swagger UI e ReDoc são disponibilizados pelo FastAPI;
- handlers convertem exceções de aplicação em respostas HTTP descritivas;
- erros inesperados são registrados internamente e não vazam detalhes técnicos.

### Frontend

- foi criada uma aplicação React, TypeScript e Vite em `frontend`;
- o frontend envia mensagens para `/api/chat`;
- respostas são renderizadas como Markdown, com HTML embutido desabilitado;
- erros de rede, HTTP e formato de resposta são apresentados de maneira
  descritiva;
- o Vite encaminha `/api` ao backend durante o desenvolvimento;
- o FastAPI serve `frontend/dist` na execução integrada.

### Empacotamento

- o Dockerfile usa um estágio Node 24 para gerar o frontend;
- a imagem Python 3.14 recebe somente o bundle compilado;
- o processo final inicia o Uvicorn com `app.main:app`;
- PostgreSQL e MongoDB permanecem serviços externos ao Compose atual.

### Qualidade e CI

- a workflow usa Python 3.14, alinhado ao `pyproject.toml`;
- Ruff, MyPy, testes unitários e testes de integração têm jobs próprios;
- o frontend possui jobs explícitos para Oxlint, TypeScript e build Vite;
- a instalação frontend na CI usa `npm ci` e o lockfile versionado;
- cada validação aparece separadamente no pull request para facilitar o
  diagnóstico de falhas.

## 3. Decisões mantidas durante a migração

| Tema | Decisão entregue | Consequência |
|---|---|---|
| Framework HTTP | FastAPI | API assíncrona, OpenAPI e handlers centralizados |
| Resposta do chat | Completa, sem streaming | Contrato e frontend mais simples nesta versão |
| Checkpoint do grafo | Memória do processo | Não oferece continuidade entre processos ou workers |
| Persistência | MongoDB para chat e PostgreSQL para domínio financeiro | Mantém responsabilidades distintas |
| Logging | Configurável e contextual com `ContextVar` | Tasks assíncronas não compartilham contexto acidentalmente |
| Tempo | Clock centralizado e timezone configurável | Testes determinísticos e persistência coerente em UTC |
| Segurança de erros | Mensagens públicas controladas | Tracebacks e exceções internas não chegam ao cliente |
| Distribuição do frontend | Build estático servido pelo FastAPI | Uma única origem na execução integrada |

## 4. Trabalhos preparatórios incorporados

Antes e durante a exposição HTTP, foram concluídas melhorias necessárias para uma
aplicação de longa duração:

- validação explícita das chaves LLM no startup;
- settings de logging, timeout e timezone;
- separação do arquivo de ambiente versionado e do `.env` local;
- correção de ordenação e limite na consulta de histórico;
- guardrail de entrada fail-closed;
- logging com contexto seguro para concorrência assíncrona;
- substituição de datas capturadas no import por um Clock injetável;
- timestamps de sessão timezone-aware;
- padronização do namespace raiz `app`;
- tratamento HTTP centralizado para exceções conhecidas e inesperadas.

Essas alterações continuam relevantes mesmo com o escopo menor de sessões da
primeira versão web.

## 5. Diferenças em relação ao plano original

### Sessão

O plano previa receber ou criar um `session_id` por conversa e serializar requests
concorrentes da mesma sessão. A implementação entregue cria um UUID no lifespan e
o reutiliza durante toda a vida do processo.

Consequências:

- clientes atendidos pelo mesmo processo compartilham a sessão ativa;
- reiniciar o processo inicia outra sessão;
- múltiplos workers não compartilham o checkpoint em memória;
- a versão atual é adequada a demonstração e uso controlado, não a isolamento
  multiusuário.

### Histórico e títulos

Não foram implementados os endpoints originalmente propostos para listar sessões
ou carregar mensagens de uma sessão específica. Também não foi entregue geração
de título de conversa para a interface.

### Testes de API e frontend

O projeto cobre os serviços, agentes, infraestrutura e tratamento de exceções,
mas ainda deve ampliar testes direcionados às rotas FastAPI. O frontend possui
lint, type checking e build automatizados, porém ainda não possui testes de
componentes.

### CLI

A interface de linha de comando deixou de ser a entrada documentada. O nome
`app/main.py` foi mantido, agora como composition root da aplicação FastAPI.

## 6. Operação atual

O fluxo suportado é:

1. configurar `.env` a partir de `.env.example`;
2. disponibilizar PostgreSQL e MongoDB;
3. instalar dependências Python e frontend;
4. gerar `frontend/dist`;
5. aplicar as migrations Alembic;
6. iniciar `app.main:app` com Uvicorn;
7. acessar a interface ou chamar `POST /api/chat`.

Comandos e exemplos atualizados estão centralizados no README para evitar que este
registro histórico volte a competir com a documentação operacional.

## 7. Evoluções futuras

As seguintes extensões não fazem parte da migração concluída:

- sessão identificada por usuário ou conversa;
- locks por sessão para turnos concorrentes;
- checkpointer persistente compatível com múltiplos workers;
- `GET /sessions` e `GET /sessions/{id}/messages`;
- títulos e previews de conversas;
- política contínua de resumos por quantidade de mensagens ou inatividade;
- testes de rota com ciclo de vida e dependências substituídas;
- testes de componentes e integração HTTP do frontend;
- streaming de respostas.

Cada evolução deve ser tratada como uma nova feature, com contrato, segurança,
persistência e critérios de aceite próprios, sem reabrir a migração já concluída.
