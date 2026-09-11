# Terminal Session Manager — Especificação

## 1. Objetivo

Construir um Terminal Session Manager minimalista, modular e orientado a agentes. O sistema mantém sessões de terminal independentemente do agente que as iniciou, executa comandos e jobs de forma síncrona ou assíncrona, preserva histórico consultável e permite operar dispositivos cadastrados sem expor credenciais ao agente.

O produto deve funcionar como um serviço de baixa complexidade operacional, com processamento e armazenamento proporcionais ao uso.

## 2. Objetivos

- manter sessões persistentes mesmo após desconexão ou substituição do agente;
- executar comandos e scripts com múltiplas entradas, saídas e estados;
- recuperar posteriormente estado, eventos, resultados e erros;
- cadastrar dispositivos e dados de conexão reutilizáveis;
- permitir que o agente use apenas o nome ou nickname do dispositivo;
- resolver credenciais internamente sem expor seus valores ao agente;
- preservar credenciais localmente de forma protegida quando necessário;
- expor API programática e MCP com capacidades equivalentes;
- manter módulos independentes, contratos pequenos e baixo consumo de recursos.

## 3. Não objetivos

- interface gráfica completa;
- detecção inteligente de prompts ou interpretação semântica geral;
- alta disponibilidade, distribuição ou escalonamento horizontal;
- suporte inicial a todos os terminais, protocolos e sistemas operacionais;
- automação baseada em IA dentro do servidor;
- revelação, edição ou exportação de senhas por agentes.

## 4. Escopo funcional

### 4.1 Sessões

Permitir criar, consultar, reconectar, ler, escrever, redimensionar e encerrar sessões. Uma sessão possui identidade estável, estado, timestamps, destino opcional e histórico.

Estados mínimos: `created`, `running`, `waiting`, `completed`, `failed`, `closed` e `lost`.

Quando possível, a sessão continua após a desconexão do agente. A reconexão recupera estado e saídas por cursor.

### 4.2 Comandos e jobs

Aceitar escrita interativa e jobs identificados. Um job pode conter comando ou script, parâmetros, política de execução e destino.

Registrar identidade, estado, timestamps, sessão, dispositivo, entradas, saídas, erros, código de saída, falha, cancelamento e timeout.

Jobs longos não devem exigir conexão contínua do agente.

### 4.3 Histórico e eventos

Sessões e jobs produzem eventos ordenados e recuperáveis. Eventos distinguem entrada, saída, erro, mudança de estado e eventos do sistema.

O histórico deve suportar leitura incremental por cursor, consulta resumida/detalhada, retenção configurável, indicação de dados mascarados e associação ao job de origem.

### 4.4 Dispositivos

Permitir cadastrar, consultar, atualizar, desativar e remover logicamente dispositivos. Um dispositivo possui nome ou nickname, endereço, tipo, porta, método de conexão, usuário padrão, opções não secretas e referência a uma credencial.

O agente solicita conexão pelo identificador ou nickname; o gerenciador resolve internamente os dados de conexão.

### 4.5 Credenciais

Credenciais são separadas dos metadados do dispositivo e do histórico. Podem representar senha, chave, token ou outro segredo.

O sistema pode persistir credenciais localmente quando necessário, mas nunca em texto puro. A proteção em repouso deve usar mecanismo apropriado, com chave ou mecanismo de proteção separado do registro público do dispositivo. Quando disponível, pode ser usado um provedor externo de segredos.

Durante a autenticação, o segredo pode existir em memória e trafegar internamente pelo Terminal Session Manager. O componente de conexão pode resolvê-lo, mas API e MCP nunca devem devolver seu valor ao agente.

### 4.6 API e MCP

A API deve oferecer operações para sessões, eventos, jobs, dispositivos e metadados de credenciais sem expor segredos.

O MCP deve apresentar ferramentas pequenas, previsíveis e orientadas a tarefas, com respostas compactas, paginação, cursores e limites explícitos.

API e MCP usam os mesmos serviços internos. A implementação MCP usará a biblioteca FastMCP.

## 5. Princípios arquiteturais

- persistência pertence ao serviço, não ao agente;
- o núcleo não depende de transporte, terminal específico ou provedor de segredos;
- adaptadores encapsulam terminal local, PTY, SSH e futuros transportes;
- eventos são a unidade comum de histórico e recuperação;
- operações devem ser idempotentes quando possível;
- o caminho comum deve ser simples;
- recursos devem ser liberados explicitamente e por timeout/limpeza;
- funcionalidades opcionais não devem aumentar a complexidade do núcleo.

Módulos conceituais: domínio de sessões/jobs; persistência; adaptadores de terminal/transporte; catálogo de dispositivos; credenciais; API/MCP; autorização, auditoria e retenção.

