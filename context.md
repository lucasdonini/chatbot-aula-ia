# Contexto do Projeto: Assessor.IA

## 1. Visão geral

O Assessor.IA é uma aplicação web de estudo que demonstra um assistente
multiagente para organização financeira e apoio ao dia a dia. O sistema combina
uma API FastAPI, um grafo de agentes LangGraph e uma interface React.

O projeto é usado em aulas de IA de um curso de desenvolvimento de sistemas. Por
ser público e possuir uma arquitetura diferente da implementação de referência do
curso, sua documentação deve permitir que outros alunos entendam tanto a execução
quanto as decisões técnicas sem depender do histórico das aulas.

## 2. Stack tecnológica

### Aplicação

- API: FastAPI e Uvicorn;
- orquestração de agentes: LangGraph e LangChain;
- frontend: React 19, TypeScript, Vite e Oxlint;
- modelos: Gemini e Groq;
- gerenciamento Python: uv;
- qualidade Python: Ruff, MyPy e Pytest;
- qualidade frontend: Oxlint, TypeScript e build Vite;
- containers: Docker e Docker Compose.

### Persistência

- PostgreSQL: transações e demais dados estruturados de domínio;
- SQLAlchemy assíncrono: acesso ao PostgreSQL;
- Alembic: evolução do schema relacional;
- MongoDB: sessão, mensagens, erros e resumo da conversa;
- Beanie/PyMongo: acesso ao MongoDB;
- Qdrant: banco vetorial usado para indexação e consulta ao FAQ.

## 3. Arquitetura

O backend segue uma arquitetura em camadas, com separação gradual entre domínio,
aplicação e detalhes técnicos:

- `app/domain` contém modelos do domínio;
- `app/application` contém portas, contratos, modelos de entrada e exceções;
- `app/services` coordena casos de uso;
- `app/infrastructure` implementa agentes, persistência, LLMs, relógio e logging;
- `app/api` contém rotas, dependências e tratamento de exceções HTTP;
- `app/main.py` é o composition root FastAPI;
- `app/lifespan.py` inicializa bancos, serviços, grafo e sessão.

O frontend fica isolado em `frontend`. Durante o desenvolvimento, o Vite encaminha
`/api` ao FastAPI. Em execução integrada, o backend serve o conteúdo compilado de
`frontend/dist`.

## 4. Fluxo atual de uma mensagem

1. O usuário envia uma mensagem pela interface React.
2. O frontend chama `POST /api/chat`.
3. A rota persiste a mensagem humana no MongoDB.
4. O grafo executa guardrails, roteamento e o agente especialista adequado.
5. Tools financeiras acessam o PostgreSQL por meio de serviços e repositórios.
6. A resposta é persistida no MongoDB e devolvida como string JSON.
7. O frontend valida o formato e renderiza a resposta como Markdown seguro.

A versão atual cria uma sessão quando o processo da API inicia e a finaliza no
shutdown. Todos os requests atendidos pelo mesmo processo usam essa sessão. Lista
de conversas, seleção de sessão pelo cliente e endpoints de histórico não fazem
parte do escopo entregue.

## 5. Configuração e execução

- Python suportado: 3.14, conforme `pyproject.toml`;
- Node.js usado no build: 24, conforme `Dockerfile` e CI;
- arquivo de configuração da aplicação: `.env`;
- exemplo versionado: `.env.example`;
- entrada da API: `app.main:app`;
- frontend de desenvolvimento: `http://localhost:5173`;
- aplicação integrada: `http://localhost:8000`;
- documentação OpenAPI: `/docs` e `/redoc`;
- health check: `/health`.

PostgreSQL e MongoDB são dependências externas. O Compose atual executa apenas a
aplicação e não cria containers para esses bancos. O Qdrant também é uma
dependência externa e deve estar acessível antes da inicialização.

Os comandos operacionais atualizados estão no `README.md` e no `makefile`.

## 6. Testes e CI

Os testes Python estão organizados em unitários, arquiteturais e de integração.
O Pytest padrão exclui a marca `integration`; a execução explícita dessa marca usa
Testcontainers e requer Docker.

A workflow `.github/workflows/ci.yml` roda em pull requests para `main` e apresenta
os seguintes checks independentes:

- `lint` — Ruff;
- `unit-tests` — testes sem a marca de integração;
- `integration-tests` — testes com Testcontainers;
- `type-checks` — MyPy;
- `frontend-lint` — Oxlint;
- `frontend-tests` — Vitest e Testing Library;
- `frontend-type-check` — compilação TypeScript;
- `frontend-build` — geração do bundle Vite.

A separação dos jobs permite identificar diretamente qual camada falhou. O
snapshot verificado em 2026-08-23 é de 312 testes Python sem a marca de
integração, 64 testes Python de integração e 10 testes do frontend, todos verdes.

Os testes HTTP cobrem o contrato da rota de chat, validação, timeout, erro
inesperado, health check, OpenAPI e entrega dos arquivos estáticos. O frontend
cobre o cliente HTTP, a renderização de Markdown e os fluxos principais da tela.
O lifespan com substituição completa da infraestrutura ainda não possui teste
dedicado.

A execução ainda emite avisos de manutenção provenientes da transição futura do
Google GenAI para Python 3.17, da descontinuação gradual de
`langchain-community` e da camada `TestClient` atual do FastAPI. O import
depreciado do módulo PostgreSQL do Testcontainers foi atualizado para
`testcontainers.community.postgres` durante esta auditoria.

## 7. Estado da migração para API

A migração da antiga interface de linha de comando para a aplicação web foi
concluída no escopo atualmente entregue:

- FastAPI é a entrada da aplicação;
- startup e shutdown são controlados pelo lifespan;
- o chat está exposto em `POST /api/chat`;
- exceções são convertidas em respostas HTTP sem expor detalhes internos;
- a interface React consome a API;
- o backend serve o build do frontend;
- Docker gera e empacota os dois componentes;
- a CI valida backend e frontend.

As decisões permanentes e as diferenças entre o plano original e o escopo final
foram consolidadas neste documento após a conclusão da migração.

## 8. Decisões e características relevantes

- Guardrails de entrada operam de forma fail-closed.
- Dados sensíveis são anonimizados antes do processamento que não precisa deles.
- O contexto de logs usa `ContextVar` para evitar cruzamento entre tasks
  assíncronas.
- O relógio da aplicação centraliza UTC para persistência e timezone local para
  contexto temporal.
- Exceções inesperadas são registradas internamente, mas a API devolve mensagem
  genérica.
- O Markdown do frontend ignora HTML embutido.
- O checkpointer do grafo permanece em memória e não é adequado a múltiplos
  workers com continuidade de sessão.
- O FAQ usa coleções Qdrant versionadas e um alias estável. Cada nova ingestão
  troca o alias atomicamente e remove a coleção anteriormente ativa.

## 9. Próximos passos fora da migração concluída

- definir uma estratégia de sessão por usuário e persistência de checkpoints;
- decidir se lista de conversas e endpoints de histórico entrarão no produto;
- ampliar os testes frontend conforme surgirem novos fluxos e componentes;
- testar o lifespan com dependências de infraestrutura substituídas;
- melhorar progressivamente a separação entre camadas;
- continuar o aprimoramento de tipagem e observabilidade;
- adicionar novas categorias e capacidades financeiras conforme a necessidade.
