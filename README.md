# Chatbot Aula IA

Assistente modular para as aulas de IA — agentes principais em `src/agents/` e infraestrutura em `src/infrastructure/`.

## Rápido (o essencial)
- Requisitos: `python 3.12+`, `git`. Docker é opcional para execução em container.
- Logs: `logs/`.

## Como rodar (opções)

1) Usando `make` (recomendado quando disponível)

- Preparar e rodar (constrói containers e inicia o app):

```bash
make build
```

- Rodar local (usa `.venv` se existir):

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
uv run src.main
```

3) Sem `make` e sem `uv` (manual, funciona em Windows/Unix)

- Criar e ativar um venv (Unix/macOS):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
python -m src.main
```

- Criar e ativar um venv (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
.\.venv\Scripts\python -m src.main
```

4) Somente Docker (sem instalar dependências locais)

```bash
docker compose up -d --build
```

Para acessar o banco (quando o serviço estiver ativo):

```bash
docker exec -it acessoria-sql psql -d acessoriadb
```

## Comandos úteis (Makefile)

- `make build` — executa `uv sync`, sobe containers e inicia o app.
- `make build-db` — `docker compose up -d --build` (apenas DB/infra).
- `make run` — executa `python -m src.main` usando o `.venv`.
- `make prepare-environment` — `uv sync` (sincroniza dependências).
- `make access-db` — abre um shell psql no container do banco.

## Como alterar o projeto

- Código: `src/` — edite agentes em `src/agents/`.
- Dependências: se possível, adicione e remova dependências via `uv add / remove`. Se não der, altere o `pyproject.toml` e rode `pip install -e .`
- Banco: scripts em `sql/` (ex.: `sql/init-db.sql`). Para recriar a infra, use `docker compose up -d --build`.

## Dicas rápidas

- Se não tiver `uv`: use o fluxo de venv + `python -m src.main`.
- Se não tiver `make`: use `uv` ou os comandos manuais acima.
- Para trocar o Python usado pelo projeto, ative o venv desejado antes de rodar.

## Contribuição

- Abra issues e PRs. Crie uma branch por feature e escreva commits pequenos.
