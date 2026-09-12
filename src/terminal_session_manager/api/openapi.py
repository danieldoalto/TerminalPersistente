"""OpenAPI 3.0 specification and Swagger UI HTML generator for Terminal Session Manager."""

from __future__ import annotations

from typing import Any


def get_openapi_spec() -> dict[str, Any]:
    """Generates the OpenAPI 3.0.3 schema for Terminal Session Manager HTTP API."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Terminal Session Manager API",
            "version": "0.1.0",
            "description": (
                "Minimalist, persistent, agent-oriented terminal session manager. "
                "Supports long-running interactive sessions, asynchronous jobs, "
                "cursor-paginated event history, and safe device resolution without exposing secrets."
            ),
        },
        "servers": [
            {"url": "/", "description": "Local API Server"},
        ],
        "tags": [
            {"name": "Sessions", "description": "Terminal session lifecycle and interactive I/O"},
            {"name": "Events", "description": "Cursor-paginated historical event stream"},
            {"name": "Jobs", "description": "Asynchronous background command execution"},
            {"name": "Devices", "description": "Device inventory and safe connection resolution"},
            {"name": "SCP", "description": "Secure file copy transfers to and from remote devices"},
            {"name": "Documentation", "description": "API discovery and documentation"},
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "description": "Optional local API token passed via 'Authorization: Bearer <token>'",
                },
                "apiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "Optional local API token passed via 'X-API-Key: <token>'",
                },
            },
            "schemas": {
                "ErrorResponse": {
                    "type": "object",
                    "required": ["error", "message", "status_code"],
                    "properties": {
                        "error": {"type": "string", "example": "ValidationError"},
                        "message": {"type": "string", "example": "Invalid input provided."},
                        "status_code": {"type": "integer", "example": 400},
                    },
                },
                "Session": {
                    "type": "object",
                    "required": ["id", "name", "status", "created_at", "updated_at", "metadata"],
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string", "example": "main-terminal"},
                        "status": {
                            "type": "string",
                            "enum": ["created", "running", "waiting", "completed", "failed", "closed", "lost"],
                        },
                        "device_id": {"type": "string", "nullable": True},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                        "closed_at": {"type": "string", "format": "date-time", "nullable": True},
                        "metadata": {"type": "object"},
                    },
                },
                "SessionCreate": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "default": "default"},
                        "device_identifier": {
                            "type": "string",
                            "description": "Device name or UUID to bind this session to",
                            "nullable": True,
                        },
                        "metadata": {"type": "object", "default": {}},
                    },
                },
                "SessionWriteRequest": {
                    "type": "object",
                    "required": ["data"],
                    "properties": {
                        "data": {"type": "string", "description": "Text or command to write to STDIN"},
                        "is_sensitive": {
                            "type": "boolean",
                            "default": False,
                            "description": "If true, masks input as [REDACTED] in stored history",
                        },
                    },
                },
                "SessionWriteResponse": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "bytes_written": {"type": "integer"},
                    },
                },
                "SessionReadRequest": {
                    "type": "object",
                    "properties": {
                        "max_bytes": {"type": "integer", "default": 4096},
                        "timeout": {"type": "number", "nullable": True, "example": 0.5},
                    },
                },
                "SessionReadResponse": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string"},
                        "data": {"type": "string", "description": "Decoded output text (with secrets redacted)"},
                        "status": {"type": "string"},
                    },
                },
                "Event": {
                    "type": "object",
                    "required": ["id", "sequence", "session_id", "event_type", "payload", "timestamp", "is_masked"],
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "sequence": {"type": "integer", "description": "Monotonically increasing sequence cursor"},
                        "session_id": {"type": "string"},
                        "job_id": {"type": "string", "nullable": True},
                        "event_type": {
                            "type": "string",
                            "enum": ["stdin", "stdout", "stderr", "state_change", "system"],
                        },
                        "payload": {"description": "Event content or state object (secrets redacted)"},
                        "timestamp": {"type": "string", "format": "date-time"},
                        "is_masked": {"type": "boolean"},
                        "metadata": {"type": "object"},
                    },
                },
                "EventList": {
                    "type": "object",
                    "properties": {
                        "items": {"type": "array", "items": {"$ref": "#/components/schemas/Event"}},
                        "count": {"type": "integer"},
                        "since_sequence": {"type": "integer"},
                        "latest_sequence": {"type": "integer"},
                    },
                },
                "Job": {
                    "type": "object",
                    "required": ["id", "session_id", "command", "status", "created_at", "inputs", "stdout", "stderr"],
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "session_id": {"type": "string"},
                        "command": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["created", "running", "completed", "failed", "cancelled", "timeout"],
                        },
                        "device_id": {"type": "string", "nullable": True},
                        "created_at": {"type": "string", "format": "date-time"},
                        "started_at": {"type": "string", "format": "date-time", "nullable": True},
                        "finished_at": {"type": "string", "format": "date-time", "nullable": True},
                        "exit_code": {"type": "integer", "nullable": True},
                        "inputs": {"type": "array", "items": {"type": "string"}},
                        "stdout": {"type": "string"},
                        "stderr": {"type": "string"},
                        "failure_reason": {"type": "string", "nullable": True},
                        "metadata": {"type": "object"},
                    },
                },
                "JobCreate": {
                    "type": "object",
                    "required": ["command"],
                    "properties": {
                        "session_id": {"type": "string", "description": "Required when posting to /jobs"},
                        "command": {"type": "string", "description": "Command string to execute in background"},
                        "inputs": {"type": "array", "items": {"type": "string"}},
                        "timeout": {"type": "number", "nullable": True, "description": "Execution timeout in seconds"},
                        "metadata": {"type": "object"},
                    },
                },
                "JobWait": {
                    "type": "object",
                    "properties": {
                        "timeout": {"type": "number", "default": 10.0, "description": "Wait timeout in seconds"},
                    },
                },
                "Device": {
                    "type": "object",
                    "required": ["id", "name", "host", "port", "device_type", "connection_method", "is_active", "is_deleted"],
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "name": {"type": "string", "example": "bastion-01"},
                        "host": {"type": "string", "example": "192.168.1.1"},
                        "port": {"type": "integer", "default": 22},
                        "device_type": {
                            "type": "string",
                            "enum": ["server", "router", "switch", "container", "workstation", "generic"],
                        },
                        "connection_method": {
                            "type": "string",
                            "enum": ["local", "ssh", "serial", "telnet"],
                        },
                        "default_user": {"type": "string", "nullable": True},
                        "options": {"type": "object"},
                        "credential_ref_id": {"type": "string", "nullable": True},
                        "is_active": {"type": "boolean"},
                        "is_deleted": {"type": "boolean"},
                        "created_at": {"type": "string", "format": "date-time"},
                        "updated_at": {"type": "string", "format": "date-time"},
                    },
                },
                "DeviceCreate": {
                    "type": "object",
                    "required": ["name", "host"],
                    "properties": {
                        "name": {"type": "string", "example": "router-core"},
                        "host": {"type": "string", "example": "10.0.0.1"},
                        "port": {"type": "integer", "default": 22},
                        "device_type": {"type": "string", "default": "server"},
                        "connection_method": {"type": "string", "default": "ssh"},
                        "default_user": {"type": "string", "nullable": True},
                        "options": {"type": "object", "default": {}},
                        "credential_ref_id": {"type": "string", "nullable": True},
                    },
                },
                "ResolvedConnection": {
                    "type": "object",
                    "description": "Safe connection resolution metadata (strictly omits secrets)",
                    "required": ["device_id", "device_name", "host", "port", "connection_method", "has_credential"],
                    "properties": {
                        "device_id": {"type": "string"},
                        "device_name": {"type": "string"},
                        "host": {"type": "string"},
                        "port": {"type": "integer"},
                        "connection_method": {"type": "string"},
                        "default_user": {"type": "string", "nullable": True},
                        "has_credential": {
                            "type": "boolean",
                            "description": "True if an associated credential was resolved in internal memory",
                        },
                        "credential_ref_id": {"type": "string", "nullable": True},
                        "options": {"type": "object"},
                    },
                },
                "SCPUploadRequest": {
                    "type": "object",
                    "required": ["device", "local_path", "remote_path"],
                    "properties": {
                        "device": {"type": "string", "description": "Device name or UUID"},
                        "local_path": {"type": "string", "description": "Local file path to upload"},
                        "remote_path": {"type": "string", "description": "Destination file path on remote host"},
                        "session_id": {"type": "string", "nullable": True},
                        "timeout": {"type": "number", "default": 30.0},
                        "metadata": {"type": "object", "default": {}},
                    },
                },
                "SCPDownloadRequest": {
                    "type": "object",
                    "required": ["device", "remote_path", "local_path"],
                    "properties": {
                        "device": {"type": "string", "description": "Device name or UUID"},
                        "remote_path": {"type": "string", "description": "Remote file path to download"},
                        "local_path": {"type": "string", "description": "Destination file path on local host"},
                        "session_id": {"type": "string", "nullable": True},
                        "timeout": {"type": "number", "default": 30.0},
                        "metadata": {"type": "object", "default": {}},
                    },
                },
            },
        },
        "security": [
            {"bearerAuth": []},
            {"apiKeyAuth": []},
        ],
        "paths": {
            "/openapi.json": {
                "get": {
                    "tags": ["Documentation"],
                    "summary": "Retrieve OpenAPI 3.0 specification",
                    "security": [],
                    "responses": {
                        "200": {"description": "OpenAPI JSON specification"},
                    },
                },
            },
            "/docs": {
                "get": {
                    "tags": ["Documentation"],
                    "summary": "Interactive Swagger UI documentation",
                    "security": [],
                    "responses": {
                        "200": {"description": "HTML page rendering Swagger UI"},
                    },
                },
            },
            "/sessions": {
                "get": {
                    "tags": ["Sessions"],
                    "summary": "List all sessions",
                    "responses": {
                        "200": {
                            "description": "List of sessions",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "items": {"type": "array", "items": {"$ref": "#/components/schemas/Session"}},
                                            "total": {"type": "integer"},
                                        },
                                    }
                                }
                            },
                        },
                    },
                },
                "post": {
                    "tags": ["Sessions"],
                    "summary": "Create and start a new terminal session",
                    "requestBody": {
                        "required": False,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SessionCreate"}}},
                    },
                    "responses": {
                        "201": {
                            "description": "Session created successfully",
                            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Session"}}},
                        },
                        "400": {"description": "Validation error", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                },
            },
            "/sessions/{id}": {
                "get": {
                    "tags": ["Sessions"],
                    "summary": "Get session by ID",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"description": "Session details", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Session"}}}},
                        "404": {"description": "Session not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                },
                "delete": {
                    "tags": ["Sessions"],
                    "summary": "Close a session",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"description": "Session closed", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Session"}}}},
                    },
                },
            },
            "/sessions/{id}/write": {
                "post": {
                    "tags": ["Sessions"],
                    "summary": "Write data to an active session",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SessionWriteRequest"}}},
                    },
                    "responses": {
                        "200": {"description": "Bytes written", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SessionWriteResponse"}}}},
                        "409": {"description": "Session closed or not active", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                },
            },
            "/sessions/{id}/read": {
                "post": {
                    "tags": ["Sessions"],
                    "summary": "Read output text from an active session",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "required": False,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SessionReadRequest"}}},
                    },
                    "responses": {
                        "200": {"description": "Decoded output text", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SessionReadResponse"}}}},
                    },
                },
            },
            "/sessions/{id}/close": {
                "post": {
                    "tags": ["Sessions"],
                    "summary": "Close active session channel",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"description": "Session closed", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Session"}}}},
                    },
                },
            },
            "/sessions/{id}/events": {
                "get": {
                    "tags": ["Events"],
                    "summary": "Retrieve events using cursor pagination",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}},
                        {"name": "since_sequence", "in": "query", "schema": {"type": "integer", "default": 0}},
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 50}},
                    ],
                    "responses": {
                        "200": {"description": "Paginated events", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/EventList"}}}},
                    },
                },
            },
            "/sessions/{id}/jobs": {
                "get": {
                    "tags": ["Jobs"],
                    "summary": "List jobs for a session",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {
                            "description": "List of jobs",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "items": {"type": "array", "items": {"$ref": "#/components/schemas/Job"}},
                                            "total": {"type": "integer"},
                                        },
                                    }
                                }
                            },
                        },
                    },
                },
                "post": {
                    "tags": ["Jobs"],
                    "summary": "Submit a job bound to a session",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/JobCreate"}}},
                    },
                    "responses": {
                        "202": {"description": "Job submitted", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Job"}}}},
                    },
                },
            },
            "/jobs": {
                "post": {
                    "tags": ["Jobs"],
                    "summary": "Submit an asynchronous job",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/JobCreate"}}},
                    },
                    "responses": {
                        "202": {"description": "Job submitted", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Job"}}}},
                    },
                },
            },
            "/jobs/{id}": {
                "get": {
                    "tags": ["Jobs"],
                    "summary": "Get job status and output",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"description": "Job status and results", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Job"}}}},
                        "404": {"description": "Job not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                },
            },
            "/jobs/{id}/wait": {
                "post": {
                    "tags": ["Jobs"],
                    "summary": "Wait for job completion",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "required": False,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/JobWait"}}},
                    },
                    "responses": {
                        "200": {"description": "Finished or current job state", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Job"}}}},
                    },
                },
            },
            "/jobs/{id}/cancel": {
                "post": {
                    "tags": ["Jobs"],
                    "summary": "Cancel running job",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"description": "Job cancelled", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Job"}}}},
                    },
                },
            },
            "/devices": {
                "get": {
                    "tags": ["Devices"],
                    "summary": "List devices in inventory",
                    "parameters": [
                        {"name": "only_active", "in": "query", "schema": {"type": "boolean", "default": True}}
                    ],
                    "responses": {
                        "200": {
                            "description": "List of devices",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "items": {"type": "array", "items": {"$ref": "#/components/schemas/Device"}},
                                            "total": {"type": "integer"},
                                        },
                                    }
                                }
                            },
                        },
                    },
                },
                "post": {
                    "tags": ["Devices"],
                    "summary": "Register a new device",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/DeviceCreate"}}},
                    },
                    "responses": {
                        "201": {"description": "Device registered", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Device"}}}},
                    },
                },
            },
            "/devices/{id_or_name}": {
                "get": {
                    "tags": ["Devices"],
                    "summary": "Get device by ID or nickname",
                    "parameters": [{"name": "id_or_name", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"description": "Device details", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Device"}}}},
                        "404": {"description": "Device not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                },
                "patch": {
                    "tags": ["Devices"],
                    "summary": "Update device configuration",
                    "parameters": [{"name": "id_or_name", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"type": "object"}}},
                    },
                    "responses": {
                        "200": {"description": "Device updated", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Device"}}}},
                    },
                },
                "delete": {
                    "tags": ["Devices"],
                    "summary": "Logically remove device",
                    "parameters": [{"name": "id_or_name", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"description": "Device removed", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Device"}}}},
                    },
                },
            },
            "/devices/{id_or_name}/deactivate": {
                "post": {
                    "tags": ["Devices"],
                    "summary": "Deactivate device logically",
                    "parameters": [{"name": "id_or_name", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"description": "Device deactivated", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Device"}}}},
                    },
                },
            },
            "/devices/{id_or_name}/resolve": {
                "get": {
                    "tags": ["Devices"],
                    "summary": "Resolve connection parameters by nickname (strictly secret-safe)",
                    "description": "Returns address, port, user and confirmation of credential without exposing the secret.",
                    "parameters": [{"name": "id_or_name", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {
                        "200": {"description": "Resolved connection metadata", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ResolvedConnection"}}}},
                        "400": {"description": "Device inactive or deleted", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "404": {"description": "Device or credential not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                },
            },
            "/scp/upload": {
                "post": {
                    "tags": ["SCP"],
                    "summary": "Submit an asynchronous SCP upload transfer",
                    "description": "Uploads a local file to a remote SSH device identified by nickname or UUID as a background Job.",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SCPUploadRequest"}}},
                    },
                    "responses": {
                        "202": {"description": "Transfer job accepted and launched", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Job"}}}},
                        "400": {"description": "Validation error or missing local file", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "404": {"description": "Device not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                },
            },
            "/scp/download": {
                "post": {
                    "tags": ["SCP"],
                    "summary": "Submit an asynchronous SCP download transfer",
                    "description": "Downloads a remote file from an SSH device identified by nickname or UUID to local storage as a background Job.",
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SCPDownloadRequest"}}},
                    },
                    "responses": {
                        "202": {"description": "Transfer job accepted and launched", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Job"}}}},
                        "400": {"description": "Validation error or invalid destination", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                        "404": {"description": "Device not found", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ErrorResponse"}}}},
                    },
                },
            },
        },
    }


def get_swagger_ui_html() -> str:
    """Returns standalone Swagger UI v5 HTML loading assets via CDN (zero dependencies)."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Terminal Session Manager — Swagger UI</title>
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <link rel="icon" type="image/png" href="https://fastapi.tiangolo.com/img/favicon.png" />
  <style>
    html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
    *, *:before, *:after { box-sizing: inherit; }
    body { margin: 0; background: #fafafa; }
    .topbar { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {
      const ui = SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: "#swagger-ui",
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "BaseLayout"
      });
      window.ui = ui;
    };
  </script>
</body>
</html>
"""
