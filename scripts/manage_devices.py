#!/usr/bin/env python3
"""Script interativo para gerenciamento de dispositivos, teste de conexão e geração de chaves SSH no TSM."""

from __future__ import annotations

import getpass
import io
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any

import paramiko

from terminal_session_manager.app import TSMApplication
from terminal_session_manager.errors import (
    DeviceInactiveError,
    DeviceNotFoundError,
    TransportError,
    TransportTimeoutError,
    ValidationError,
)
from terminal_session_manager.models.credential import CredentialRef, CredentialType
from terminal_session_manager.models.device import ConnectionMethod, Device, DeviceType
from terminal_session_manager.services.scp_service import SCPTransferDirection
from terminal_session_manager.transports.ssh import SSHTransport


def print_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def clean_path_input(raw: str) -> Path:
    """Remove aspas acidentais (comuns ao copiar caminho no Windows) e expande ~."""
    cleaned = raw.strip().strip('"').strip("'")
    return Path(cleaned).expanduser().resolve()


def list_devices_view(app: TSMApplication) -> list[Device]:
    print_header("Dispositivos Cadastrados")
    devices = app.device_service.list_devices(only_active=False)

    if not devices:
        print("  Nenhum dispositivo cadastrado no momento.")
        return []

    print(
        f"  {'NOME / NICKNAME':<20} {'HOST:PORTA':<24} {'USUÁRIO':<12} {'MÉTODO':<8} {'STATUS':<10} {'CREDENCIAL'}"
    )
    print("  " + "-" * 90)

    for dev in devices:
        status_str = "Ativo" if dev.is_active else "Inativo"
        has_cred = "Sim (Protegida)" if dev.credential_ref_id else "Não"
        host_port = f"{dev.host}:{dev.port}"
        user = dev.default_user or "-"
        method = dev.connection_method.value.upper()
        print(
            f"  {dev.name:<20} {host_port:<24} {user:<12} {method:<8} {status_str:<10} {has_cred}"
        )
    print("  " + "-" * 90)
    print(f"  Total: {len(devices)} dispositivo(s)\n")
    return devices


