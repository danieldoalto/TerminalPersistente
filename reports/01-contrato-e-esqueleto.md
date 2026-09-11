# Relatório — Etapa 0: Contrato e Esqueleto

## Status
concluída

## Entregue
- Inicialização e configuração do projeto Python gerenciado via `uv` com suporte a execução CLI e testes (`pyproject.toml`).
- Estrutura modular limpa e sem dependências externas de runtime (`src/terminal_session_manager`).
- Modelos de domínio completos:
  - `Session` e `SessionStatus` com máquina de estados de 7 status conceituais e grafo de transições permitidas.
  - `Job` e `JobStatus` com ciclo de vida (6 status), controle de timestamps, código de saída e razão de falha.
  - `Device`, `DeviceType` e `ConnectionMethod` com validação de formato, porta e desativação lógica.
  - `CredentialRef` e `CredentialType` com isolamento total de segredos (sem atributo de senha/chave em texto puro).
  - `Event` e `EventType` com ordenação natural estrita por sequência e timestamp, suporte a mascaramento e vínculo bidirecional com sessão e job.
- Interfaces formais de persistência e adaptadores (`typing.Protocol`):
  - `SessionRepository`, `JobRepository`, `EventRepository` em `interfaces.persistence`.
  - `TerminalTransport` em `interfaces.transport`.
  - `DeviceRepository` em `interfaces.device`.
  - `CredentialResolver` em `interfaces.credentials`.
- Hierarquia de exceções de domínio (`DomainError`, `InvalidStateTransitionError`, `InvalidStateError`, `EntityNotFoundError`, `ValidationError`, etc.).
- Suíte de 41 testes unitários cobrindo 100% dos modelos, regras de transição, ordenação de eventos e conformidade dos contratos.
- Documentação de instalação, execução e testes no `README.md`.

## Estrutura do Projeto
```text
.
├── pyproject.toml
├── README.md
├── spec.md
├── reports/
│   └── 01-contrato-e-esqueleto.md
├── src/
│   └── terminal_session_manager/
│       ├── __init__.py
│       ├── errors.py
│       ├── main.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── credential.py
│       │   ├── device.py
│       │   ├── event.py
│       │   ├── job.py
│       │   └── session.py
│       └── interfaces/
│           ├── __init__.py
│           ├── credentials.py
│           ├── device.py
│           ├── persistence.py
│           └── transport.py
└── tests/
    ├── test_contracts.py
    ├── test_device_and_credential.py
    ├── test_event.py
    ├── test_job.py
    └── test_session.py
```

## Decisões Tomadas
- **Zero runtime dependencies**: O domínio foi construído usando `dataclasses`, `enum.Enum` e `typing.Protocol` da biblioteca padrão do Python (>= 3.11). Isso evita acoplamento acidental e mantém o núcleo extremamente leve.
- **Validação estrita de transições**: `Session.transition_to` e `Job.transition_to` validam qualquer mudança de estado contra tabelas explícitas de transições (`SESSION_TRANSITIONS` e `JOB_TRANSITIONS`), levantando `InvalidStateTransitionError` em violações.
- **Isolamento estrutural de credenciais**: O modelo `CredentialRef` expressamente omite campos de texto puro para segredos. Segredos só são manipulados pelo protocolo interno `CredentialResolver`, garantindo que agentes ou serializadores de API nunca tenham acesso direto a senhas.
- **Ordenação determinística de eventos**: O modelo `Event` implementa `functools.total_ordering` e comparações primariamente pela tupla `(sequence, timestamp)`, viabilizando reconciliação e ordenação direta via `sort()`.

## Requisitos Atendidos
- Inicialização e execução via `uv` -> `uv sync`, `uv run terminal-session-manager` e `uv run python -m terminal_session_manager.main`.
- Estrutura modular pequena -> `models/`, `interfaces/`, `errors.py`, `main.py`.
- Modelos para sessão, job, dispositivo, credencial e evento -> Implementados em `src/terminal_session_manager/models/`.
- Estados válidos de sessão e job -> Enums `SessionStatus` e `JobStatus` com grafos de transição.
- Rejeição de estados inválidos -> Testes parametrizados em `tests/test_session.py` e `tests/test_job.py`.
- Eventos ordenáveis e vinculáveis -> Testes de ordenação de lista e chaves `session_id`/`job_id` em `tests/test_event.py`.
- Interfaces para persistência, transporte, dispositivos e credenciais -> Protocols verificados com implementações mock em `tests/test_contracts.py`.
- Erros de domínio -> `errors.py` com testes em todas as entidades.
- Testes sem rede/recursos externos -> 41 testes unitários em memória executados em 0.14s.
- Documentação no README -> Atualizado com instruções de instalação, comandos de teste e árvore do projeto.

## Testes e Resultados
- `uv run pytest -v`: 41 passed em 0.14s.
  - `tests/test_contracts.py`: 6 testes de conformidade de protocolos (SessionRepository, JobRepository, EventRepository, TerminalTransport, DeviceRepository, CredentialResolver) -> PASSED.
  - `tests/test_device_and_credential.py`: 6 testes de validação, limites de portas, desativação e garantia de não exposição de segredos -> PASSED.
  - `tests/test_event.py`: 5 testes de criação, links com job, validação de tipos e ordenação estrita por sequência e timestamp -> PASSED.
  - `tests/test_job.py`: 12 testes de ciclo de vida, códigos de saída e rejeição de transições ilegais -> PASSED.
  - `tests/test_session.py`: 12 testes de máquina de estados, idempotência e rejeição de transições inválidas -> PASSED.
- `uv run terminal-session-manager --version`: Saída `terminal-session-manager 0.1.0` -> PASSED.
- `uv run python -m terminal_session_manager.main`: Saída com confirmação de esqueleto e contratos carregados -> PASSED.

## Desvios e Limitações
- Conforme exigido para a Etapa 0, não foram implementados subprocessos PTY reais, conectores SSH, drivers SQLite/Postgres nem servidores HTTP/MCP.
- As implementações dos repositórios e transportes nos testes são in-memory mocks criados exclusivamente para validação contratual.

## Riscos e Decisões Pendentes
- **Compatibilidade de PTY no Windows (Etapa 1)**: Em ambientes Windows, a criação de pseudoterminais interativos pode requerer ConPTY (`pywinpty`) ou fallback para subprocess com pipes sem controle de terminal completo; no Linux/macOS, o suporte nativo via `pty`/`termios` é padrão. Será necessário decidir a estratégia de abstração para manter portabilidade.
- **Estratégia de Buffer e Janela de Rolagem**: Na Etapa 1 e 2, o tamanho do buffer de saída do transporte e a persistência em disco devem ter limites de retenção para evitar consumo excessivo de memória.

## Entrada Recomendada para a Próxima Etapa (Etapa 1 — Sessão Local Mínima)
- **Objetivo**: Implementar uma sessão local funcional através de um adaptador de terminal concreto, com criação de processo, leitura, escrita, encerramento limpo e ciclo de vida ativo.
- **Contexto Factual**: Contratos `TerminalTransport`, `Session`, `SessionStatus` e eventos de `stdin`/`stdout`/`stderr` já estão formalizados e validados pela Etapa 0.
- **Restrições**: Sem SSH, sem banco de dados complexo e sem servidor HTTP/MCP ainda; foco exclusivo no ciclo do processo local interativo e canal de I/O.
- **Testes Obrigatórios**: Comandos interativos, leituras parciais, término voluntário de processo, captura de código de saída, erro de comando inexistente e fechamento forçado de sessão.
