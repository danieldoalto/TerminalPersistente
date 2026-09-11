# Terminal Session Manager — Especificação do Projeto

## 1. Objetivo

Construir um Terminal Session Manager minimalista, modular e orientado a agentes. O sistema mantém sessões de terminal independentemente do agente que as iniciou, executa comandos e jobs de forma síncrona ou assíncrona, preserva histórico consultável e permite operar dispositivos cadastrados sem expor credenciais ao agente.

O produto deve funcionar como um serviço de baixa complexidade operacional, com processamento e armazenamento proporcionais ao uso.

## 2. Objetivos

- Manter sessões persistentes mesmo quando o agente desconecta ou é substituído.
- Executar comandos e scripts com múltiplas entradas, saídas e estados intermediários.
- Permitir recuperação posterior de estado, eventos, resultados e erros.
- Cadastrar dispositivos, parâmetros de conexão e referências a credenciais reutilizáveis.
- Resolver automaticamente o destino e o método de conexão a partir de um dispositivo conhecido.
- Impedir que segredos sejam retornados ao agente ou gravados em texto aberto no histórico.
- Expor uma API programática e uma interface MCP com capacidades equivalentes.
- Manter módulos independentes, contratos pequenos e baixo consumo de recursos.
- Permitir evolução incremental sem exigir um frontend ou banco sofisticado no início.

## 3. Não objetivos

Ficam fora do núcleo inicial:

- Interface gráfica completa.
- Detecção inteligente de prompts ou interpretação semântica de toda saída.
- Orquestração distribuída, alta disponibilidade ou escalonamento horizontal.
- Suporte inicial a todos os tipos de terminal, protocolos e sistemas operacionais.
- Automação baseada em IA dentro do servidor.
- Revelação, edição ou exportação de senhas por agentes.

## 4. Escopo funcional

### 4.1 Sessões

O sistema deve permitir criar, consultar, reconectar, ler, escrever, redimensionar e encerrar sessões. Uma sessão representa um terminal vivo e possui identidade estável, estado, timestamps, destino opcional e vínculo com seu histórico.

Estados conceituais mínimos: `created`, `running`, `waiting`, `completed`, `failed`, `closed` e `lost`.

Uma sessão deve continuar executando, quando possível, após a desconexão do agente. A reconexão deve permitir recuperar o estado e as saídas desde uma posição ou cursor informado.

### 4.2 Comandos e jobs assíncronos

O sistema deve aceitar tanto escrita interativa quanto execução de um job identificado. Um job pode conter um comando ou script, parâmetros, política de execução e destino.

O job deve registrar, no mínimo:

- identidade e estado;
- momento de criação, início e término;
- sessão e dispositivo relacionados;
- entradas enviadas;
- saídas normal e de erro;
- código de saída, quando disponível;
- falha, cancelamento ou timeout, quando aplicável.

Jobs longos não devem exigir conexão contínua do agente. O agente deve conseguir consultar status, eventos recentes, histórico completo ou resultado final.

### 4.3 Histórico e eventos

Cada sessão e job deve produzir eventos ordenados e recuperáveis. O histórico deve distinguir entrada, saída, erro, mudança de estado e eventos do sistema.

O histórico deve suportar:

- leitura incremental por cursor ou sequência;
- consulta resumida e consulta detalhada;
- retenção configurável;
- indicação de dados sensíveis omitidos ou mascarados;
- associação entre eventos e o job que os originou.

O formato de persistência é detalhe de implementação; o contrato deve preservar ordem, identidade e significado dos eventos.

### 4.4 Dispositivos

O sistema deve permitir cadastrar, consultar, atualizar, desativar e remover logicamente dispositivos. Um dispositivo pode conter nome, endereço, tipo, porta, método de conexão, usuário padrão, opções não secretas e referência a uma credencial.

O agente deve poder solicitar conexão por identificador ou nome do dispositivo, sem precisar repetir a linha de comando completa.