def add_device_interactive(app: TSMApplication) -> Device | None:
    print_header("Cadastrar Novo Dispositivo")

    # 1. Nome / Nickname
    while True:
        name = input("  Nome / Nickname único (ex: srv-prod): ").strip()
        if not name:
            print("  [!] O nome não pode ser vazio.")
            continue
        existing = app.device_repo.get_by_name(name)
        if existing and not existing.is_deleted:
            print(f"  [!] Já existe um dispositivo com o nome '{name}'. Escolha outro.")
            continue
        break

    # 2. Host
    while True:
        host = input("  Endereço IP ou Hostname (ex: 192.168.1.50): ").strip()
        if not host:
            print("  [!] O host não pode ser vazio.")
            continue
        break

    # 3. Porta
    port_input = input("  Porta SSH [padrão: 22]: ").strip()
    try:
        port = int(port_input) if port_input else 22
        if not (1 <= port <= 65535):
            raise ValueError()
    except ValueError:
        print("  [!] Porta inválida. Usando padrão 22.")
        port = 22

    # 4. Usuário
    default_user = input("  Usuário padrão [ex: ubuntu, root, admin]: ").strip() or None

    # 5. Tipo de dispositivo
    print("\n  Tipos de dispositivo disponíveis:")
    print("    1) server (padrão)   2) router   3) switch   4) container   5) workstation")
    type_choice = input("  Escolha o tipo [1-5, padrão: 1]: ").strip()
    type_map = {
        "1": DeviceType.SERVER,
        "2": DeviceType.ROUTER,
        "3": DeviceType.SWITCH,
        "4": DeviceType.CONTAINER,
        "5": DeviceType.WORKSTATION,
    }
    device_type = type_map.get(type_choice, DeviceType.SERVER)

    # 6. Método de conexão
    print("\n  Método de conexão:")
    print("    1) SSH (padrão)   2) Local")
    conn_choice = input("  Escolha o método [1-2, padrão: 1]: ").strip()
    conn_method = ConnectionMethod.LOCAL if conn_choice == "2" else ConnectionMethod.SSH

    # 7. Autenticação e Credenciais
    credential_ref_id: str | None = None
    if conn_method == ConnectionMethod.SSH:
        print("\n  Autenticação SSH:")
        print("    1) Senha (password)")
        print("    2) Chave Privada SSH (arquivo PEM, OpenSSH, id_rsa, id_ed25519)")
        print("    3) Sem credencial / agente SSH do sistema")
        auth_choice = input("  Escolha a autenticação [1-3, padrão: 1]: ").strip()

        if auth_choice in ("1", ""):
            password = getpass.getpass("  Digite a senha de acesso SSH: ").strip()
            if password:
                cred_ref = CredentialRef(
                    name=f"cred-{name}-password",
                    credential_type=CredentialType.PASSWORD,
                    description=f"Senha para dispositivo {name}",
                )
                app.credential_store.save_credential(cred_ref, password)
                credential_ref_id = cred_ref.id
                print("  [✓] Senha armazenada de forma segura e cifrada em repouso no cofre.")
            else:
                print("  [i] Nenhuma senha digitada.")

        elif auth_choice == "2":
            key_raw = input("  Caminho do arquivo de chave privada (ex: ~/.ssh/id_ed25519): ")
            resolved_path = clean_path_input(key_raw)
            if resolved_path.is_file():
                try:
                    key_content = resolved_path.read_text(encoding="utf-8")
                    cred_ref = CredentialRef(
                        name=f"cred-{name}-key",
                        credential_type=CredentialType.SSH_KEY,
                        description=f"Chave SSH de {resolved_path.name} para {name}",
                    )
                    app.credential_store.save_credential(cred_ref, key_content)
                    credential_ref_id = cred_ref.id
                    print(f"  [✓] Chave '{resolved_path.name}' importada e criptografada com sucesso no cofre.")
                except Exception as err:
                    print(f"  [!] Erro ao ler arquivo de chave: {err}")
            else:
                print(f"  [!] Arquivo não encontrado: '{resolved_path}'. Prosseguindo sem credencial vinculada.")

    # 8. Criar e registrar o dispositivo
    device = Device(
        name=name,
        host=host,
        port=port,
        device_type=device_type,
        connection_method=conn_method,
        default_user=default_user,
        credential_ref_id=credential_ref_id,
    )

    try:
        registered = app.device_service.register_device(device)
        print("\n  " + "=" * 60)
        print(f"  [✓] DISPOSITIVO CADASTRADO COM SUCESSO!")
        print(f"      Nome / Nickname: {registered.name}")
        print(f"      Host:Porta:      {registered.host}:{registered.port}")
        print(f"      Usuário:         {registered.default_user or '(nenhum)'}")
        print(f"      Método:          {registered.connection_method.value.upper()}")
        print(f"      Credencial:      {'Associada e Criptografada' if credential_ref_id else 'Nenhuma'}")
        print(f"      ID:              {registered.id}")
        print("  " + "=" * 60)
        return registered
    except Exception as err:
        print(f"  [!] Falha ao registrar dispositivo: {err}")
        return None


