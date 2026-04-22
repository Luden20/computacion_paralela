# NixOS Slurm Cluster — Guía de Despliegue

## Estructura del proyecto

```
.
├── flake.nix               # Entrypoint: define todos los nodos del cluster
├── configuration.nix       # Legado (referencia); usar flake.nix en su lugar
├── modules/
│   ├── common.nix          # Config base compartida (ssh, munge, tailscale, usuarios)
│   ├── slurm-master.nix    # Rol: controlador (slurmctld)
│   └── slurm-worker.nix    # Rol: nodo de computo (slurmd)
└── hosts/
    ├── master.nix          # Hardware y config especifica del master
    └── worker.nix          # Hardware y paquetes MPI de los workers
```

---

## Cómo funciona la conectividad

Todos los nodos se conectan a la misma red VPN de **Tailscale**.  
Una vez conectados, **MagicDNS** resuelve los hostnames automáticamente:

```
nix-master        →  100.x.x.10  (slurmctld)
nix-worker-01     →  100.x.x.11  (slurmd)
nix-worker-02     →  100.x.x.12  (slurmd)
```

Slurm usa los hostnames directamente — no necesitas conocer los IPs de Tailscale.  
Al arrancar, cada worker se conecta a Tailscale y se registra solo con el master.

> **Importante:** Los workers NO se auto-declaran en Slurm.  
> Debes agregarlos en `flake.nix` **antes** de desplegarlos.  
> Una vez declarados y desplegados, se conectan automáticamente.

---

## Requisitos previos

- NixOS instalado en cada nodo (master y workers)
- Acceso SSH entre el master y los workers
- Cuenta de Tailscale con **MagicDNS habilitado**:  
  👉 https://login.tailscale.com/admin/dns → activar **MagicDNS**
- Auth key de Tailscale (tipo `Reusable`, `Ephemeral: off`):  
  👉 https://login.tailscale.com/admin/settings/keys

---

## Primer despliegue (orden obligatorio)

### Paso 1 — Clonar el repo en el master

```bash
sudo git clone <tu-repo> /etc/nixos/cluster
cd /etc/nixos/cluster
```

### Paso 2 — Declarar los nodos en `flake.nix`

Edita la sección `clusterConfig` con los hostnames de tus máquinas:

```nix
clusterConfig = {
  masterHostname = "nix-master";   # debe coincidir con el hostname del master

  workers = [
    { hostname = "nix-worker-01"; }
    { hostname = "nix-worker-02"; }
  ];

  tailscaleKeyFile = "/run/secrets/tailscale_key";
};
```

Agrega también una entrada en `nixosConfigurations` por cada worker:

```nix
nix-worker-01 = mkNixosSystem {
  hostname = "worker";
  extraModules = [
    { networking.hostName = nixpkgs.lib.mkForce "nix-worker-01"; }
  ];
};
```

### Paso 3 — Ajustar CPUs y RAM en `modules/slurm-master.nix`

Corre esto en **cada worker** para obtener sus valores reales:

```bash
slurmd -C
# Salida de ejemplo:
# NodeName=nix-worker-01 CPUs=8 Boards=1 SocketsPerBoard=1 CoresPerSocket=4 ThreadsPerCore=2 RealMemory=15811
```

Actualiza `mkNodeLine` en `slurm-master.nix` con esos valores.

### Paso 4 — Generar y distribuir la clave Munge

La **misma clave** debe estar en todos los nodos. Generala en el master:

```bash
# En el MASTER:
sudo dd if=/dev/urandom bs=1 count=1024 > /etc/munge/munge.key
sudo chmod 400 /etc/munge/munge.key
sudo chown munge:munge /etc/munge/munge.key

# Copiar a cada worker:
for w in nix-worker-01 nix-worker-02; do
  sudo scp /etc/munge/munge.key CPDN@$w:/etc/munge/munge.key
  sudo ssh CPDN@$w "sudo chmod 400 /etc/munge/munge.key && sudo chown munge:munge /etc/munge/munge.key"
done
```

### Paso 5 — Poner la auth key de Tailscale en cada nodo

Ejecuta esto **localmente en cada máquina** (master y cada worker):

```bash
sudo mkdir -p /run/secrets
echo "tskey-auth-TUCLAVE" | sudo tee /run/secrets/tailscale_key > /dev/null
sudo chmod 600 /run/secrets/tailscale_key
```

> ⚠️ **Nunca pongas la auth key en el código ni en git.**  
> El archivo `/run/secrets/` vive solo en disco y no se versiona.