### 4.5 Credenciais

Credenciais devem ser tratadas como referências protegidas, separadas dos metadados de dispositivo e do histórico. O componente de conexão pode resolver uma credencial internamente, mas a API e o MCP não devem devolver seu valor ao agente.

O sistema deve suportar, conforme o adaptador disponível, senha, chave, token ou outro segredo. A forma de armazenamento seguro e o provedor de segredos devem ser abstraídos por um contrato pequeno.

### 4.6 API e MCP

A API deve oferecer operações equivalentes às capacidades essenciais do sistema, incluindo:

- criar e listar sessões;
- ler eventos e resultados;
- escrever em uma sessão;
- executar, consultar, cancelar e aguardar jobs;
- cadastrar e consultar dispositivos;
- consultar metadados de credenciais sem expor o segredo.

O MCP deve apresentar ferramentas pequenas, previsíveis e orientadas a tarefas. Respostas devem ser compactas por padrão, com paginação, cursores e limites explícitos.

API e MCP devem usar os mesmos serviços internos, evitando duas implementações de regras de negócio.

## 5. Princípios arquiteturais

- Persistência pertence ao serviço, não ao agente.
- Núcleo de domínio não deve depender de transporte, terminal específico ou provedor de segredos.
- Adaptadores devem encapsular PTY, SSH, shell local e futuros transportes.
- Eventos são a unidade comum de observabilidade, histórico e recuperação.
- Operações devem ser idempotentes quando isso for possível e declarar seus efeitos quando não forem.
- O caminho comum deve ser simples: criar, executar, acompanhar, recuperar e encerrar.
- Recursos devem ser liberados explicitamente e também por políticas de timeout/limpeza.
- Funcionalidades opcionais não devem aumentar a complexidade do núcleo.

Módulos conceituais:

1. Domínio de sessões e jobs.
2. Persistência de estado e eventos.
3. Adaptadores de terminal e transporte.
4. Catálogo de dispositivos.
5. Abstração de credenciais.
6. Serviços de API e MCP.
7. Autorização, auditoria e políticas de retenção.

## 6. Requisitos não funcionais

- **Confiabilidade:** falhas de conexão devem produzir estado e evento claros; o serviço não deve perder silenciosamente um job ou sua posição no histórico.
- **Persistência:** reinício do serviço não deve apagar sessões finalizadas, jobs nem eventos persistidos; sessões vivas devem ser marcadas ou recuperadas conforme a capacidade do adaptador.
- **Segurança:** princípio do menor privilégio, validação de entradas, isolamento de sessões e ausência de segredos em logs, respostas e mensagens de erro.
- **Desempenho:** baixo overhead; leitura incremental e limites de saída devem ser preferidos a cópias integrais repetidas.
- **Operabilidade:** logs técnicos mínimos, diagnóstico de estado e encerramento limpo.
- **Testabilidade:** contratos e adaptadores devem poder ser testados sem depender de dispositivos reais.
- **Evolução:** novos transportes, armazenamentos e provedores de segredo devem ser adicionáveis sem alterar o domínio.
- **Compatibilidade:** versionamento explícito dos contratos públicos e comportamento previsível para clientes antigos.

## 7. Segurança e proteção de dados

- Toda operação deve ter uma identidade e uma política de autorização, mesmo que a primeira versão tenha apenas um usuário local.
- Acesso a dispositivo, sessão, job e histórico deve ser validado individualmente.
- Segredos nunca devem aparecer em respostas, eventos, dumps, traces ou mensagens de erro.
- Entradas sensíveis devem ser marcadas e mascaradas no histórico.
- Comandos e destinos recebidos pela API devem ser validados e não devem permitir escape indevido do contexto autorizado.
- O sistema deve registrar auditoria de ações relevantes sem registrar o conteúdo secreto.
- Retenção e exclusão lógica do histórico devem ser configuráveis.

## 8. Critérios gerais de aceitação