def edit_device_interactive(app: TSMApplication) -> Device | None:
    print_header("Editar Dispositivo")
    devices = list_devices_view(app)
    if not devices:
        return None

    name_or_id = input("  Digite o Nome (nickname) ou ID do dispositivo para editar: ").strip()
    if not name_or_id:
        return None

    dev = app.device_repo.get_by_name(name_or_id) or app.device_repo.get_by_id(name_or_id)
    if not dev or dev.is_deleted:
        print(f"  [!] Dispositivo '{name_or_id}' não encontrado no inventário.")
        return None

    print(f"\n  Editando dispositivo '{dev.name}' (ID: {dev.id})")
    print("  (Pressione Enter em qualquer campo para manter o valor atual)\n")

    # 1. Nome / Nickname
    new_name = dev.name
    while True:
        prompt_name = input(f"  Nome / Nickname [atual: {dev.name}]: ").strip()
        if not prompt_name or prompt_name == dev.name:
            new_name = dev.name
            break
        existing = app.device_repo.get_by_name(prompt_name)
        if existing and existing.id != dev.id and not existing.is_deleted:
            print(f"  [!] Já existe outro dispositivo com o nome '{prompt_name}'. Escolha outro.")
            continue
        new_name = prompt_name
        break

    # 2. Host
    prompt_host = input(f"  Host / IP [atual: {dev.host}]: ").strip()
    new_host = prompt_host if prompt_host else dev.host

    # 3. Porta
    prompt_port = input(f"  Porta [atual: {dev.port}]: ").strip()
    new_port = dev.port
    if prompt_port:
        try:
            val_port = int(prompt_port)
            if 1 <= val_port <= 65535:
                new_port = val_port
            else:
                print(f"  [!] Porta fora do intervalo (1-65535). Mantendo porta atual ({dev.port}).")
        except ValueError:
            print(f"  [!] Porta inválida. Mantendo porta atual ({dev.port}).")

    # 4. Usuário padrão
    current_user_display = dev.default_user or "(nenhum)"
    prompt_user = input(f"  Usuário padrão [atual: {current_user_display}] (digite '-' para remover): ").strip()
    if prompt_user == "-":
        new_user: str | None = None
        user_modified = True
    elif prompt_user:
        new_user = prompt_user
        user_modified = True
    else:
        new_user = dev.default_user
        user_modified = False

    # 5. Tipo de dispositivo
    type_map = {
        "1": DeviceType.SERVER,
        "2": DeviceType.ROUTER,
        "3": DeviceType.SWITCH,
        "4": DeviceType.CONTAINER,
        "5": DeviceType.WORKSTATION,
    }
    print(f"\n  Tipo de dispositivo [atual: {dev.device_type.value}]:")
    print("    1) server   2) router   3) switch   4) container   5) workstation")
    type_choice = input("  Escolha o tipo [1-5, Enter para manter]: ").strip()
    new_device_type = type_map.get(type_choice, dev.device_type)

    # 6. Método de conexão
    print(f"\n  Método de conexão [atual: {dev.connection_method.value.upper()}]:")
    print("    1) SSH   2) Local")
    conn_choice = input("  Escolha o método [1-2, Enter para manter]: ").strip()
    if conn_choice == "1":
        new_conn_method = ConnectionMethod.SSH
    elif conn_choice == "2":
        new_conn_method = ConnectionMethod.LOCAL
    else:
        new_conn_method = dev.connection_method

    try:
        updated = app.device_service.update_device(
            device_id=dev.id,
            name=new_name,
            host=new_host,
            port=new_port,
            device_type=new_device_type,
            connection_method=new_conn_method,
            default_user=new_user if user_modified else dev.default_user,
        )
        if user_modified and new_user is None:
            updated.default_user = None
            app.device_repo.register(updated)

        print("\n  " + "=" * 60)
        print(f"  [✓] DISPOSITIVO ATUALIZADO COM SUCESSO!")
        print(f"      Nome / Nickname: {updated.name}")
        print(f"      Host:Porta:      {updated.host}:{updated.port}")
        print(f"      Usuário:         {updated.default_user or '(nenhum)'}")
        print(f"      Tipo:            {updated.device_type.value}")
        print(f"      Método:          {updated.connection_method.value.upper()}")
        print(f"      Status:          {'Ativo' if updated.is_active else 'Inativo'}")
        print(f"      ID:              {updated.id}")
        print("  " + "=" * 60)
        return updated
    except Exception as err:
        print(f"  [!] Falha ao atualizar dispositivo: {err}")
        return None


