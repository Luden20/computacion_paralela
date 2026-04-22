# modules/slurm-worker.nix
# Modulo de nodo WORKER: corre slurmd (ejecuta los trabajos).

{ config, pkgs, lib, clusterConfig, ... }:

{
  services.slurm = {
    client.enable = true;   # Activa slurmd

    # Debe coincidir exactamente con la config del master
    clusterName = "nixcluster";
    controlMachine = clusterConfig.masterHostname;

    extraConfig = ''
      # Autenticacion via Munge (debe coincidir con master)
      AuthType=auth/munge
      CryptoType=crypto/munge

      SlurmdSpoolDir=/var/spool/slurmd
      SlurmdLogFile=/var/log/slurm/slurmd.log
      SlurmdDebug=info
    '';
  };

  # Directorios necesarios en el worker
  systemd.tmpfiles.rules = [
    "d /var/log/slurm   0755 slurm slurm -"
    "d /var/spool/slurmd 0755 slurm slurm -"
  ];

  # Puerto del daemon de computo
  networking.firewall.allowedTCPPorts = [ 6818 ];
}