## 6. Requisitos não funcionais

- **Confiabilidade:** falhas produzem estado e evento claros; nada falha silenciosamente.
- **Persistência:** reinício não apaga sessões finalizadas, jobs ou eventos; sessões vivas devem ser marcadas ou recuperadas conforme o adaptador.
- **Segurança:** menor privilégio, validação, isolamento e ausência de segredos em registros observáveis.
- **Desempenho:** baixo overhead, leitura incremental e limites de saída.
- **Operabilidade:** logs técnicos mínimos, diagnóstico de estado e encerramento limpo.
- **Testabilidade:** contratos e adaptadores testáveis sem dispositivos reais.
- **Evolução:** novos transportes, armazenamentos e provedores de segredo sem alterar o domínio.
- **Compatibilidade:** contratos públicos versionados e comportamento previsível.

## 7. Segurança e proteção de dados

- toda operação possui identidade e política de autorização;
- acesso a dispositivo, sessão, job e histórico é validado por recurso;
- segredos nunca aparecem em respostas, eventos, histórico, dumps, traces, logs, erros ou mensagens de diagnóstico;
- credenciais persistidas localmente são protegidas em repouso e não ficam em texto puro;
- entradas sensíveis são marcadas e mascaradas antes da persistência;
- saídas de terminal contendo credenciais são mascaradas;
- comandos e destinos são validados dentro do contexto autorizado;
- auditoria registra ações sem registrar conteúdo secreto;
- retenção e exclusão lógica do histórico são configuráveis.

## 8. Critérios gerais de aceitação

1. Uma sessão continua consultável após a desconexão do cliente.
2. Entradas, saídas, erros e estados são recuperáveis em ordem.
3. Um job termina sem o agente conectado e seu resultado pode ser recuperado.
4. Um nickname resolve o dispositivo sem repetir manualmente os dados de conexão.
5. O gerenciador usa a credencial configurada sem revelar seu valor ao agente.
6. Credenciais persistidas localmente não ficam em texto puro.
7. Segredos não aparecem em histórico, logs, erros, API ou MCP.
8. API e MCP usam as mesmas regras e estados do núcleo.
9. Reinício, timeout, cancelamento, falha de transporte e saída volumosa têm comportamento definido e testado.
10. O sistema executa com configuração mínima e sem componentes opcionais.

## 9. Etapas de desenvolvimento

Cada etapa gera relatório com escopo, decisões, arquivos/módulos, testes, resultados, limitações, riscos e recomendação para a etapa seguinte.

### Etapa 0 — Contrato e esqueleto

Definir módulos, modelos, estados, eventos e contratos mínimos. Validar rastreabilidade e testes conceituais.

### Etapa 1 — Sessão local mínima

Implementar sessão local com criação, leitura, escrita e encerramento. Testar comandos, timeout, erro, processo encerrado e isolamento.

### Etapa 2 — Persistência e histórico

Persistir metadados e eventos, com cursor e recuperação após reinício. Testar ordem, replay, paginação, retenção e saída volumosa.

### Etapa 3 — Jobs assíncronos

Implementar execução sem cliente conectado, status, cancelamento, timeout e recuperação. Testar sucesso, erro, cancelamento, timeout e concorrência.

### Etapa 4 — Dispositivos e credenciais

Implementar catálogo, nickname, referências de credenciais e proteção em repouso. Testar resolução, desativação, segredo ausente e não exposição.

### Etapa 5 — API

Expor contratos essenciais com limites, paginação, erros estáveis e autorização mínima. Executar testes de contrato e concorrência.

### Etapa 6 — MCP

Mapear capacidades para FastMCP, mantendo respostas compactas e sem exposição de segredos. Executar testes ponta a ponta.

### Etapa 7 — Endurecimento e documentação

Consolidar configuração, observabilidade, limpeza, compatibilidade e documentação. Executar suite completa, falhas, segurança e instalação limpa.

## 10. Formato do relatório

```text
# Relatório — Etapa N

## Status
concluída | parcial | bloqueada

## Entregue

## Requisitos atendidos

## Testes

## Desvios e limitações

## Riscos e decisões pendentes

## Entrada recomendada para a próxima etapa
```

## 11. Regra dos prompts

Cada prompt de etapa deve conter somente objetivo, escopo, limites, critérios e relatório, referenciando esta especificação em vez de repetir regras gerais. O agente deve validar o resultado contra o prompt antes de concluir.

## 12. Decisões adiadas

Além de Python e `uv`, escolhas de banco, bibliotecas de terminal, protocolo remoto, autenticação, provedor de segredos e empacotamento devem ser feitas somente quando necessárias, priorizando simplicidade, segurança, disponibilidade local, custo e testabilidade.