### Paso 6 — Desplegar el MASTER (siempre primero)

```bash
sudo nixos-rebuild switch --flake /etc/nixos/cluster#nix-master
```

Verifica que Tailscale esté activo y el master aparezca:

```bash
tailscale status
systemctl status slurmctld
```

### Paso 7 — Desplegar los WORKERS (desde el master)

El master compila la config y la envía a cada worker via SSH:

```bash
for w in nix-worker-01 nix-worker-02; do
  nixos-rebuild switch \
    --flake /etc/nixos/cluster#$w \
    --target-host CPDN@$w \
    --use-remote-sudo
done
```

Al arrancar, cada worker:
1. Se conecta a Tailscale automáticamente
2. Inicia `slurmd`
3. Se registra con el master

### Paso 8 — Verificar el cluster

```bash
sinfo                        # Ver nodos y su estado (debe mostrar "idle")
squeue                       # Cola de trabajos (vacía al inicio)
srun --nodes=2 hostname      # Test: ejecuta un comando en 2 workers
```

---

## Agregar un worker nuevo

Los workers no se auto-declaran. Sigue este orden:

**1. Editar `flake.nix`** — agregar el nuevo worker en ambos lugares:

```nix
# En clusterConfig.workers:
{ hostname = "nix-worker-03"; }

# En nixosConfigurations:
nix-worker-03 = mkNixosSystem {
  hostname = "worker";
  extraModules = [
    { networking.hostName = nixpkgs.lib.mkForce "nix-worker-03"; }
  ];
};
```

**2. Rebuild el master primero** (para que `slurmctld` conozca el nuevo nodo):

```bash
sudo nixos-rebuild switch --flake /etc/nixos/cluster#nix-master
```

**3. Preparar el nuevo nodo** (munge key + tailscale key):

```bash
sudo scp /etc/munge/munge.key CPDN@nix-worker-03:/etc/munge/munge.key
sudo ssh CPDN@nix-worker-03 "sudo chmod 400 /etc/munge/munge.key && sudo chown munge:munge /etc/munge/munge.key"
sudo ssh CPDN@nix-worker-03 "sudo mkdir -p /run/secrets && echo 'tskey-auth-TUCLAVE' | sudo tee /run/secrets/tailscale_key && sudo chmod 600 /run/secrets/tailscale_key"
```

**4. Desplegar el nuevo worker:**

```bash
nixos-rebuild switch \
  --flake /etc/nixos/cluster#nix-worker-03 \
  --target-host CPDN@nix-worker-03 \
  --use-remote-sudo
```

El worker aparecerá solo en `sinfo` una vez activo.

---

## Enviar trabajos al cluster

```bash
# Trabajo interactivo en 1 nodo:
srun --nodes=1 --ntasks=4 hostname

# Trabajo en todos los nodos:
srun --nodes=2 --ntasks-per-node=4 my_program

# Trabajo batch (script):
sbatch mi_trabajo.sh
```

Ejemplo de script batch `mi_trabajo.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=test
#SBATCH --nodes=2
#SBATCH --ntasks-per-node=4
#SBATCH --output=resultado_%j.txt

mpirun ./mi_programa_paralelo
```

---

## Comandos útiles de administración

```bash
# Estado del cluster
sinfo -N                     # Ver nodos con detalle
scontrol show nodes          # Info completa de cada nodo

# Gestionar trabajos
squeue -u CPDN               # Trabajos del usuario CPDN
scancel <job_id>             # Cancelar un trabajo

# Poner un nodo en mantenimiento
scontrol update NodeName=nix-worker-01 State=DRAIN Reason="mantenimiento"
scontrol update NodeName=nix-worker-01 State=RESUME   # volver a activar

# Tailscale
tailscale status             # Ver todos los nodos en la VPN
tailscale ping nix-worker-01 # Test de conectividad a un worker
```

---

## Seguridad

- **Auth key de Tailscale**: siempre en `/run/secrets/tailscale_key`, nunca en git
- **Clave Munge**: distribuida manualmente via scp, nunca en git
- **Contraseña del usuario**: cambia `initialPassword` por `hashedPassword` tras el primer boot:
  ```bash
  mkpasswd -m sha-512   # genera el hash
  # Luego en common.nix:
  # hashedPassword = "$6$...hash...";
  ```
- **SSH**: una vez tengas claves SSH configuradas, desactiva el login con contraseña en `common.nix`
