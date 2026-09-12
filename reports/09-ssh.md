# Relatório — Etapa 8: Transporte SSH

## Status
concluída

## Entregue
- **Adaptador de Transporte SSH (`SSHTransport` em `src/terminal_session_manager/transports/ssh.py`):**
  - Implementação completa e aderente ao protocolo `TerminalTransport` (`open`, `read`, `read_stderr`, `write`, `resize`, `close`, `is_alive`, `exit_code`).
  - Substituível por injeção: aceita `client_factory` customizável, viabilizando mocks e testes unitários 100% isolados de hardware ou servidores SSH externos.
  - Suporte tanto ao modo interativo de sessão PTY (`client.invoke_shell`) quanto à execução de comandos pontuais (`exec_command`).
  - Threads assíncronas dedicadas para leitura de streams (`STDOUT` e `STDERR`), garantindo compatibilidade com timeouts e drenagem confiável de saídas sem travamento.
- **Autenticação e Resolução de Credenciais:**
  - Suporte transparente a credenciais resolvidas via `DeviceService` e `ProtectedLocalCredentialStore`.
  - Autenticação por senha (`CredentialType.PASSWORD`) e chave privada (`CredentialType.SSH_KEY` — suportando RSA, Ed25519 e ECDSA).
  - Isolamento estrito de segredos: chaves privadas e senhas são decodificadas apenas em memória e **nunca** aparecem em logs, traces, mensagens de erro de autenticação, argumentos de processo ou respostas HTTP/MCP.
- **Verificação Estrita de Host Keys (Host Key Verification):**
  - Por padrão, adota política estrita de rejeição (`paramiko.RejectPolicy`) contra arquivos `known_hosts`.
  - Rejeição segura: nunca aceita silenciosamente hosts desconhecidos em modo de segurança ativado (`strict_host_key_checking=True`).
  - Configuração granular de arquivo `known_hosts` via `config.yml` e variável de ambiente `TSM_SSH_KNOWN_HOSTS`.
- **Integração com `ConnectionMethod.SSH` nos Serviços de Domínio:**
  - **`LocalSession`:** Quando inicializada com dispositivo cujo método de conexão é `ConnectionMethod.SSH` (ou ao receber `device_identifier`), o `SSHTransport` é instanciado automaticamente com os parâmetros resolvidos.
  - **`SessionService`:** Permite criar sessões interativas em máquinas remotas simplesmente informando o `device_identifier` (nickname).
  - **`JobService`:** Executa jobs em dispositivos remotos por nickname ou por herança de sessão, capturando separadamente `stdout` e `stderr`, gravando eventos no SQLite, propagando exit codes remotos e suportando cancelamento e timeout de execução.
- **Configuração Centralizada (`config.yml` e `config.py`):**
  - Seção `ssh` incorporada em `TSMConfig`:
    - `known_hosts_path: str | None = None`
    - `strict_host_key_checking: bool = True`
    - `connect_timeout: float = 10.0`
    - `default_port: int = 22`
  - Sobrescrita determinística por variáveis de ambiente (`TSM_SSH_KNOWN_HOSTS`, `TSM_SSH_STRICT_HOST_KEY_CHECKING`, `TSM_SSH_CONNECT_TIMEOUT`, `TSM_SSH_DEFAULT_PORT`).
  - Validação estrita de portas e timeouts na inicialização.
- **Suíte de Testes Automatizados:**
  - `tests/test_ssh_transport.py`: 9 testes unitários cobrindo ciclo de vida de autenticação (senha e chave RSA), host keys (rejeição estrita e aceitação), timeout de conexão, sanitização de erros sem vazamento de senha, redimensionamento de terminal e modo de comando com código de saída.
  - `tests/test_ssh_session_and_jobs.py`: 5 testes de integração ponta a ponta validando criação de sessão por nickname, mascaramento dinâmico de senha no banco SQLite de eventos (`[REDACTED]`), submissão e espera de job remoto, código de saída não-zero e cancelamento seguro.
  - Total de **133 testes automatizados** passando com sucesso via `uv run pytest`.

## Biblioteca Escolhida
- **`paramiko>=3.5.0` (versão 5.0.0 instalada via `uv add paramiko`)**:
  - **Justificativa da Decisão:**
    - Biblioteca padrão de fato no ecossistema Python para o protocolo SSHv2.
    - Implementação madura, ativamente mantida e auditada pela comunidade.
    - Pura em Python com aceleração criptográfica via `cryptography` e `pynacl` (já incluídos no build).
    - Alinhamento perfeito com a arquitetura multithreaded síncrona do TSM (`TerminalTransport`, `ThreadingHTTPServer` e filas de eventos).
    - Evita a necessidade de implementar manualmente ou reinventar o protocolo criptográfico de rede SSH.

