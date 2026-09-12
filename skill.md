---
name: terminal-session-manager
description: Operates persistent terminal sessions, asynchronous jobs, event history, and remote SSH devices via the Terminal Session Manager FastMCP server without leaking credentials.
---

# Terminal Session Manager (TSM) — MCP Agent Skill

This skill guides AI agents on how to effectively, safely, and idiomatically interact with the **Terminal Session Manager FastMCP Server**.

---

## 1. Overview & Core Philosophy

The Terminal Session Manager (TSM) provides persistent execution environments for agents:
- **Persistence Across Turns**: Sessions continue running even after your prompt turn ends or if you disconnect.
- **Background Jobs**: Long-running commands run in worker threads decoupled from your immediate response loop.
- **Strict Secret Isolation**: Registered devices (local and remote SSH) are operated **solely by their nickname** (e.g., `maclinux`, `srv-prod`). You **never** need, see, or handle passwords or private keys. Any echoed secrets are proactively redacted (`[REDACTED]`) in the event store.
- **Ordered Event History**: All inputs, outputs, errors, and state transitions are stored sequentially and can be replayed or paginated via sequence cursors.

---

## 2. Server Configuration

To connect this MCP server to your agent client:

### Cursor / Antigravity (`.agents/mcp_config.json` or global config)
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

### Claude Desktop (`claude_desktop_config.json`)
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

---

## 3. Tool Reference

The server exposes 17 focused tools across 5 categories:

### 3.1. Devices (Inventory & Remote SSH)
Use devices to run sessions or jobs on remote machines via SSH or locally.

- **`list_devices(only_active=True)`**: Returns list of registered devices.
  - *Response*: `[{"id": "...", "name": "maclinux", "host": "192.168.10.123", "port": 22, "default_user": "daniel", "connection_method": "ssh", "device_type": "server", "is_active": true}]`
- **`get_device(name_or_id="maclinux")`**: Retrieves metadata for a specific device by nickname or UUID.
- **`resolve_device(name_or_id="maclinux")`**: Verifies if the device is active and whether credentials are validly configured in memory.
  - *Response*: `{"device_id": "...", "device_name": "maclinux", "has_credential": true, ...}` *(Never returns the plaintext password)*.

### 3.2. Sessions (Interactive Terminal PTY)
Use sessions for interactive command lines or multi-step shell dialogues.

- **`create_session(name="default", device_identifier=None)`**: Creates and starts a terminal session.
  - To connect locally: omit `device_identifier`.
  - To connect to a remote host via SSH: pass the nickname (e.g. `device_identifier="maclinux"`).
  - *Response*: `{"id": "session-uuid", "name": "...", "status": "running", "device_id": "..."}`
- **`get_session(session_id)`**: Checks current status (`running`, `completed`, `failed`, `closed`, `lost`).
- **`list_sessions()`**: Lists all active and past sessions.
- **`write_session(session_id, data, is_sensitive=False)`**: Writes input/commands to the terminal stdin.
  - Always append `\n` if executing a line command (e.g. `data="ls -la\n"`).
  - If typing sensitive tokens, pass `is_sensitive=True` to enforce redaction.
- **`read_session(session_id, max_bytes=4096, timeout=0.5)`**: Reads available stdout stream.
- **`close_session(session_id)`**: Closes the terminal and marks the session as `closed`.

### 3.3. Jobs (Asynchronous Background Execution)
**Recommended for discrete commands, builds, scripts, and monitoring.**

- **`submit_job(session_id, command, inputs=None, timeout=None)`**:
  - Submits a job to run in the background.
  - If `session_id` is bound to a remote SSH device (like `maclinux`), the command executes on the remote machine via SSH!
  - `command`: String (e.g. `"df -h"`) or array of args (e.g. `["git", "status"]`).
  - *Response*: `{"id": "job-uuid", "status": "created", "command": "..."}`
- **`get_job(job_id)`**: Checks status (`created`, `running`, `completed`, `failed`, `cancelled`, `timeout`), `exit_code`, `stdout`, `stderr`, and `failure_reason`.
- **`wait_job(job_id, timeout=10.0)`**: Synchronously blocks until the job finishes or until timeout is reached.
- **`cancel_job(job_id)`**: Immediately terminates the underlying process or SSH channel.
- **`list_jobs(session_id)`**: Lists all jobs executed inside a session.

