# Melhorias futuras

Este backlog reúne evoluções que não são necessárias para o fluxo atual funcionar,
mas aumentam sua correção, clareza arquitetural e capacidade de operar com mais de
um cliente ou worker. Os itens estão ordenados por prioridade.

## Prioridade alta

### Consolidar a composição da aplicação

- Construir `ChatSessionService`, repositório, clock, gerador de texto e loggers no
  composition root.
- Fazer as dependências FastAPI apenas recuperarem serviços já construídos.
- Eliminar imports diretos da infraestrutura em `app/api/dependencies.py`.
- Garantir que o timezone venha da porta de settings, sem valor fixo na API.
- Definir explicitamente o ciclo de vida de cada dependência.
- Construir uma única instância por aplicação para serviços stateless e componentes
  seguros para uso concorrente.
- Manter contexto de logging, identificadores, transações e outros estados da
  requisição isolados por requisição ou por `ContextVar`.
- Evitar singletons globais: limitar as instâncias compartilhadas ao lifespan da
  aplicação para preservar isolamento e substituição simples nos testes.
- Documentar quais clientes e serviços podem ser reutilizados concorrentemente.

Critério de conclusão: a camada de API depende apenas de contratos e serviços da
aplicação; implementações concretas são selecionadas em um único local; e cada
dependência possui ciclo de vida e garantias de concorrência documentados.

### Validar o identificador de sessão na API

- Receber `session_id` como UUID na fronteira HTTP.
- Manter a conversão para string somente onde os contratos atuais exigirem.
- Cobrir UUID inválido com resposta HTTP 422.

Critério de conclusão: valores arbitrários não chegam ao repositório, ao grafo ou
ao contexto de logging.

### Tornar falhas de persistência semânticas

- Substituir asserts usados para validar retornos externos por exceções internas
  específicas da aplicação ou infraestrutura.
- Verificar se `append_entry` e `update_summary` encontraram o documento esperado.
- Traduzir falhas técnicas para respostas públicas seguras, preservando a causa nos
  logs.

Critério de conclusão: documento ausente, retorno inesperado do ODM e indisponibilidade
do banco têm comportamentos explícitos e testes próprios.

### Definir o encerramento da sessão

- Criar uma operação explícita para finalizar uma conversa.
- Tornar a finalização idempotente.
- Gerar e persistir o resumo apenas quando houver entradas novas.
- Limpar o contador de interações do logger ao encerrar a sessão.
- Definir o comportamento quando uma mensagem chega após a finalização.

Critério de conclusão: o ciclo de vida da sessão possui estados e transições
documentados, sem depender do shutdown do processo ou do fechamento da página.

## Prioridade média

### Serializar turnos concorrentes da mesma sessão

- Impedir que duas mensagens da mesma conversa sejam processadas fora de ordem.
- Permitir que sessões diferentes continuem em paralelo.
- Documentar que `asyncio.Lock` protege somente um processo.
- Avaliar lock distribuído apenas quando houver múltiplos workers.

Critério de conclusão: pergunta e resposta de cada turno permanecem ordenadas sob
requisições concorrentes.

### Persistir checkpoints do grafo

- Substituir o checkpointer em memória quando a aplicação precisar sobreviver a
  reinícios ou operar com múltiplos workers.
- Garantir que o identificador usado pelo grafo seja o mesmo da sessão persistida.
- Testar retomada de conversa após reinício do processo.

Critério de conclusão: o contexto do agente não depende da memória de um worker.

### Ampliar os testes de integração de sessão

- Executar duas chamadas concorrentes de `get_or_create` e confirmar um único
  documento no MongoDB.
- Verificar que `$setOnInsert` não altera uma sessão existente.
- Cobrir falha ao adicionar uma entrada em sessão inexistente.
- Cobrir contexto de logging em requisições concorrentes e nos exception handlers.

Critério de conclusão: atomicidade, isolamento de contexto e persistência são
validados contra implementações reais, não apenas mocks.

### Evoluir a interface de conversa

- Exibir o histórico completo da conversa em vez de somente a última resposta.
- Permitir iniciar uma nova sessão explicitamente.
- Definir se uma sessão deve sobreviver ao reload da página.
- Preparar a interface para carregar conversas anteriores quando houver endpoints
  de histórico.

Critério de conclusão: o ciclo de vida visível no frontend corresponde ao ciclo de
vida definido no backend.

## Prioridade baixa ou condicionada a métricas

### Avaliar Redis

- Usar Redis inicialmente apenas para coordenação distribuída, TTL ou locks.
- Não usar cache como fonte de verdade do histórico.
- Considerar Redis Streams e persistência assíncrona somente se medições mostrarem
  que o MongoDB é um gargalo.

Critério de adoção: necessidade comprovada de múltiplos processos, redução de
latência ou throughput superior ao suportado pelo desenho atual.

### Adicionar streaming de respostas

- Definir contrato SSE ou WebSocket.
- Preservar tratamento de timeout e persistência da resposta completa.
- Tratar desconexão do cliente sem corromper o turno.

### Tratar avisos de dependências

- Migrar `PyPDFLoader` de `langchain-community` para uma integração mantida antes
  da remoção definitiva do pacote, acompanhando seus avisos de descontinuação.
- Acompanhar a compatibilidade do Google GenAI com versões futuras do Python.
- Atualizar a camada de testes quando a transição de `httpx` do Starlette estiver
  estabilizada.

### Adicionar rollback da coleção vetorial do FAQ

- Preservar temporariamente a coleção Qdrant anteriormente ativa.
- Definir uma política de retenção para coleções versionadas.
- Permitir que o alias do FAQ volte atomicamente para a versão anterior.

Critério de adoção: o FAQ tornar-se crítico ou exigir recuperação imediata após
uma ingestão semanticamente incorreta.

### Manter documentação e decisões arquiteturais

- Atualizar README e `context.md` após estabilizar o contrato de sessão.
- Registrar decisões relevantes em ADRs curtos: ausência de cache, atomicidade do
  upsert, política de concorrência e estratégia de checkpoints.
- Documentar limitações operacionais conhecidas antes de habilitar múltiplos
  workers.
