# modules/common.nix
# Configuracion BASE compartida por TODOS los nodos del cluster.
# Cualquier cambio aqui se aplica a master y workers.

{ config, pkgs, lib, clusterConfig, mkHostsEntries, ... }:

{
  # ── Boot ─────────────────────────────────────────────────────────────────
  boot.loader.systemd-boot.enable = true;
  boot.loader.efi.canTouchEfiVariables = true;

  # ── Red ──────────────────────────────────────────────────────────────────
  networking.firewall = {
    enable = true;
    # Puertos requeridos por Slurm
    allowedTCPPorts = [
      6817   # slurmctld (master)
      6818   # slurmd    (workers)
      6819   # slurmdbd  (accounting, opcional)
    ];
  };

  # Tailscale MagicDNS resuelve los hostnames del cluster automaticamente.
  # No se necesitan entradas estaticas de /etc/hosts con IPs hardcodeadas.
  # El servicio tailscale-update-hosts (definido abajo) lo mantiene actualizado.

  # ── Zona horaria y locale ────────────────────────────────────────────────
  time.timeZone = "America/Guayaquil";
  i18n.defaultLocale = "es_EC.UTF-8";

  # ── Usuario del cluster ──────────────────────────────────────────────────
  # IMPORTANTE: Cambia la contrasena con `passwd CPDN` en el primer boot.
  # initialPassword solo sirve para el primer login; despues usa hashedPassword.
  users.users.CPDN = {
    isNormalUser = true;
    extraGroups = [ "wheel" ];
    # Genera el hash con: mkpasswd -m sha-512
    # Por ahora usa initialPassword solo para el primer boot:
    initialPassword = "cambiar_al_primer_boot";

    # Una vez que tengas tu clave publica SSH, descomenta esto y borra initialPassword:
    # openssh.authorizedKeys.keys = [
    #   "ssh-ed25519 AAAA... tu_clave_publica"
    # ];
  };

  # ── Paquetes base ─────────────────────────────────────────────────────────
  environment.systemPackages = with pkgs; [
    vim
    git
    htop
    wget
    slurm    # CLI de slurm (sinfo, squeue, sbatch, etc.)
    munge    # Autenticacion entre nodos
  ];

  # ── SSH ───────────────────────────────────────────────────────────────────
  services.openssh = {
    enable = true;
    settings = {
      # Deshabilita login con contrasena una vez que tengas claves SSH configuradas:
      # PasswordAuthentication = false;
      PermitRootLogin = "no";
    };
  };

  # ── Munge (autenticacion Slurm entre nodos) ───────────────────────────────
  # La misma clave munge debe estar en TODOS los nodos.
  # Generala con: dd if=/dev/urandom bs=1 count=1024 > /etc/munge/munge.key
  # Luego distribuyela a todos los nodos via scp.
  services.munge = {
    enable = true;
    # NixOS maneja el archivo /etc/munge/munge.key automaticamente.
    # Asegurate de que sea identico en todos los nodos.
  };

  # ── Tailscale (VPN — une todos los nodos en la misma red privada) ────────
  #
  # La auth key NUNCA va en el codigo. Se lee de un archivo en disco:
  #
  #   ANTES de aplicar nixos-rebuild en CADA nodo, ejecuta:
  #
  #     sudo mkdir -p /run/secrets
  #     echo "tskey-auth-XXXX" | sudo tee /run/secrets/tailscale_key > /dev/null
  #     sudo chmod 600 /run/secrets/tailscale_key
  #
  #   Reemplaza "tskey-auth-XXXX" por una clave nueva generada en:
  #     https://login.tailscale.com/admin/settings/keys
  #   (usa "Reusable" + "Ephemeral: off" para nodos permanentes)

  services.tailscale = {
    enable = true;
    # Permite que el firewall de NixOS coexista con Tailscale:
    useRoutingFeatures = "both";   # "client" si no vas a anunciar rutas
  };

  # Servicio oneshot que conecta automaticamente al primer boot
  # y no vuelve a hacer nada si ya esta conectado.
  systemd.services.tailscale-autoconnect = {
    description = "Conectar automaticamente a Tailscale al arrancar";
    after    = [ "network-online.target" "tailscale.service" ];
    wants    = [ "network-online.target" "tailscale.service" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type      = "oneshot";
      RemainAfterExit = true;
    };

    script = with pkgs; ''
      # Espera a que tailscaled este listo
      sleep 2

      # Verifica el estado actual (no reconecta si ya esta autenticado)
      STATUS=$(${tailscale}/bin/tailscale status --json \
               | ${jq}/bin/jq -r '.BackendState')

      if [ "$STATUS" = "NeedsLogin" ] || [ "$STATUS" = "NoState" ]; then
        KEY_FILE="${clusterConfig.tailscaleKeyFile}"
        if [ ! -f "$KEY_FILE" ]; then
          echo "ERROR: No se encontro el archivo de auth key: $KEY_FILE"
          echo "Ejecuta: echo 'tskey-auth-XXXX' | sudo tee $KEY_FILE && sudo chmod 600 $KEY_FILE"
          exit 1
        fi
        echo "Conectando a Tailscale..."
        ${tailscale}/bin/tailscale up \
          --authkey "$(cat $KEY_FILE)" \
          --hostname "$(hostname)" \
          --accept-routes \
          --accept-dns=true   # MagicDNS resuelve hostnames del cluster
        echo "Conectado. Esperando propagacion de MagicDNS..."
        sleep 3
      else
        echo "Tailscale ya esta conectado (estado: $STATUS). Sin accion."
      fi

      # Actualiza /etc/hosts con las IPs reales de Tailscale como fallback
      # (util para Slurm/Munge si MagicDNS tarda en propagar)
      echo "Actualizando /etc/hosts con IPs de Tailscale..."
      ${tailscale}/bin/tailscale status --json \
        | ${jq}/bin/jq -r '
            .Self as $self |
            (.Peer // {}) | to_entries[] | .value |
            select(.Online == true) |
            "\(.TailscaleIPs[0]) \(.HostName)"
          ' \
        | while read -r line; do
            HOST=$(echo "$line" | awk ''{print $2}'')
            # Evita duplicar entradas existentes
            if ! grep -q "$HOST" /etc/hosts 2>/dev/null; then
              echo "$line" >> /etc/hosts
              echo "  + Agregado: $line"
            fi
          done
    '';
  };

  # Permite trafico de Tailscale en el firewall de NixOS
  networking.firewall = {
    trustedInterfaces = [ "tailscale0" ];
    # Puerto UDP de Tailscale
    allowedUDPPorts = [ config.services.tailscale.port ];
  };

  system.stateVersion = "25.05";
}
