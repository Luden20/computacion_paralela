# hosts/worker.nix
# Configuracion ESPECIFICA de los nodos worker.
# El hostname se sobreescribe en flake.nix por cada worker via `mkForce`.

{ config, pkgs, lib, clusterConfig, ... }:

{
  imports = [
    ./hardware-configuration.nix   # Generado por nixos-generate-config en CADA worker
    ../modules/slurm-worker.nix    # Rol: nodo de computo
  ];

  # El hostname base; flake.nix lo sobreescribe con mkForce para cada instancia
  networking.hostName = "nix-worker";

  # IP estatica: ajusta segun el worker (el flake puede parametrizarlo si lo necesitas)
  # networking.interfaces.eth0.ipv4.addresses = [{
  #   address      = "10.0.0.11";   # Cambia por la IP del worker especifico
  #   prefixLength = 24;
  # }];
  # networking.defaultGateway = "10.0.0.1";
  # networking.nameservers    = [ "8.8.8.8" "1.1.1.1" ];

  # Paquetes especificos para nodos de computo (MPI, etc.)
  environment.systemPackages = with pkgs; [
    openmpi    # Para trabajos paralelos con MPI
    gcc        # Compilador C/C++
    python3    # Python para scripts de trabajo
  ];
}
