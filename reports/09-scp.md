# Relatório — Etapa 9: Transferência SCP

## Status
concluída

## Entregue
- **Serviço Modular de Transferência (`SCPService` em `src/terminal_session_manager/services/scp_service.py`):**
  - Implementação dedicada e desacoplada do contrato `TerminalTransport`, respeitando o princípio de responsabilidade única (SRP) para transferências de arquivos com semântica de cópia segura.
  - Suporte completo às operações de `upload` (máquina local -> dispositivo remoto) e `download` (dispositivo remoto -> máquina local).
  - Execução assíncrona orientada a `Job`: cada transferência dispara uma thread em segundo plano, registrando status contínuo (`created` -> `running` -> `completed` / `failed` / `cancelled` / `timeout`), exit code, bytes transferidos e tempo de execução.
  - Rastreabilidade e auditoria: emite eventos sequenciados atômicos no `EventRepository` (`STATE_CHANGE`, `STDOUT`, `STDERR`), viabilizando inspeção incremental via cursores de eventos.
  - Cancelamento em voo (`cancel_transfer`): fecha imediatamente sockets e canais SSH, persistindo estado `JobStatus.CANCELLED` com exit code `130`.
  - Controle de timeout: suporte a timeouts configuráveis de conexão e transferência, com encerramento gracioso e marcação determinística como `JobStatus.TIMEOUT`.
  - Substituível por injeção: aceita `client_factory` e `scp_factory` customizáveis, viabilizando testes unitários e de integração 100% isolados de hardware ou servidores SSH externos.
- **Autenticação e Resolução Segura de Dispositivos:**
  - Resolução por nickname ou UUID via `DeviceService.resolve_connection(name_or_id)`.
  - Rejeição imediata com exceções de domínio tipadas:
    - `DeviceNotFoundError`: quando o dispositivo não existe no catálogo;
    - `DeviceInactiveError`: quando o dispositivo está desativado;
    - `ValidationError`: quando o método de conexão não for `ConnectionMethod.SSH`.
  - Suporte a credenciais em repouso protegidas por cofre criptográfico (`CredentialType.PASSWORD` e `CredentialType.SSH_KEY` com RSA, Ed25519 e ECDSA).
  - Isolamento estrito de segredos: chaves e senhas são decodificadas apenas em memória volátil e **nunca** aparecem em logs, mensagens de erro, eventos ou respostas HTTP/MCP.
  - Mascaramento pró-ativo: qualquer erro de autenticação ou socket que contenha tokens de segredo tem esses valores substituídos automaticamente por `[REDACTED]`.
- **Validação de Caminhos e Destinos:**
  - Upload: valida que o arquivo local existe e é um arquivo regular legível antes de despachar a thread.
  - Download: valida que o diretório de destino local existe e é gravável.
  - Validação de integridade do caminho remoto para impedir injeções ou quebras de comando.
- **Integração na Aplicação Central (`TSMApplication` em `src/terminal_session_manager/app.py`):**
  - Instanciação de `self.scp_service` unificando `device_service`, `job_repo`, `event_repo`, `session_repo` e `ssh_config`.
  - Vinculação com `job_service.scp_service` para que `job_service.cancel_job` também interrompa transferências SCP em andamento.
- **Exposição via API HTTP REST (`src/terminal_session_manager/api/handler.py` e `openapi.py`):**
  - `POST /scp/upload`: Envio assíncrono de arquivo local para o dispositivo remoto (retorna HTTP 202 com Job).
  - `POST /scp/download`: Baixa de arquivo do dispositivo remoto para o computador local (retorna HTTP 202 com Job).
  - Cancelamento e consulta reutilizam a infraestrutura existente (`GET /jobs/{id}`, `POST /jobs/{id}/cancel`, `POST /jobs/{id}/wait`, `GET /sessions/{id}/events`).
  - Documentação interativa OpenAPI 3.0.3 e Swagger UI em `/docs` atualizadas com schemas e tag `SCP`.
- **Exposição via Servidor FastMCP (`src/terminal_session_manager/mcp/server.py`):**
  - Ferramenta `scp_upload(device, local_path, remote_path, session_id=None, timeout=30.0)`.
  - Ferramenta `scp_download(device, remote_path, local_path, session_id=None, timeout=30.0)`.
  - Permite a agentes de IA manipular arquivos em nós remotos indicando apenas o nickname do dispositivo, sem tocar em senhas.
- **Documentação de Agente e Ajuda:**
  - `skill.md` e `.agents/skills/terminal-session-manager/SKILL.md` atualizados com referência detalhada das ferramentas e **Pattern D: Transfer Files (Upload / Download via SCP)**.
  - `help.md` e `README.md` atualizados com exemplos práticos via `curl` e tabela atualizada de 17 ferramentas MCP.

---

