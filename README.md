# Chatbot Aula IA

Assistente modular para as aulas de IA — agentes principais em `app/agents/` e infraestrutura em `app/infrastructure/`.

## Rápido (o essencial)
- Requisitos: `python 3.12+`, `git`. Docker é opcional para execução em container.
- Logs: `logs/`.
- Configuração local: copie `.env.app.example` para `.env.app` e
  `.env.compose.example` para `.env.compose`. Preencha as chaves LLM em `.env.app`.

## Como rodar (opções)

1) Usando `make` (recomendado quando disponível)

- Preparar dependências, configurar ambiente, banco e iniciar a CLI:

```bash
make prepare-environment
# Crie .env.app e .env.compose a partir dos respectivos arquivos .example.
make build-db
make upgrade-db
make run
```

- O MongoDB deve estar disponível em `MONGODB_URI` e as chaves LLM devem estar
  configuradas em `.env.app` antes de executar `make run`.

- Rodar a CLI após a preparação:

```bash
make run
```

2) Usando `uv` (se instalado)

- Sincronizar dependências/ambiente:

```bash
uv sync
```

- Executar o módulo principal:

```bash
uv run python -m app.main
```

3) Sem `make` e sem `uv` (manual, funciona em Windows/Unix)

- Criar e ativar um venv (Unix/macOS):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m app.main
```

- Criar e ativar um venv (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
.\.venv\Scripts\python -m app.main
```

4) Banco PostgreSQL com Docker

```bash
docker compose up -d --build
```

O PostgreSQL 18 usa o volume em `/var/lib/postgresql`. Ao atualizar de uma
imagem anterior, recrie o volume após exportar dados que precisem ser mantidos.

Para acessar o banco (quando o serviço estiver ativo):

```bash
docker exec -it assessoria-sql psql -d assessoriadb
```

## Comandos úteis (Makefile)

- `make build-db` — `docker compose up -d --build` (apenas DB/infra).
- `make run` — executa `uv run python -m app.main`.
- `make prepare-environment` — `uv sync` (sincroniza dependências).
- `make access-db` — abre um shell psql no container do banco.

## Como alterar o projeto

- Código: `app/` — edite agentes em `app/agents/`.
- Dependências: se possível, adicione e remova dependências via `uv add / remove`. Se não der, altere o `pyproject.toml` e rode `pip install -e .`
- Banco: scripts em `sql/` (ex.: `sql/init-db.sql`). Para recriar a infra, use `docker compose up -d --build`.

## Dicas rápidas

- Se não tiver `uv`: use o fluxo de venv + `python -m app.main`.
- Se não tiver `make`: use `uv` ou os comandos manuais acima.
- Para trocar o Python usado pelo projeto, ative o venv desejado antes de rodar.

## Contribuição

- Abra issues e PRs. Crie uma branch por feature e escreva commits pequenos.
