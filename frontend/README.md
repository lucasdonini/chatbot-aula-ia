# Frontend do Assessor.IA

Interface React e TypeScript do Assessor.IA, construída com Vite. A aplicação
envia mensagens ao backend FastAPI e renderiza as respostas do assistente em
Markdown com suporte a GitHub Flavored Markdown.

## Requisitos

- Node.js 24;
- npm;
- backend do Assessor.IA disponível em `http://localhost:8000` durante o
  desenvolvimento integrado.

## Instalação

A partir da pasta `frontend`:

```bash
npm ci
```

O uso de `npm ci` preserva as versões definidas no `package-lock.json` e é o mesmo
fluxo usado no Dockerfile e na CI.

## Desenvolvimento

```bash
npm run dev
```

O Vite disponibiliza a interface em `http://localhost:5173`. Requisições para
`/api` são encaminhadas para `http://localhost:8000` pela configuração de proxy em
`vite.config.ts`.

O backend deve estar ativo para que o envio de mensagens funcione. Atualmente o
frontend consome `POST /api/chat` com um objeto contendo `message` e espera uma
string JSON como resposta.

## Scripts

- `npm run dev` — inicia o servidor Vite com hot reload;
- `npm run lint` — executa Oxlint;
- `npm run type-check` — valida o projeto com TypeScript sem gerar bundle;
- `npm run build-only` — gera o bundle Vite sem repetir o type checking;
- `npm run build` — executa type checking e build Vite em sequência;
- `npm run preview` — serve localmente o último build para inspeção.

## Build e execução integrada

```bash
npm run build
```

O resultado é gravado em `frontend/dist`. O FastAPI monta esse diretório e serve
o arquivo `index.html` em `/`, permitindo entregar frontend e API pelo mesmo
processo em produção.

O Dockerfile executa esse build em um estágio Node separado e copia somente o
conteúdo compilado para a imagem Python final.

## Estrutura principal

- `src/App.tsx` — formulário, estados de carregamento, resposta e erro;
- `src/api/chat.ts` — cliente HTTP de `POST /api/chat`;
- `src/components/MarkdownResponse.tsx` — renderização segura de Markdown;
- `src/index.css` e `src/App.css` — estilos globais e da interface;
- `vite.config.ts` — plugins e proxy de desenvolvimento.

HTML embutido nas respostas Markdown é ignorado por segurança. Erros de rede,
status HTTP não bem-sucedido e respostas em formato inesperado são convertidos
em mensagens descritivas para o usuário.

## Validações na CI

Cada validação possui um job próprio na workflow, facilitando identificar a causa
de uma falha no pull request:

- `frontend-lint`;
- `frontend-type-check`;
- `frontend-build`.

O projeto ainda não possui uma suíte automatizada de testes de componentes. Ao
adotá-la, o teste deve ser incluído como outro job explícito, sem ser ocultado no
job de build.
