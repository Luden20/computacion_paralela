{
  description = "NixOS Cluster con Slurm - Computacion Paralela";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    # Descomenta si necesitas nixos-hardware para tu hardware especifico:
    # nixos-hardware.url = "github:NixOS/nixos-hardware/master";
  };

  outputs = { self, nixpkgs, ... }@inputs:
  let
    # ── Configuración del cluster ──────────────────────────────────────────
    # Solo se necesitan los HOSTNAMES. Tailscale MagicDNS los resuelve
    # automaticamente a sus IPs 100.x.x.x dentro de la VPN.
    #
    # Regla: el hostname de NixOS DEBE ser identico al nombre de la maquina
    # en Tailscale (se configura automaticamente con --hostname $(hostname)).
    clusterConfig = {
      # Nombre del nodo master
      masterHostname = "nix-master";

      # Lista de workers — solo hostnames, sin IPs
      workers = [
        { hostname = "nix-worker-01"; }
        { hostname = "nix-worker-02"; }
        # Para agregar un worker nuevo, solo agrega una linea aqui
        # y una entrada en nixosConfigurations mas abajo:
        # { hostname = "nix-worker-03"; }
      ];

      # Ruta al secreto de Tailscale en disco (NO la clave en texto plano)
      tailscaleKeyFile = "/run/secrets/tailscale_key";
    };

    # Con MagicDNS activo, /etc/hosts ya no es necesario para el cluster.
    # Esta funcion queda como fallback por si MagicDNS no esta disponible.
    # Los nombres simplemente se listan sin IP (solo comentario de referencia).
    mkHostsEntries = cfg:
      "# Cluster Slurm — resolucion via Tailscale MagicDNS\n" +
      "# ${cfg.masterHostname} (master)\n" +
      builtins.concatStringsSep "\n"
        (map (w: "# ${w.hostname} (worker)") cfg.workers);

    # Helper que construye la configuracion NixOS de un nodo
    mkNixosSystem = { hostname, extraModules ? [] }:
      nixpkgs.lib.nixosSystem {
        system = "x86_64-linux";
        specialArgs = { inherit inputs clusterConfig mkHostsEntries; };
        modules = [
          ./modules/common.nix          # Base compartida por todos los nodos
          ./hosts/${hostname}.nix       # Hardware y rol del nodo
        ] ++ extraModules;
      };

  in {
    nixosConfigurations = {

      # ── Nodo maestro (slurmctld) ───────────────────────────────────────
      nix-master = mkNixosSystem {
        hostname = "master";
      };

      # ── Workers (slurmd) ──────────────────────────────────────────────
      # Para agregar un nuevo worker: copia hosts/worker.nix con el nuevo nombre
      # y agrega una entrada aqui.
      nix-worker-01 = mkNixosSystem {
        hostname = "worker";
        extraModules = [
          { networking.hostName = nixpkgs.lib.mkForce "nix-worker-01"; }
        ];
      };

      nix-worker-02 = mkNixosSystem {
        hostname = "worker";
        extraModules = [
          { networking.hostName = nixpkgs.lib.mkForce "nix-worker-02"; }
        ];
      };

    };
  };
}