def test_connection_interactive(app: TSMApplication) -> None:
    print_header("Testar Conexão de um Dispositivo")
    devices = list_devices_view(app)
    if not devices:
        return

    name_or_id = input("  Digite o Nome (nickname) ou ID do dispositivo para testar: ").strip()
    if not name_or_id:
        return

    try:
        resolved = app.device_service.resolve_connection(name_or_id)
    except DeviceInactiveError:
        print(f"  [!] O dispositivo '{name_or_id}' está desativado. Ative-o antes de testar.")
        return
    except DeviceNotFoundError:
        print(f"  [!] Dispositivo '{name_or_id}' não encontrado no inventário.")
        return
    except Exception as err:
        print(f"  [!] Erro na resolução do dispositivo: {err}")
        return

    print(f"\n  Iniciando teste de conectividade para '{resolved.device_name}'...")
    print(f"  Destino: {resolved.host}:{resolved.port}")
    print(f"  Usuário: {resolved.default_user or '(não especificado)'}")
    print(f"  Método:  {resolved.connection_method.value.upper()}")
    print(f"  Credencial vinculada: {'Sim (Cifrada)' if resolved.secret else 'Nenhuma'}")

    # Se for Local
    if resolved.connection_method == ConnectionMethod.LOCAL:
        print("  [✓] Dispositivo local configurado. Pronto para uso.")
        return

    # Preparar credenciais para SSHTransport
    cred_type = resolved.credential_ref.credential_type if resolved.credential_ref else None
    password = None
    private_key = None
    secret = resolved.secret
    if cred_type == CredentialType.PASSWORD:
        password = secret if isinstance(secret, str) else (secret.decode("utf-8", errors="ignore") if secret else None)
    elif cred_type == CredentialType.SSH_KEY:
        private_key = secret
    elif secret:
        sec_str = secret if isinstance(secret, str) else secret.decode("utf-8", errors="ignore")
        if "PRIVATE KEY" in sec_str:
            private_key = secret
        else:
            password = sec_str

    # Se não tiver credencial vinculada, oferece para digitar na hora para teste
    if not password and not private_key:
        print("\n  [i] Este dispositivo não possui credencial salva no cofre.")
        resp = input("      Deseja digitar uma senha temporária para testar agora? (s/N): ").strip().lower()
        if resp in ("s", "sim", "y", "yes"):
            temp_pass = getpass.getpass("      Senha temporária: ").strip()
            if temp_pass:
                password = temp_pass
                # Pergunta se quer salvar de vez
                save_resp = input("      Deseja salvar essa senha no cofre para este dispositivo? (s/N): ").strip().lower()
                if save_resp in ("s", "sim", "y", "yes"):
                    cred_ref = CredentialRef(
                        name=f"cred-{resolved.device_name}-password",
                        credential_type=CredentialType.PASSWORD,
                    )
                    app.credential_store.save_credential(cred_ref, temp_pass)
                    dev_obj = app.device_repo.get_by_id(resolved.device_id)
                    if dev_obj:
                        dev_obj.credential_ref_id = cred_ref.id
                        app.device_service.register_device(dev_obj)
                        print("      [✓] Senha gravada com sucesso no cofre do dispositivo.")

    print("\n  [•] Conectando via SSH...", end="", flush=True)

    # Configuração de SSH segura
    known_hosts = app.config.ssh.known_hosts_path
    strict_checking = app.config.ssh.strict_host_key_checking
    timeout = min(app.config.ssh.connect_timeout, 10.0)

    # Executa comando diagnóstico leve (uname -a ou ver)
    transport = SSHTransport(
        host=resolved.host,
        port=resolved.port,
        username=resolved.default_user,
        password=password,
        private_key=private_key,
        known_hosts_path=known_hosts,
        strict_host_key_checking=strict_checking,
        connect_timeout=timeout,
        command="uname -a 2>/dev/null || ver 2>/dev/null || echo SSH_CONNECTED_OK",
        options=resolved.options,
    )

    start_time = time.monotonic()
    try:
        transport.open()
        raw_output = transport.read(1024, timeout=3.0)
        elapsed = time.monotonic() - start_time
        transport.close()

        print(" [OK]")
        print("\n  " + "=" * 60)
        print("  [✓] CONEXÃO SSH ESTABELECIDA COM SUCESSO!")
        print(f"      Latência:   {elapsed:.2f}s")
        print(f"      Host:       {resolved.host}:{resolved.port}")
        print(f"      Usuário:    {resolved.default_user}")
        if raw_output:
            out_text = raw_output.decode("utf-8", errors="replace").strip()
            print(f"      Resposta:   {out_text}")
        print("  " + "=" * 60)
    except TransportTimeoutError:
        print(" [FALHOU]")
        print("\n  [!] TIMEOUT DE CONEXÃO:")
        print(f"      Não foi possível conectar a '{resolved.host}:{resolved.port}' após {timeout}s.")
        print("      - Verifique se o endereço IP/hostname está correto.")
        print("      - Verifique se o serviço SSH está rodando no servidor remoto.")
        print("      - Verifique regras de firewall ou permissões de rede.")
    except TransportError as err:
        print(" [FALHOU]")
        err_msg = str(err)
        print(f"\n  [!] FALHA NA CONEXÃO SSH: {err_msg}")
        if "authentication failed" in err_msg.lower():
            print("      Dica: O usuário ou a senha/chave privada fornecida foram recusados pelo servidor remoto.")
        elif "host key verification failed" in err_msg.lower():
            print("      Dica: Chave do host desconhecida ou não listada no known_hosts com strict_checking ativo.")
        elif "connection refused" in err_msg.lower():
            print(f"      Dica: A porta {resolved.port} recusou a conexão. O SSH server está escutando nela?")
    except Exception as err:
        print(f" [FALHOU]\n  [!] Erro inesperado: {err}")