O projeto será considerado conforme quando uma implementação demonstrar, por testes automatizados e evidências de execução, que:

1. Uma sessão continua disponível para consulta após a desconexão do cliente.
2. Entradas, saídas, erros e mudanças de estado podem ser recuperados em ordem.
3. Um job assíncrono pode terminar sem o agente permanecer conectado e seu resultado pode ser recuperado depois.
4. Um dispositivo cadastrado permite iniciar uma conexão sem repetir manualmente seus dados não secretos.
5. O fluxo de conexão usa a credencial configurada sem revelar seu valor ao agente nem ao histórico.
6. API e MCP chegam às mesmas regras e estados do núcleo.
7. Reinício, timeout, cancelamento, falha de transporte e saída volumosa têm comportamento definido e testado.
8. O sistema pode ser executado com configuração mínima e sem componentes opcionais.

## 9. Etapas de desenvolvimento

Cada etapa deve gerar um relatório curto contendo: escopo implementado, decisões, arquivos/módulos alterados, testes executados, resultados, limitações, riscos e recomendações para a etapa seguinte. Esse relatório será a entrada factual do próximo prompt.

### Etapa 0 — Contrato e esqueleto

Definir limites dos módulos, modelo conceitual, estados, eventos e contratos mínimos, sem implementar integrações desnecessárias.

**Testes/validação:** revisar rastreabilidade entre requisitos e contratos; validar que cada operação essencial tem entrada, saída, erro e estado definidos.

### Etapa 1 — Sessão local mínima

Implementar uma sessão local através de um adaptador de terminal, com criação, leitura, escrita, encerramento e ciclo de vida.

**Testes/validação:** comandos interativos, múltiplas leituras, encerramento, erro de processo, timeout e isolamento básico.

### Etapa 2 — Persistência e histórico

Adicionar armazenamento de metadados e eventos, recuperação por cursor e comportamento após reinício.

**Testes/validação:** ordem dos eventos, replay, paginação, histórico vazio, saída grande, reinício e retenção.

### Etapa 3 — Jobs assíncronos

Adicionar jobs, estados, execução sem cliente conectado, cancelamento, timeout e recuperação do resultado.

**Testes/validação:** jobs curtos e longos, sucesso, erro, cancelamento, timeout, múltiplas saídas e idempotência quando aplicável.

### Etapa 4 — Dispositivos e credenciais

Adicionar catálogo de dispositivos, referências de credenciais e adaptador de conexão remota escolhido para a primeira versão.

**Testes/validação:** resolução de dispositivo, conexão bem-sucedida e falha, segredo ausente, segredo incorreto e ausência do segredo em qualquer saída observável.

### Etapa 5 — API

Expor os contratos essenciais por uma API, com autenticação/autorização mínima, limites, paginação e erros estáveis.

**Testes/validação:** testes de contrato, concorrência básica, reconexão, limites de payload e autorização por recurso.

### Etapa 6 — MCP

Mapear as mesmas capacidades para ferramentas MCP compactas, com descrições claras e respostas adequadas ao consumo por agentes.

**Testes/validação:** chamadas ponta a ponta, respostas truncadas/paginadas, erros recuperáveis e confirmação de que segredos não são expostos.

### Etapa 7 — Endurecimento e documentação

Consolidar configuração, observabilidade mínima, limpeza de recursos, migração/compatibilidade e documentação operacional.

**Testes/validação:** suite completa, cenários de falha, análise de segurança, teste de reinício e execução a partir de instalação limpa.

## 10. Formato do relatório de etapa

```text
# Relatório — Etapa N

## Status
concluída | parcial | bloqueada

## Entregue
- ...

## Requisitos atendidos
- requisito -> evidência/teste

## Testes
- comando/ação: resultado

## Desvios e limitações
- ...

## Riscos e decisões pendentes
- ...

## Entrada recomendada para a próxima etapa
- objetivo
- contexto factual
- restrições
- testes obrigatórios
```