### 3.4. History & Events
- **`get_events(session_id, since_sequence=0, limit=50)`**:
  - Reads incremental history of the session.
  - Events have: `sequence`, `timestamp`, `event_type` (`stdin`, `stdout`, `stderr`, `state_change`), `payload`, `is_masked`.
  - Store the highest `sequence` to query only newer events in subsequent calls: `since_sequence = last_sequence + 1`.

### 3.5. File Transfers (SCP)
**Used for transferring files to and from remote SSH devices.**

- **`scp_upload(device, local_path, remote_path, session_id=None, timeout=30.0)`**:
  - Uploads a local file to the remote device identified by nickname (e.g. `maclinux`).
  - Runs as an asynchronous background `Job` with progress tracking and event logging.
  - Returns created Job metadata (`id`, `status`, `metadata`).
  - Use `wait_job(job_id)` or `get_job(job_id)` to monitor completion.
- **`scp_download(device, remote_path, local_path, session_id=None, timeout=30.0)`**:
  - Downloads a remote file from an SSH device to local storage.
  - Runs as an asynchronous background `Job`.
  - Returns created Job metadata (`id`, `status`, `metadata`).
  - Use `wait_job(job_id)` or `get_job(job_id)` to monitor completion.

---

## 4. Standard Agent Interaction Patterns

### Pattern A: Execute a Remote Command on a Named Device (Most Common)
When the user asks you to check or run something on a remote server (e.g., `maclinux`):

1. **Find or create a session for the device:**
   ```json
   call create_session(name="remote-work", device_identifier="maclinux")
   // -> returns session_id: "3b29c9e1-..."
   ```
2. **Submit the command as a job:**
   ```json
   call submit_job(session_id="3b29c9e1-...", command="df -h && uptime")
   // -> returns job_id: "8f71aa24-..."
   ```
3. **Wait for completion:**
   ```json
   call wait_job(job_id="8f71aa24-...", timeout=10.0)
   // -> returns job with status="completed", exit_code=0, stdout="...", stderr="..."
   ```
4. **Inspect output:**
   Read `job.stdout` and summarize the results to the user.

---

### Pattern B: Interactive Multi-Step Session
When you need an ongoing shell session (e.g., entering a subshell, running Python REPL, or chained commands where environment variables must persist):

1. **Create session:**
   ```json
   call create_session(name="interactive-shell")
   ```
2. **Send command:**
   ```json
   call write_session(session_id="...", data="cd /var/log && pwd\n")
   ```
3. **Read output:**
   ```json
   call read_session(session_id="...", timeout=1.0)
   ```
4. **Repeat steps 2 and 3 as needed.**
5. **Clean up when done:**
   ```json
   call close_session(session_id="...")
   ```

---

### Pattern C: Monitoring Long-Running Tasks Without Blocking
If a job takes minutes (e.g., Docker build, large download):

1. `submit_job(session_id="...", command="make build", timeout=300.0)`
2. Instead of calling `wait_job` with 300s, poll periodically or inform the user:
   - Call `get_job(job_id="...")` to check if `status == "running"`.
   - Call `get_events(session_id="...", since_sequence=...)` to stream partial build logs to the user.
3. If user requests cancellation:
   - Call `cancel_job(job_id="...")`.

---

### Pattern D: Transfer Files (Upload / Download via SCP)
When the user asks to send or fetch a file from a remote device:

1. **Upload local file to remote host:**
   ```json
   call scp_upload(device="maclinux", local_path="C:/data/config.yml", remote_path="/etc/app/config.yml")
   // -> returns job with id: "abc-..."
   call wait_job(job_id="abc-...", timeout=30.0)
   ```
2. **Download remote file to local host:**
   ```json
   call scp_download(device="maclinux", remote_path="/var/log/syslog", local_path="C:/logs/remote_syslog.txt")
   call wait_job(job_id="def-...", timeout=30.0)
   ```

---

## 5. Security & Invariants for Agents

- **NEVER Ask the User for Passwords**: If a device is registered (e.g., `maclinux`), TSM resolves credentials from the encrypted local vault automatically.
- **Do Not Attempt to Extract Secrets**: Tools like `resolve_device` or `get_device` intentionally do not output passwords or private keys. Do not construct commands to dump the vault table.
- **Failures are Explicit**:
  - If a device is unknown: `ToolError: Device 'xyz' not found`.
  - If a device is deactivated: `ToolError: Device 'xyz' is deactivated`.
  - If SSH auth fails or host key is rejected: Job status transitions to `FAILED` with `failure_reason` explaining the condition without leaking credential values.