def generate_ssh_key_interactive(app: TSMApplication) -> None:
    print_header("Gerador de Chaves SSH")
    print("  Este assistente gera um novo par de chaves SSH (privada e pública)")
    print("  e fornece instruções completas de como autorizar no seu servidor.\n")

    print("  Escolha o algoritmo da chave:")
    print("    1) Ed25519 (Recomendado — moderna, mais rápida e mais segura)")
    print("    2) RSA 2048 bits")
    print("    3) RSA 4096 bits")
    algo_choice = input("  Opção [1-3, padrão: 1]: ").strip()

    if algo_choice == "2":
        algo_name = "RSA-2048"
        key_type = "rsa"
        key_obj = paramiko.RSAKey.generate(bits=2048)
    elif algo_choice == "3":
        algo_name = "RSA-4096"
        key_type = "rsa"
        key_obj = paramiko.RSAKey.generate(bits=4096)
    else:
        algo_name = "Ed25519"
        key_type = "ed25519"
        key_obj = paramiko.Ed25519Key.generate()

    # Local padrão para salvar
    default_dir = Path.home() / ".ssh"
    default_dir.mkdir(parents=True, exist_ok=True)
    default_filename = f"tsm_id_{key_type}"
    default_path = default_dir / default_filename

    print(f"\n  Local para salvar a chave privada:")
    path_input = input(f"  Caminho [padrão: {default_path}]: ").strip()
    save_path = clean_path_input(path_input) if path_input else default_path

    if save_path.is_file():
        overwrite = input(f"  [!] O arquivo '{save_path}' já existe. Deseja sobrescrever? (s/N): ").strip().lower()
        if overwrite not in ("s", "sim", "y", "yes"):
            print("  [i] Geração cancelada para não sobrescrever arquivo existente.")
            return

    # Passphrase opcional
    passphrase = getpass.getpass("  Passphrase para proteger a chave privada (deixe em branco para sem senha): ").strip()
    passphrase = passphrase if passphrase else None

    # Salva a chave privada
    save_path.parent.mkdir(parents=True, exist_ok=True)
    key_obj.write_private_key_file(str(save_path), password=passphrase)
    if os.name != "nt":
        try:
            os.chmod(save_path, 0o600)
        except OSError:
            pass

    # Gera e salva a chave pública
    pub_path = save_path.with_suffix(save_path.suffix + ".pub") if save_path.suffix else save_path.with_name(save_path.name + ".pub")
    pub_key_str = f"{key_obj.get_name()} {key_obj.get_base64()} tsm-agent-key"
    pub_path.write_text(pub_key_str + "\n", encoding="utf-8")

    print("\n  " + "=" * 70)
    print("  [✓] CHAVES GERADAS COM SUCESSO!")
    print(f"      Algoritmo:     {algo_name}")
    print(f"      Chave Privada: {save_path}")
    print(f"      Chave Pública: {pub_path}")
    print("  " + "=" * 70)

    # Exibe instruções de uso
    print_header("COMO USAR ESTA CHAVE NO SEU SERVIDOR REMOTO")
    print("  Para que o TSM e seus agentes consigam conectar usando essa chave,")
    print("  a chave pública precisa ser autorizada no seu servidor.\n")
    print("  Sua Chave Pública:")
    print("  " + "-" * 70)
    print(f"  {pub_key_str}")
    print("  " + "-" * 70)

    print("\n  MÉTODO 1 — Automático (pelo seu terminal):")
    print(f"    ssh-copy-id -i \"{pub_path}\" usuario@seu-servidor")

    print("\n  MÉTODO 2 — Manual (copiar e colar no servidor remoto):")
    print("    1. Conecte-se no servidor remoto normalmente.")
    print("    2. Execute os seguintes comandos no servidor:")
    print("       mkdir -p ~/.ssh")
    print("       chmod 700 ~/.ssh")
    print(f"       echo '{pub_key_str}' >> ~/.ssh/authorized_keys")
    print("       chmod 600 ~/.ssh/authorized_keys")

    # Oferecer vincular agora a um dispositivo
    print("\n  " + "-" * 70)
    vincular = input("  Deseja associar esta chave privada agora a um dispositivo cadastrado? (s/N): ").strip().lower()
    if vincular in ("s", "sim", "y", "yes"):
        devices = app.device_service.list_devices(only_active=False)
        if not devices:
            print("  Nenhum dispositivo cadastrado. Use a opção 2 do menu para cadastrar.")
            return

        print("\n  Dispositivos:")
        for d in devices:
            print(f"    - {d.name} ({d.host}:{d.port})")

        target_name = input("  Nome do dispositivo para vincular: ").strip()
        dev = app.device_repo.get_by_name(target_name) or app.device_repo.get_by_id(target_name)
        if dev:
            key_content = save_path.read_text(encoding="utf-8")
            cred_ref = CredentialRef(
                name=f"cred-{dev.name}-key",
                credential_type=CredentialType.SSH_KEY,
                description=f"Chave SSH gerada {save_path.name}",
            )
            app.credential_store.save_credential(cred_ref, key_content)
            dev.credential_ref_id = cred_ref.id
            app.device_service.register_device(dev)
            print(f"  [✓] Chave vinculada com sucesso ao dispositivo '{dev.name}'!")
        else:
            print(f"  [!] Dispositivo '{target_name}' não encontrado.")


