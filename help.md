# Terminal Session Manager — Guia de Uso (help.md)

O **Terminal Session Manager (TSM)** é uma arquitetura modular, minimalista e orientada a agentes para gerenciar sessões interativas de terminal, jobs assíncronos em segundo plano, streaming de eventos e catálogo de dispositivos com resolução segura de credenciais.

---

## 1. Instalação e Requisitos

### Requisitos
- **Python**: Versão `>= 3.11`
- **uv**: Gerenciador de dependências e ambientes virtuais ([documentação do uv](https://docs.astral.sh/uv/))

### Clonando e Sincronizando
```bash
git clone git@github.com:danieldoalto/TerminalPersistente.git
cd TerminalPersistente

# Instala todas as dependências no ambiente virtual .venv
uv sync
```

---

## 2. Configuração Centralizada

O sistema utiliza um arquivo central [`config.yml`](config.yml) carregado automaticamente do diretório raiz do projeto ou indicado via CLI/variável de ambiente.

### Estrutura do `config.yml`

```yaml
server:
  host: "127.0.0.1"       # Escuta estritamente local por padrão
  port: 8000              # Porta TCP da API HTTP
  api_token: ""           # Token opcional; se preenchido ativa autenticação obrigatória

storage:
  db_path: ".tsm/tsm.db"  # Caminho do banco SQLite durável

security:
  require_auth: false     # Se true, exige Bearer token ou X-API-Key

sessions:
  default_read_timeout: 0.5   # Timeout de leitura em segundos
  max_read_bytes: 4096        # Limite máximo de bytes lidos por chamada
  cleanup_on_shutdown: true   # Encerra processos ativos ao desligar

jobs:
  default_timeout: 60.0       # Timeout padrão de jobs assíncronos
  recover_orphaned_on_start: true # Marca jobs interrompidos como FAILED ao reiniciar

history:
  default_event_limit: 50     # Quantidade padrão de eventos retornados
  max_event_limit: 200        # Limite teto para paginação por cursor
```

### Sobrescrita por Variáveis de Ambiente

Qualquer valor do YAML pode ser sobrescrito em tempo de execução com variáveis de ambiente prefixadas por `TSM_`:

| Variável | Descrição | Exemplo |
| :--- | :--- | :--- |
| `TSM_CONFIG_PATH` | Caminho de um arquivo de configuração customizado | `export TSM_CONFIG_PATH=/etc/tsm/prod.yml` |
| `TSM_SERVER_HOST` | Endereço IP de escuta da API HTTP | `export TSM_SERVER_HOST=0.0.0.0` |
| `TSM_SERVER_PORT` | Porta TCP da API HTTP | `export TSM_SERVER_PORT=8080` |
| `TSM_API_TOKEN` | Token de autenticação da API HTTP | `export TSM_API_TOKEN=meu-token-forte` |
| `TSM_REQUIRE_AUTH`| Força a exigência de autenticação (`true` ou `false`) | `export TSM_REQUIRE_AUTH=true` |
| `TSM_DB_PATH` | Caminho do arquivo de banco de dados SQLite | `export TSM_DB_PATH=/var/lib/tsm/tsm.db` |
| `TSM_MASTER_KEY` | Chave mestra de criptografia das credenciais | `export TSM_MASTER_KEY=chave-secreta-32bytes` |

> [!IMPORTANT]
> **Segurança de Credenciais:** Nunca salve senhas ou tokens em texto puro no arquivo `config.yml`. Chaves mestras e tokens sensíveis devem sempre ser injetados via variáveis de ambiente (`TSM_MASTER_KEY` e `TSM_API_TOKEN`).

---

## 3. Comandos CLI

O executável CLI `terminal-session-manager` oferece controle direto sobre validação, execução e inspeção:

### 3.1. Validar a Configuração
Verifica se as portas, diretórios, limites e parâmetros de segurança estão corretos antes de iniciar o serviço:
```bash
uv run terminal-session-manager validate
```
Para testar um arquivo alternativo:
```bash
uv run terminal-session-manager validate --config caminho/para/config.yml
```

### 3.2. Exibir Status
Exibe a versão e um resumo do estado operacional:
```bash
uv run terminal-session-manager status
```

### 3.3. Iniciar a API HTTP REST
Inicia o servidor HTTP multithread com documentação Swagger interativa:
```bash
uv run terminal-session-manager api
```
Para encerrar, pressione `Ctrl + C` (o encerramento gracioso finaliza os processos ativos com segurança).

### 3.4. Iniciar o Servidor MCP (Model Context Protocol)
Inicia o servidor MCP via transporte padrão `stdio` para agentes de IA:
```bash
uv run terminal-session-manager mcp
# ou diretamente pelo atalho:
uv run terminal-session-manager-mcp
```

### 3.5. Executar os Testes Automatizados
Executa a suíte completa de 119 testes:
```bash
uv run pytest -v
```

---

## 4. Usando a API HTTP

Quando a API estiver em execução (`uv run terminal-session-manager api`), você pode acessar:

- **Swagger UI (Documentação Interativa):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **OpenAPI Schema (JSON puro):** [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

### Exemplos Práticos via `curl`

#### 1. Criar uma Nova Sessão
Para abrir uma sessão no terminal local nativo da máquina, basta informar o nome (o campo `device_identifier` é opcional e, se omitido, inicia o shell local diretamente):
```bash
# Sessão no terminal local nativo (sem precisar cadastrar dispositivo)
curl -X POST http://127.0.0.1:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "sessao-trabalho"}'

# Ou sessão em dispositivo SSH remoto cadastrado
curl -X POST http://127.0.0.1:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"name": "sessao-remota", "device_identifier": "maclinux"}'
```
*Resposta:*
```json
{
  "id": "7bf3a2e1-4567-4890-a1b2-c3d4e5f60718",
  "name": "sessao-trabalho",
  "status": "running",
  "device_id": null,
  "created_at": "2026-09-11T22:00:00+00:00",
  "updated_at": "2026-09-11T22:00:00+00:00",
  "closed_at": null,
  "metadata": {}
}
```

#### 2. Escrever um Comando na Sessão
```bash
curl -X POST http://127.0.0.1:8000/sessions/7bf3a2e1-4567-4890-a1b2-c3d4e5f60718/write \
  -H "Content-Type: application/json" \
  -d '{"data": "echo Olá Mundo!\n"}'
```

#### 3. Ler a Saída do Terminal
```bash
curl -X POST http://127.0.0.1:8000/sessions/7bf3a2e1-4567-4890-a1b2-c3d4e5f60718/read \
  -H "Content-Type: application/json" \
  -d '{"timeout": 1.0, "max_bytes": 4096}'
```

#### 4. Submeter um Job Assíncrono em Segundo Plano
```bash
curl -X POST http://127.0.0.1:8000/sessions/7bf3a2e1-4567-4890-a1b2-c3d4e5f60718/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "command": "python -c \"import time; time.sleep(5); print(\\\"Job Concluído\\\")\"",
    "timeout": 30.0
  }'
```

#### 5. Consultar Status do Job
```bash
curl -X GET http://127.0.0.1:8000/jobs/<JOB_ID>
```

#### 6. Aguardar Conclusão do Job
```bash
curl -X POST http://127.0.0.1:8000/jobs/<JOB_ID>/wait \
  -H "Content-Type: application/json" \
  -d '{"timeout": 10.0}'
```

#### 7. Cadastrar um Dispositivo no Catálogo
```bash
curl -X POST http://127.0.0.1:8000/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "roteador-borda",
    "host": "192.168.1.1",
    "port": 22,
    "device_type": "router",
    "connection_method": "ssh",
    "default_user": "admin"
  }'
```

#### 8. Resolver Conexão por Nickname (Sem Exposição de Segredos)
```bash
curl -X GET http://127.0.0.1:8000/devices/roteador-borda/resolve
```
*Resposta:*
```json
{
  "device_id": "99f8c12a-...",
  "device_name": "roteador-borda",
  "host": "192.168.1.1",
  "port": 22,
  "connection_method": "ssh",
  "default_user": "admin",
  "has_credential": true,
  "credential_ref_id": "c1f7b...",
  "options": {}
}
```

#### 9. Transferência de Arquivos via SCP (Upload e Download)
```bash
# Upload de arquivo local para o dispositivo remoto
curl -X POST http://127.0.0.1:8000/scp/upload \
  -H "Content-Type: application/json" \
  -d '{
    "device": "roteador-borda",
    "local_path": "C:/backups/config.boot",
    "remote_path": "/etc/config.boot"
  }'

# Download de arquivo remoto para o computador local
curl -X POST http://127.0.0.1:8000/scp/download \
  -H "Content-Type: application/json" \
  -d '{
    "device": "roteador-borda",
    "remote_path": "/var/log/messages",
    "local_path": "C:/logs/router_messages.log"
  }'
```
*A transferência é disparada como um `Job` assíncrono em segundo plano (HTTP 202).*

---

## 5. Usando com Agentes via MCP

O Terminal Session Manager expõe 17 ferramentas nativas via protocolo **Model Context Protocol (MCP)**, permitindo que agentes LLM operem terminais e transfiram arquivos com segurança.

### 5.1. Configuração no Claude Desktop

Edite o arquivo de configuração do Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json` no Windows ou `~/.config/Claude/claude_desktop_config.json` no macOS/Linux):

```json
{
  "mcpServers": {
    "terminal-session-manager": {
      "command": "uv",
      "args": [
        "--directory",
        "d:/Projetos/TerminalPersistente",
        "run",
        "terminal-session-manager-mcp"
      ],
      "env": {
        "TSM_DB_PATH": ".tsm/tsm.db"
      }
    }
  }
}
```

### 5.2. Configuração no Cursor / Antigravity

Em `.agents/mcp_config.json`:

```json
{
  "mcpServers": {
    "terminal-session-manager": {
      "command": "uv",
      "args": [
        "--directory",
        "d:/Projetos/TerminalPersistente",
        "run",
        "terminal-session-manager-mcp"
      ]
    }
  }
}
```

### 5.3. Ferramentas Disponíveis no Servidor MCP

| Categoria | Nome da Ferramenta | Descrição |
| :--- | :--- | :--- |
| **Sessões** | `create_session` | Inicia uma nova sessão de terminal persistente |
| | `get_session` | Consulta status e metadados de uma sessão por ID |
| | `list_sessions` | Lista todas as sessões registradas com status atualizado |
| | `write_session` | Envia comandos ou caracteres de entrada para a sessão |
| | `read_session` | Lê saídas da sessão com mascaramento automático |
| | `close_session` | Encerra o processo de transporte da sessão |
| **Histórico** | `get_events` | Consulta paginada por cursor (`since_sequence`, `limit`) |
| **Jobs** | `submit_job` | Dispara execução de comando assíncrono em segundo plano |
| | `get_job` | Consulta status, códigos de retorno, stdout e stderr |
| | `list_jobs` | Lista os jobs vinculados a uma sessão |
| | `wait_job` | Aguarda conclusão ou término por timeout de um job |
| | `cancel_job` | Cancela e encerra o processo de um job em andamento |
| **Dispositivos** | `list_devices` | Lista os dispositivos cadastrados no catálogo |
| | `get_device` | Consulta metadados públicos de um dispositivo por nickname |
| | `resolve_device` | Resolve parâmetros de conexão **sem retornar senhas ao agente** |
| **Arquivos (SCP)** | `scp_upload` | Envia arquivo local para dispositivo remoto como job |
| | `scp_download` | Baixa arquivo de dispositivo remoto para storage local |

---

## 6. Ciclo de Vida e Reconciliação de Falhas

O Terminal Session Manager foi projetado com endurecimento para operar de forma resiliente em ambientes locais ou de produção:

1. **Recuperação de Falhas (Crash Recovery):**
   - Caso o servidor caia ou o processo seja finalizado abruptamente:
     - Na próxima inicialização, jobs que estavam em execução são detectados e marcados como `FAILED`, prevenindo bloqueios eternos.
     - Sessões que estavam ativas são marcadas como `LOST`, registrando um evento no histórico para auditoria.
2. **Encerramento Limpo (Graceful Shutdown):**
   - Ao receber sinal de interrupção (`SIGINT`, `SIGTERM` ou `app.shutdown()`):
     - Todas as sessões ativas são finalizadas e seus canais fechados.
     - Processos filhos em segundo plano são terminados.
     - Conexões com o banco de dados SQLite são fechadas de forma determinística.
3. **Proteção de Credenciais em Repouso:**
   - Senhas e chaves são cifradas com PBKDF2-HMAC-SHA256 e autenticadas via HMAC-SHA256 no SQLite.
   - Suporte à rotação atômica da chave mestra através do método `rotate_master_key()` sem perda de dados.

---

## 7. Solução de Problemas (FAQ)

### A porta 8000 já está em uso?
Altere a porta facilmente via variável de ambiente:
```bash
export TSM_SERVER_PORT=8888
uv run terminal-session-manager api
```
Ou edite a chave `server.port` em `config.yml`.

### Como ativar autenticação local por token?
Defina um token no ambiente e ative a flag de autenticação:
```bash
export TSM_API_TOKEN="meu-segredo-de-acesso"
export TSM_REQUIRE_AUTH=true
uv run terminal-session-manager api
```
Todas as requisições (exceto `/docs` e `/openapi.json`) passarão a exigir o cabeçalho:
```bash
curl -H "Authorization: Bearer meu-segredo-de-acesso" http://127.0.0.1:8000/sessions
```

### Onde os dados ficam gravados?
Por padrão, o banco de dados SQLite é mantido em `.tsm/tsm.db`. Ele pode ser movido ou configurado via `TSM_DB_PATH`.

### Como gerenciar dispositivos, credenciais e transferências SCP de forma interativa?
Use o utilitário interativo para cadastrar, listar, editar, testar conexão, gerar chaves SSH, transferir arquivos ou apagar dispositivos:
```bash
uv run python scripts/manage_devices.py
```
O script oferece:
- Cadastro e edição com suporte a senhas protegidas e chaves privadas (Ed25519/RSA);
- Teste de conexão SSH com diagnóstico detalhado em tempo real;
- Gerador de chaves SSH com texto pronto para cópia da chave pública e instruções de instalação;
- **Opção 9: Transferência e teste de arquivos SCP**, permitindo uploads, downloads e um teste rápido de integridade SCP com o host remoto sem precisar escrever código.

### Como transferir arquivos entre o computador local e os dispositivos remotos?
Existem 3 formas seguras e padronizadas no TSM:
1. **Pelo utilitário interativo:** Execute `uv run python scripts/manage_devices.py`, selecione a opção `9` e escolha Upload, Download ou Teste Rápido.
2. **Pela API HTTP REST:** Envie uma requisição `POST /scp/upload` ou `POST /scp/download` informando o nickname do dispositivo (retorna `HTTP 202` com o `Job` assíncrono criado).
3. **Por Agentes Inteligentes via MCP:** O agente invoca a ferramenta `scp_upload` ou `scp_download` informando apenas o nickname do dispositivo (ex: `"maclinux"`), acompanhando o progresso através de `wait_job`. As credenciais e chaves são resolvidas internamente pelo cofre criptografado sem exposição.

### Preciso cadastrar um dispositivo para conectar ao terminal local?
**Não.** O terminal local é o comportamento nativo padrão do TSM. Sempre que você omitir o parâmetro `device_identifier` (ou passar `null`/`None`), o TSM inicia diretamente o shell da máquina host (`cmd.exe` no Windows ou `/bin/sh` no Linux/macOS) através do `LocalProcessTransport`. O catálogo de dispositivos é necessário apenas para máquinas remotas acessadas via SSH (ou caso queira rotular organizacionamente a máquina local como um dispositivo com método `local`).



