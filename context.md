# Contexto do Projeto: Assessor.IA

## 1. Visão Geral
Este projeto contém um sistema de assistente multiagencial com acesso via CLI. O objetivo principal do assistente é ajudar na organização, tanto financeira como do dia a dia (tarefas, compromissos, etc.). 
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

## 3.2. Arquitetura e Organização de Pastas (do professor)
Projeto praticamente monolítico, contendo apenas arquivos soltos na raiz dividos por funcionalidade no nível mais macro possível, como `main.py` para o grafo, agentes e interação com usuário; `pg_tools.py` com conexão e interação com banco PostgreSQL e tools de agentes; `faq_tools.py` para tools do agente leitor de FAQ contendo toda a lógica desde a criação da tool até os embeddings; e assim por diante.


## 4. Comandos Frequentes (Para uso do Agente)
Podem ser consultadas no `makefile`, mas para contexto:
- Gerir dependências: `uv [add|remove|sync]`
- Rodar o linter: `ruff check [--fix]; ruff format`
- Gerar migrações: `alembic revision --autogenerate -m "mensagem"`
- Rodar testes: `pytest` (a ser implementado)

## 5. Estado Atual e Problemas Mapeados

### Problemas por implementação errada
1. **Paradigmas de Arquitetura mal aplicados:** Por estar aprendendo, muitas vezes eu não consigo organizar o código da forma correta, e com o tempo esses erros começam a ficar perseptíveis.
2. **Falta de padronização de logs e comentários:** Eu tentei manter um padrão lógico, mas não deu 100% certo. Comentários excessivos em certos lugares, faltantes em outros, além de logs mal posicionados existem e estão começando a me confundir.

### Problemas por falta de implementação
1. **Falta de testes:** Hoje, não existe nenhum teste de nenhum tipo, e com o crescimento do projeto e migrações recentes, testes estão ficando cada vez mais necessários.