def toggle_device_status(app: TSMApplication) -> None:
    print_header("Ativar / Desativar Dispositivo")
    devices = list_devices_view(app)
    if not devices:
        return

    name_or_id = input("  Digite o Nome ou ID do dispositivo: ").strip()
    if not name_or_id:
        return

    dev = app.device_repo.get_by_name(name_or_id) or app.device_repo.get_by_id(name_or_id)
    if not dev or dev.is_deleted:
        print(f"  [!] Dispositivo '{name_or_id}' não encontrado.")
        return

    new_status = not dev.is_active
    dev.is_active = new_status
    app.device_service.register_device(dev)
    status_label = "ATIVADO" if new_status else "DESATIVADO"
    print(f"  [✓] Dispositivo '{dev.name}' agora está {status_label}.")


def update_device_credential_interactive(app: TSMApplication) -> None:
    print_header("Atualizar Credencial de um Dispositivo")
    devices = list_devices_view(app)
    if not devices:
        return

    name_or_id = input("  Digite o Nome ou ID do dispositivo para atualizar a credencial: ").strip()
    if not name_or_id:
        return

    dev = app.device_repo.get_by_name(name_or_id) or app.device_repo.get_by_id(name_or_id)
    if not dev or dev.is_deleted:
        print(f"  [!] Dispositivo '{name_or_id}' não encontrado.")
        return

    print(f"\n  Atualizando credencial de '{dev.name}' ({dev.host}:{dev.port}):")
    print("    1) Senha (password)")
    print("    2) Chave Privada SSH (arquivo)")
    print("    3) Remover credencial")
    choice = input("  Escolha a opção [1-3]: ").strip()

    if choice == "1":
        new_pass = getpass.getpass("  Digite a nova senha: ").strip()
        if new_pass:
            cred_ref = CredentialRef(name=f"cred-{dev.name}-password", credential_type=CredentialType.PASSWORD)
            app.credential_store.save_credential(cred_ref, new_pass)
            dev.credential_ref_id = cred_ref.id
            app.device_service.register_device(dev)
            print(f"  [✓] Nova senha salva no cofre e associada a '{dev.name}'.")
    elif choice == "2":
        key_raw = input("  Caminho do arquivo de chave privada: ")
        resolved = clean_path_input(key_raw)
        if resolved.is_file():
            content = resolved.read_text(encoding="utf-8")
            cred_ref = CredentialRef(name=f"cred-{dev.name}-key", credential_type=CredentialType.SSH_KEY)
            app.credential_store.save_credential(cred_ref, content)
            dev.credential_ref_id = cred_ref.id
            app.device_service.register_device(dev)
            print(f"  [✓] Chave '{resolved.name}' associada com sucesso a '{dev.name}'.")
        else:
            print(f"  [!] Arquivo não encontrado: '{resolved}'.")
    elif choice == "3":
        dev.credential_ref_id = None
        app.device_service.register_device(dev)
        print(f"  [✓] Credencial desvinculada de '{dev.name}'.")


def delete_device_interactive(app: TSMApplication) -> None:
    print_header("Apagar Dispositivo")
    devices = list_devices_view(app)
    if not devices:
        return

    name_or_id = input("  Digite o Nome ou ID do dispositivo para apagar: ").strip()
    if not name_or_id:
        return

    dev = app.device_repo.get_by_name(name_or_id) or app.device_repo.get_by_id(name_or_id)
    if not dev or dev.is_deleted:
        print(f"  [!] Dispositivo '{name_or_id}' não encontrado.")
        return

    confirm = input(f"  [?] Tem certeza de que deseja apagar '{dev.name}'? (s/N): ").strip().lower()
    if confirm in ("s", "sim", "y", "yes"):
        try:
            app.device_service.remove_device(dev.id)
            print(f"  [✓] Dispositivo '{dev.name}' foi removido com sucesso!")
        except Exception as err:
            print(f"  [!] Erro ao remover dispositivo: {err}")
    else:
        print("  [i] Operação cancelada.")


