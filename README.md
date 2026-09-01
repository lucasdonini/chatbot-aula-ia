# Assessor.IA

Assistente web multiagente para organização financeira e apoio ao dia a dia. O
backend usa FastAPI e LangGraph; a interface usa React, TypeScript e Vite.

O PostgreSQL armazena transações, o MongoDB armazena a sessão e o histórico do
chat, e o Qdrant mantém os embeddings usados na consulta ao FAQ. As respostas
podem ser produzidas por modelos Gemini e Groq.

## Requisitos

- Python 3.14;
- [uv](https://docs.astral.sh/uv/);
- Node.js 24 e npm;
- PostgreSQL, MongoDB e Qdrant acessíveis pela aplicação;
- chaves de API do Gemini, do Groq e do Qdrant;
- Docker, opcionalmente, para executar a aplicação em container.

O `docker-compose.yml` atual constrói e executa a aplicação, mas não provisiona
PostgreSQL, MongoDB nem Qdrant. Esses serviços precisam estar disponíveis
separadamente.

## Configuração inicial

Na raiz do projeto, crie o arquivo de ambiente usado pela aplicação:

```powershell
Copy-Item .env.example .env
```

Em Linux ou macOS, use `cp .env.example .env`. Preencha ao menos
`GEMINI_API_KEY`, `GROQ_API_KEY`, `QDRANT_API_KEY`, `QDRANT_URL`,
`POSTGRES_URL`, `MONGODB_URI` e `MONGODB_DBNAME`. O arquivo `.env` contém
segredos e não deve ser versionado.

Na primeira execução, use `INGEST_FAQ_PDF=true` para criar a coleção vetorial e
o alias configurado em `FAQ_COLLECTION_ALIAS`. Depois da ingestão, a opção pode
voltar para `false`. Novas ingestões constroem uma coleção versionada, trocam o
alias atomicamente e removem a coleção anterior.

### Configuração da busca no FAQ

As principais variáveis do pipeline vetorial são:

- `FAQ_COLLECTION_ALIAS`: alias estável consultado pela aplicação;
- `FAQ_COLLECTION_PREFIX`: prefixo das coleções versionadas criadas na ingestão;
- `EMBEDDING_DIMMENSIONS`: dimensão dos vetores, que deve ser compatível com o
  modelo de embeddings;
- `FAQ_CHUNK_SIZE` e `FAQ_CHUNK_OVERLAP`: tamanho e sobreposição dos trechos do
  PDF. A sobreposição deve ser menor que o tamanho do trecho;
- `FAQ_INGESTION_BATCH_SIZE`: quantidade de trechos processados por lote;
- `FAQ_SEARCH_SCORE_THRESHOLD`: similaridade mínima, entre `0` e `1`, para um
  trecho ser considerado relevante;
- `INGEST_FAQ_PDF`: controla se o PDF será ingerido durante a inicialização.

Mantenha `INGEST_FAQ_PDF=true` somente até uma inicialização concluir a ingestão
com sucesso. Cada nova ingestão cria outra coleção, valida a quantidade de pontos
e então troca o alias. O valor inicial de `FAQ_SEARCH_SCORE_THRESHOLD` é `0.52`,
mas deve ser calibrado com perguntas representativas sempre que o modelo de
embeddings ou o conteúdo do FAQ mudar.

Instale as dependências e prepare o frontend:

```bash
uv sync
npm ci --prefix frontend
npm run --prefix frontend build
uv run alembic upgrade head
```

O build inicial do frontend cria `frontend/dist`, diretório que o FastAPI monta
para servir a interface. Por isso, ele também é necessário antes da primeira
execução local do backend em um clone limpo.

## Desenvolvimento local

Inicie o backend em um terminal:

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Em outro terminal, inicie o servidor de desenvolvimento do frontend:

```bash
npm run --prefix frontend dev
```

A interface de desenvolvimento fica em `http://localhost:5173`. O Vite encaminha
requisições iniciadas por `/api` para o backend em `http://localhost:8000`.

Para testar o modo integrado, gere o frontend e inicie somente o backend:

```bash
npm run --prefix frontend build
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Nesse modo, a aplicação completa fica em `http://localhost:8000`.

Os atalhos equivalentes estão no `makefile`: `make dev`, `make up`,
`make build-frontend` e `make upgrade-db`.

## Execução com Docker

Com PostgreSQL, MongoDB e Qdrant já acessíveis e o `.env` configurado:

```bash
docker compose up --build
```

O build multi-stage instala o frontend, gera `frontend/dist`, instala as
dependências Python e publica a aplicação na porta 8000. As URLs de banco usadas
pelo container podem ser ajustadas no `docker-compose.yml` conforme o ambiente.

## API

### Enviar mensagem

`POST /api/chat`

Corpo da requisição:

```json
{
  "message": "Quanto gastei com alimentação?"
}
```

Em caso de sucesso, a API devolve `200` com uma string JSON contendo a resposta
do assistente:

```json
"Você gastou R$ 150,50 com alimentação."
```

Exemplo com curl:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Quanto gastei com alimentação?"}'
```

Falhas de validação seguem o formato padrão do FastAPI. Erros conhecidos de
aplicação usam `code` e `detail`; timeout retorna `504`; erros inesperados retornam
uma mensagem genérica sem expor detalhes internos.

### Endpoints auxiliares

- `GET /health` — verifica se a API está ativa;
- `GET /docs` — documentação interativa Swagger UI;
- `GET /redoc` — documentação ReDoc;
- `GET /` — interface web compilada.

## Qualidade e testes

Backend:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
uv run pytest -m integration
```

Os testes de integração usam Testcontainers e requerem Docker disponível.

Frontend:

```bash
npm run --prefix frontend lint
npm run --prefix frontend test
npm run --prefix frontend type-check
npm run --prefix frontend build
```

A CI executa checks separados para Ruff, MyPy, testes unitários, testes de
integração, lint do frontend, testes do frontend, type checking do frontend e
build Vite. A workflow é disparada em pull requests direcionados à branch `main`.

Na última auditoria, em 2026-08-23, passaram 312 testes Python sem a marca de
integração, 64 testes Python de integração e 10 testes do frontend. Esses números
são um snapshot e podem crescer; a fonte de verdade continua sendo a execução das
suítes.

## Organização do projeto

- `app/api` — rotas, dependências e tratamento HTTP;
- `app/application` — contratos, modelos de entrada e exceções da aplicação;
- `app/domain` — modelos e regras do domínio;
- `app/services` — casos de uso e coordenação de serviços;
- `app/infrastructure` — agentes, bancos, LLMs, logging e implementações técnicas;
- `frontend` — aplicação React/Vite;
- `migrations` — migrações Alembic;
- `tests` — testes unitários, arquiteturais e de integração;
- `data` — recursos estáticos usados pelos agentes.

O contexto arquitetural mais amplo e o escopo consolidado da migração para a
aplicação web estão em [`context.md`](context.md).

## Contribuição

Crie uma branch por alteração, mantenha commits pequenos e abra um pull request
para `main`. Não inclua arquivos `.env`, logs ou outros artefatos locais no
versionamento.
