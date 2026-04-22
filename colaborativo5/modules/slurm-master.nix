# modules/slurm-master.nix
# Modulo del nodo MAESTRO: corre slurmctld (controlador de trabajos).
# Este nodo NO ejecuta trabajos directamente (solo los planifica).

{ config, pkgs, lib, clusterConfig, ... }:

let
  # Construye la lista de nodos para slurm.conf
  workerNodeNames = map (w: w.hostname) clusterConfig.workers;
  allWorkerNodes  = builtins.concatStringsSep "," workerNodeNames;

  # Con Tailscale, cada nodo se identifica por su hostname.
  # MagicDNS traduce el hostname a la IP 100.x.x.x de Tailscale.
  # NodeAddr=<hostname> le dice a Slurm que use ese nombre para conectarse.
  mkNodeLine = w:
    "${w.hostname} NodeAddr=${w.hostname} CPUs=4 RealMemory=8000 " +
    "Sockets=1 CoresPerSocket=4 ThreadsPerCore=1 State=UNKNOWN";
in
{
  services.slurm = {
    server.enable = true;   # Activa slurmctld

    # slurm.conf compartido (master y workers deben tener el mismo archivo)
    clusterName = "nixcluster";
    controlMachine = clusterConfig.masterHostname;

    # Configuracion de los nodos de computo.
    # NodeAddr=<hostname> hace que Slurm conecte via Tailscale MagicDNS.
    # IMPORTANTE: ajusta CPUs/RealMemory con el valor real de: slurmd -C
    nodeName = map mkNodeLine clusterConfig.workers;
    # Ejemplo de lo que genera mkNodeLine:
    # "nix-worker-01 NodeAddr=nix-worker-01 CPUs=4 RealMemory=8000 ..."

    # Particiones (colas de trabajos)
    partitionName = [
      "debug Nodes=${allWorkerNodes} Default=YES MaxTime=INFINITE State=UP"
    ];

    extraConfig = ''
      # Politica de planificacion
      SchedulerType=sched/backfill
      SelectType=select/cons_tres
      SelectTypeParameters=CR_Core_Memory

      # Logging
      SlurmctldLogFile=/var/log/slurm/slurmctld.log
      SlurmdLogFile=/var/log/slurm/slurmd.log
      SlurmctldDebug=info
      SlurmdDebug=info

      # Directorio de trabajo temporal de Slurm
      SlurmdSpoolDir=/var/spool/slurmd
      StateSaveLocation=/var/lib/slurm/slurmctld

      # Autenticacion via Munge
      AuthType=auth/munge
      CryptoType=crypto/munge
    '';
  };

  # Asegura que los directorios de log y estado existan
  systemd.tmpfiles.rules = [
    "d /var/log/slurm  0755 slurm slurm -"
    "d /var/lib/slurm  0755 slurm slurm -"
  ];

  # Abre el puerto del controlador
  networking.firewall.allowedTCPPorts = [ 6817 ];
}