def scp_transfer_interactive(app: TSMApplication) -> None:
    print_header("Transferência e Teste de Arquivos SCP")
    devices = list_devices_view(app)
    if not devices:
        return

    name_or_id = input("  Digite o Nome (nickname) ou ID do dispositivo remoto: ").strip()
    if not name_or_id:
        return

    dev = app.device_repo.get_by_name(name_or_id) or app.device_repo.get_by_id(name_or_id)
    if not dev or dev.is_deleted:
        print(f"  [!] Dispositivo '{name_or_id}' não encontrado.")
        return

    if not dev.is_active:
        print(f"  [!] Dispositivo '{dev.name}' está DESATIVADO.")
        return

    if dev.connection_method != ConnectionMethod.SSH:
        print(f"  [!] O dispositivo '{dev.name}' não é SSH (método: {dev.connection_method.value}). SCP requer SSH.")
        return

    print(f"\n  Operações SCP com '{dev.name}' ({dev.host}:{dev.port}):")
    print("    1) Upload   (computador local -> dispositivo remoto)")
    print("    2) Download (dispositivo remoto -> computador local)")
    print("    3) Teste Rápido de Conexão SCP (envio de arquivo de verificação)")
    print("    0) Voltar")
    choice = input("  Escolha a operação [0-3, padrão: 1]: ").strip()

    if choice == "0":
        return

    if choice == "3":
        print(f"\n  [+] Iniciando teste rápido de conectividade SCP com '{dev.name}'...")
        timestamp = int(time.time())
        test_filename = f"tsm_test_{timestamp}.txt"
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8", prefix="tsm_scp_") as tmp_f:
            tmp_f.write(f"TSM SCP Diagnostic Test\nTimestamp: {time.ctime()}\nDevice: {dev.name}\n")
            local_tmp_path = Path(tmp_f.name)

        remote_target_path = f"/tmp/{test_filename}"
        print(f"  [+] Enviando arquivo temporário local para '{remote_target_path}'...")
        start_t = time.perf_counter()
        try:
            job = app.scp_service.submit_transfer(
                device_identifier=dev.name,
                direction=SCPTransferDirection.UPLOAD,
                local_path=str(local_tmp_path),
                remote_path=remote_target_path,
                timeout=20.0,
            )
            completed_job = app.scp_service.wait_transfer(job.id, timeout=25.0)
            elapsed = time.perf_counter() - start_t
            if completed_job.status.value == "completed":
                print(f"  [✓] Teste SCP concluído com SUCESSO em {elapsed:.2f}s!")
                print(f"      Job ID: {completed_job.id}")
                print(f"      Saída:  {completed_job.stdout.strip() or 'OK'}")
            else:
                print(f"  [!] Teste SCP FALHOU (Status: {completed_job.status.value.upper()}) após {elapsed:.2f}s.")
                if completed_job.stderr:
                    print(f"      Erro:   {completed_job.stderr.strip()}")
                if completed_job.failure_reason:
                    print(f"      Motivo: {completed_job.failure_reason}")
        except Exception as err:
            print(f"  [!] Erro na execução da transferência SCP: {err}")
        finally:
            if local_tmp_path.exists():
                local_tmp_path.unlink(missing_ok=True)
        return

    is_upload = (choice != "2")
    direction = SCPTransferDirection.UPLOAD if is_upload else SCPTransferDirection.DOWNLOAD

    if is_upload:
        raw_local = input("  Caminho do arquivo LOCAL a ser enviado: ").strip()
        local_path = clean_path_input(raw_local)
        if not local_path.is_file():
            print(f"  [!] Arquivo local não encontrado: '{local_path}'.")
            return
        remote_path = input("  Caminho de destino REMOTO (ex: /tmp/arquivo.txt ou /home/usuario/): ").strip()
        if not remote_path:
            print("  [!] O caminho remoto não pode ser vazio.")
            return
    else:
        remote_path = input("  Caminho do arquivo REMOTO a ser baixado (ex: /etc/os-release): ").strip()
        if not remote_path:
            print("  [!] O caminho remoto não pode ser vazio.")
            return
        raw_local = input("  Caminho de destino LOCAL (arquivo ou diretório): ").strip()
        local_path = clean_path_input(raw_local)

    timeout_raw = input("  Timeout da transferência em segundos [padrão: 60]: ").strip()
    try:
        timeout = float(timeout_raw) if timeout_raw else 60.0
    except ValueError:
        timeout = 60.0

    dir_str = "UPLOAD (Local -> Remoto)" if is_upload else "DOWNLOAD (Remoto -> Local)"
    print(f"\n  [+] Submetendo Job de {dir_str}...")
    print(f"      Dispositivo: {dev.name} ({dev.host}:{dev.port})")
    print(f"      Origem:      {local_path if is_upload else remote_path}")
    print(f"      Destino:     {remote_path if is_upload else local_path}")
    print(f"      Timeout:     {timeout}s")

    start_t = time.perf_counter()
    try:
        job = app.scp_service.submit_transfer(
            device_identifier=dev.name,
            direction=direction,
            local_path=str(local_path),
            remote_path=remote_path,
            timeout=timeout,
        )
        print(f"  [+] Job criado com ID: {job.id}. Aguardando transferência...")
        completed_job = app.scp_service.wait_transfer(job.id, timeout=timeout + 5.0)
        elapsed = time.perf_counter() - start_t

        print("\n  " + "=" * 60)
        if completed_job.status.value == "completed":
            print(f"  [✓] TRANSFERÊNCIA CONCLUÍDA COM SUCESSO! ({elapsed:.2f}s)")
            print(f"      Job ID:      {completed_job.id}")
            print(f"      Status:      {completed_job.status.value.upper()}")
            print(f"      Código Exit: {completed_job.exit_code}")
            if completed_job.stdout:
                print(f"      Detalhes:    {completed_job.stdout.strip()}")
        else:
            print(f"  [!] TRANSFERÊNCIA NÃO CONCLUÍDA ({elapsed:.2f}s)")
            print(f"      Job ID:      {completed_job.id}")
            print(f"      Status:      {completed_job.status.value.upper()}")
            if completed_job.failure_reason:
                print(f"      Motivo:      {completed_job.failure_reason}")
            if completed_job.stderr:
                print(f"      Erro:        {completed_job.stderr.strip()}")
        print("  " + "=" * 60)
    except Exception as err:
        print(f"  [!] Erro durante a transferência: {err}")


