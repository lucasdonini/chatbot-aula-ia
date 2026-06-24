# Chatbot Aula IA

> Assistente das aulas de IA do Grilo, mas organizado em módulos e com pequenas modificações como cache do RAF do PDF e renderização de markdown rico no terminal

## Visão geral

Este projeto implementa um conjunto de agentes (FAQ, financeiro, guardrails) organizados em `src/agents/` e infraestrutura mínima em `src/infrastructure/`. Há suporte a ingestão de documentos (FAISS) e um banco inicial em `sql/init-db.sql`.

## Pré-requisitos

- Python 3.12
- UV (recomendado)
- Git
- Docker & Docker Compose (opcional, para execução em container)

## Instalação (local)

Crie e ative um ambiente virtual e instale as dependências:

```bash
uv sync
```

## Configuração inicial

- Duplique o `.env.example` e renomeie a cópia como `.env`
- Preencha as variáveis de ambiente faltantes
- (Opcional) se quiser adicionar novas variáveis de ambiente, adicione a nova chave ao `.env` e atualize o arquivo `src/infrastructure/settings.py`

## Executando localmente

Execute o módulo principal a partir da raiz do repositório:

```bash
make run
```

ou

```bash
uv run src.main
```

Saída e logs ficam em `logs/` por padrão.

## Executando com Docker

```bash
make build
```

A porta exposta depende da configuração interna — verifique `docker-compose.yml` e `Dockerfile`.

## Estrutura do projeto (resumo)

- `src/main.py` — ponto de entrada
- `src/agents/` — agentes principais e submódulos (faq, financial, guardrails)
- `src/infrastructure/` — conexão DB, store FAISS, logger e configurações
- `data/` — dados e documentos usados para RAG
- `sql/` — scripts SQL úteis (inclui `init-db.sql`)

## Uso rápido

- Para testar o agente FAQ, verifique `src/agents/faq/faq_agent.py` e execute o `main`.
- Para operações financeiras, revise `src/agents/financial/` e as ferramentas em `tools/`.

## Troubleshooting

- Se faltar dependências, execute `pip install -r requirements.txt` ou revise `pyproject.toml`.
- Logs: `logs/` para mensagens de execução.
- Erros de DB: verifique `sql/init-db.sql` e a string de conexão em `src/infrastructure/db_connection.py`.

## Contribuição

Sinta-se livre para abrir issues ou pull requests. Sugerimos seguir o padrão de commits e criar uma branch por feature.

---

Se quiser, posso:
- adicionar exemplos de comandos para cada agente;
- documentar variáveis de ambiente usadas;
- criar um `requirements.txt` baseado em `pyproject.toml`.
