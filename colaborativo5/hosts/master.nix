# hosts/master.nix
# Configuracion ESPECIFICA del nodo maestro.
# Aqui van: hardware-configuration, hostname, IP estatica, y rol Slurm.

{ config, pkgs, lib, clusterConfig, ... }:

{
  imports = [
    ./hardware-configuration.nix   # Generado por nixos-generate-config en el master
    ../modules/slurm-master.nix    # Rol: controlador de Slurm
  ];

  networking.hostName = clusterConfig.masterHostname;   # "nix-master"

  # IP estatica para el master (ajusta a tu red)
  networking.interfaces.eth0.ipv4.addresses = [{
    address      = clusterConfig.masterIp;   # "10.0.0.10"
    prefixLength = 24;
  }];
  networking.defaultGateway = "10.0.0.1";
  networking.nameservers    = [ "8.8.8.8" "1.1.1.1" ];

  # El master tambien puede tener herramientas adicionales de administracion
  environment.systemPackages = with pkgs; [
    slurmutils   # Herramientas extra de gestion Slurm (opcional)
  ];
}
