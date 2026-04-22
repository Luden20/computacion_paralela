# configuration.nix  ── ARCHIVO LEGADO ──────────────────────────────────────
#
# Este archivo ya NO se usa directamente. El cluster ahora se gestiona
# via flake.nix con una estructura modular.
#
# Para aplicar la configuracion en cada nodo, usa:
#
#   En el MASTER:
#     sudo nixos-rebuild switch --flake .#nix-master
#
#   En cada WORKER (desde el master via ssh):
#     sudo nixos-rebuild switch --flake .#nix-worker-01
#     sudo nixos-rebuild switch --flake .#nix-worker-02
#
# Ver README.md para instrucciones completas de despliegue.
#
# ─────────────────────────────────────────────────────────────────────────────

# Si necesitas usar este archivo directamente (sin flakes), importa los modulos:
{ config, pkgs, ... }:
{
  imports = [
    ./hardware-configuration.nix
    ./modules/common.nix
    # Descomenta el rol de este nodo:
    # ./modules/slurm-master.nix
    # ./modules/slurm-worker.nix
  ];
}