## Configuração
Trecho adicionado ao `config.yml`:
```yaml
ssh:
  # Caminho do arquivo known_hosts para verificação estrita de host keys
  known_hosts_path: ""
  # Modo seguro: rejeita conexões para hosts cuja chave pública não seja previamente conhecida
  strict_host_key_checking: true
  # Timeout de conexão SSH em segundos
  connect_timeout: 10.0
  # Porta padrão para conexões SSH
  default_port: 22
```

Variáveis de ambiente suportadas:
- `TSM_SSH_KNOWN_HOSTS`: caminho para arquivo de chaves de host autorizadas.
- `TSM_SSH_STRICT_HOST_KEY_CHECKING`: `true` ou `false` (default: `true`).
- `TSM_SSH_CONNECT_TIMEOUT`: timeout de conexão em segundos (float).
- `TSM_SSH_DEFAULT_PORT`: porta TCP padrão para conexões SSH (int, 1..65535).

## Testes e Resultados
Execução completa via `uv run pytest -v`:
- `tests/test_ssh_transport.py`:
  - `test_ssh_transport_conforms_to_terminal_transport_protocol` -> PASSED
  - `test_ssh_transport_password_auth_lifecycle` -> PASSED
  - `test_ssh_transport_private_key_auth` -> PASSED
  - `test_ssh_transport_strict_host_key_checking_rejects_by_default` -> PASSED
  - `test_ssh_transport_auth_failure_error_handling_masks_secrets` -> PASSED
  - `test_ssh_transport_host_key_verification_failure` -> PASSED
  - `test_ssh_transport_timeout_handling` -> PASSED
  - `test_ssh_transport_command_exec_and_exit_code` -> PASSED
  - `test_ssh_transport_write_when_not_open_raises_error` -> PASSED
- `tests/test_ssh_session_and_jobs.py`:
  - `test_session_creation_with_ssh_device_by_nickname` -> PASSED
  - `test_job_execution_on_ssh_device_by_nickname` -> PASSED
  - `test_job_execution_ssh_failure_non_zero_exit_code` -> PASSED
  - `test_job_execution_ssh_cancellation` -> PASSED
  - `test_ssh_device_resolution_errors` -> PASSED
- Suítes anteriores (API, persistência, jobs, sessões, contratos, configuração, endurecimento, MCP): 119 testes PASSED.
- **Resultado Geral: 133 passed em 26.71s (100% de sucesso).**

## Critérios Verificados
- [x] `SSHTransport` implementado e substituível por injeção (`client_factory`).
- [x] Suporte a host, porta, usuário, senha e chave privada (RSA, Ed25519, ECDSA) conforme a credencial resolvida.
- [x] Seleção automática de transporte orientada por `ConnectionMethod.SSH`.
- [x] Criação de sessões e execução de jobs em dispositivos remotos por nickname.
- [x] Leitura, escrita, redimensionamento, fechamento, timeout e código de saída totalmente compatíveis com `TerminalTransport`.
- [x] Validação estrita de host keys e configuração explícita de `known_hosts` sem aceitação silenciosa de hosts desconhecidos em modo seguro.
- [x] Nenhum segredo exposto em processos, eventos, logs, erros de autenticação ou respostas API/MCP.
- [x] Tratamento de autenticação recusada, host desconhecido, timeout, desconexão e encerramento com código não-zero.
- [x] Testes unitários e de integração mockados, autossuficientes e sem dependência de hardware real.
- [x] `config.yml`, `config.py` e `README.md` atualizados.

## Limitações
- Algoritmos legados (como chaves DSA/DSS) foram descontinuados no Paramiko 5+ por razões criptográficas e de segurança modernas; recomenda-se utilizar chaves Ed25519, RSA (>=2048 bits) ou ECDSA.
- O SSHTransport utiliza canais individuais de sessão por execução; para cenários de alta concorrência com centenas de comandos por segundo na mesma máquina remota, futuras versões poderão incorporar pools de conexões multiplexadas.

## Recomendação de Manutenção
- Manter `strict_host_key_checking: true` em ambientes produtivos para impedir ataques de man-in-the-middle (MITM).
- Em servidores de produção, apontar `known_hosts_path` para um arquivo mantido por ferramenta de configuração (Ansible, Puppet, Terraform) ou provisionado no diretório `.tsm/known_hosts`.
- Atualizar regularmente o grafo de conhecimento com `graphify update .` para rastrear as novas entidades e fluxos.