## Biblioteca Escolhida
- **`scp>=0.15.0` (versão 0.16.1)**:
  - Adicionada ao `pyproject.toml` e instalada via `uv`.
  - Biblioteca Python padrão e madura que implementa o protocolo SCP1 sobre canais Paramiko (`paramiko.Transport`).
  - Pure Python, sem dependências nativas C/C++, compatível com Linux, Windows e macOS.
  - Suporta callbacks de progresso (`sent`, `size`) e sanitização de nomes de arquivos.

---

## Decisões de Arquitetura

1. **Separação entre Terminal e Transferência de Arquivos:**
   - O contrato `TerminalTransport` é estritamente voltado a streams interativos, PTY, controle de terminal VT100 e redimensionamento de janelas.
   - Forçar transferências de arquivos dentro de `TerminalTransport` causaria poluição de abstração e acoplamento inadequado. O `SCPService` isola o protocolo de cópia de arquivos mantendo o reuso limpo de conexões SSH e credenciais.
2. **Transferências Modeladas como `Job`:**
   - A operação de cópia de arquivo é assíncrona por natureza e pode demorar dependendo da largura de banda e tamanho do arquivo.
   - Tratar a transferência como um `Job` permitiu reaproveitar 100% da infraestrutura de polling, espera (`wait_job`), cancelamento (`cancel_job`), histórico (`get_events`) e recuperação de falhas sem escrever código duplicado.
3. **Cancelamento Limpo e Desacoplado:**
   - Ao cancelar uma transferência, a flag de cancelamento é registrada e o socket/canal Paramiko é fechado explicitamente, garantindo que transferências travadas na rede sejam abortadas em milissegundos.

---

## Testes Automatizados

Dois novos módulos de teste dedicados foram implementados, totalizando **17 testes de SCP**:

1. **`tests/test_scp_service.py` (13 testes):**
   - `test_scp_upload_success`: Upload de arquivo com validação de bytes transferidos e eventos de auditoria;
   - `test_scp_download_success`: Download de arquivo remoto com criação do arquivo local;
   - `test_scp_device_nickname_resolution`: Resolução correta por nickname e vinculação a `device_id`;
   - `test_scp_upload_file_not_found`: Validação de arquivo local inexistente antes de iniciar thread;
   - `test_scp_download_invalid_destination_dir`: Validação de diretório de destino local inexistente;
   - `test_scp_inactive_device`: Rejeição com `DeviceInactiveError`;
   - `test_scp_non_existent_device`: Rejeição com `DeviceNotFoundError`;
   - `test_scp_non_ssh_device`: Rejeição com `ValidationError` quando o dispositivo não é SSH;
   - `test_scp_auth_failure_masks_secret`: Garantia absoluta de mascaramento de senhas (`[REDACTED]`) em `failure_reason`, `stderr` e eventos;
   - `test_scp_transfer_timeout`: Timeout de transferência e transição para `JobStatus.TIMEOUT` com exit code 124;
   - `test_scp_cancel_transfer`: Cancelamento limpo em andamento com transição para `JobStatus.CANCELLED` com exit code 130;
   - `test_scp_concurrency`: Múltiplas transferências em paralelo em background threads distintas;
   - `test_scp_orphan_recovery`: Recuperação de transferências órfãs interrompidas por queda de serviço como `FAILED`.
2. **`tests/test_api_scp.py` (4 testes):**
   - `test_api_scp_upload`: Endpoint `POST /scp/upload` retornando 202 Accepted sem vazar credenciais;
   - `test_api_scp_download`: Endpoint `POST /scp/download` retornando 202 Accepted;
   - `test_api_scp_validations`: Validações de payload e arquivos ausentes retornando HTTP 400;
   - `test_mcp_scp_tools_registered_and_callable`: Registro e invocação das ferramentas `scp_upload` e `scp_download` via cliente FastMCP.

### Resultado da Suíte Completa:
```bash
uv run --no-sync pytest
============================ 150 passed in 35.86s =============================
```

---

## Limitações Conhecidas
- O protocolo SCP clássico realiza transferência linear de arquivos individuais. Para transferência de árvores de diretórios com milhares de arquivos pequenos de forma mais rápida, transferências via SFTP ou compressão prévia em `.tar.gz` antes do upload continuam sendo a prática recomendada.
- O cancelamento depende do fechamento do socket subjacente; em caso de redes físicas com perda de pacotes, a notificação de encerramento pode levar alguns milissegundos até a propagação pelo sistema operacional.

---

## Entrada Recomendada para a Próxima Etapa
- O catálogo de dispositivos, cofre protegido de credenciais, sessões interativas, jobs remotos, histórico auditável de eventos e transferência de arquivos via SCP formam uma base coesa e completa para operação de servidores remotos por agentes autônomos.
- Próximos passos recomendados:
  - Adição de suporte a multiplexação de canais SSH (ControlMaster / session reuse) para diminuir latência de conexão em dispositivos que recebem múltiplos comandos consecutivos;
  - Empacotamento para distribuição ou containerização (Docker) de produção.