def main() -> None:
    app = TSMApplication()
    print("\nInicializando Terminal Session Manager — Gerenciador de Dispositivos...")
    print(f"Banco conectado: {app.config.storage.db_path}")

    while True:
        print_header("Menu Principal — Dispositivos TSM")
        print("  1) Listar dispositivos")
        print("  2) Cadastrar novo dispositivo")
        print("  3) Editar dispositivo")
        print("  4) Testar conexão de um dispositivo")
        print("  5) Gerar chave SSH com ajuda de uso")
        print("  6) Atualizar credencial de um dispositivo")
        print("  7) Ativar / Desativar dispositivo")
        print("  8) Apagar dispositivo")
        print("  9) Transferência e teste de arquivos SCP (Upload / Download)")
        print("  0) Sair")
        print("-" * 70)

        opcao = input("  Escolha uma opção [0-9]: ").strip()

        if opcao == "1":
            list_devices_view(app)
            input("  Pressione Enter para continuar...")
        elif opcao == "2":
            add_device_interactive(app)
            input("\n  Pressione Enter para continuar...")
        elif opcao == "3":
            edit_device_interactive(app)
            input("\n  Pressione Enter para continuar...")
        elif opcao == "4":
            test_connection_interactive(app)
            input("\n  Pressione Enter para continuar...")
        elif opcao == "5":
            generate_ssh_key_interactive(app)
            input("\n  Pressione Enter para continuar...")
        elif opcao == "6":
            update_device_credential_interactive(app)
            input("\n  Pressione Enter para continuar...")
        elif opcao == "7":
            toggle_device_status(app)
            input("\n  Pressione Enter para continuar...")
        elif opcao == "8":
            delete_device_interactive(app)
            input("\n  Pressione Enter para continuar...")
        elif opcao == "9":
            scp_transfer_interactive(app)
            input("\n  Pressione Enter para continuar...")
        elif opcao in ("0", "sair", "exit", "q"):
            print("\n  Encerrando gerenciador de dispositivos. Até logo!\n")
            break
        else:
            print("  [!] Opção inválida. Escolha entre 0 e 9.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperação interrompida pelo usuário.")
        sys.exit(0)
