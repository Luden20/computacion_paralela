
# Guía completa Slurm (Master + Worker) — Ubuntu
>Las credenciales de las máquinas son
> - user: cpdb
> - password: thehousealwayswins

> Configuración mínima funcional con:
> - 1 nodo **master**
> - 1 nodo **worker1**
> - Autenticación con **MUNGE**
> - Resolución por nombres (`/etc/hosts`)
>
> 📌 IPs usadas:
> - MASTER → 192.168.220.129
> - WORKER → 192.168.220.130

---

# 1) INSTALAR PAQUETES (EN AMBOS NODOS)

```bash
sudo apt update
sudo apt install -y slurm-wlm munge openssh-server bsd-mailx

sudo systemctl enable ssh
sudo systemctl restart ssh
````

---

# 2) CONFIGURAR HOSTNAMES

## 🔵 En MASTER

```bash
sudo hostnamectl set-hostname master
echo master | sudo tee /etc/hostname
```

## 🟢 En WORKER

```bash
sudo hostnamectl set-hostname worker1
echo worker1 | sudo tee /etc/hostname
```

---

# 3) CONFIGURAR /etc/hosts (EN AMBOS)

```bash
sudo nano /etc/hosts
```

### Contenido (MASTER)

```text
127.0.0.1 localhost
127.0.1.1 master

192.168.220.129 master
192.168.220.130 worker1
```

### Contenido (WORKER)

```text
127.0.0.1 localhost
127.0.1.1 worker1

192.168.220.129 master
192.168.220.130 worker1
```

---

# 4) PRUEBA DE RED

```bash
ping -c 2 master
ping -c 2 worker1
```

---

#  5) CONFIGURAR MUNGE

## 🔵 En MASTER

```bash
sudo mungekey -c -f
sudo chown munge:munge /etc/munge/munge.key
sudo chmod 400 /etc/munge/munge.key

sudo systemctl enable munge
sudo systemctl restart munge
```

---

## Copiar clave al WORKER

```bash
sudo scp /etc/munge/munge.key cpdb@worker1:/tmp/munge.key
```

---

## 🟢 En WORKER

```bash
sudo mv /tmp/munge.key /etc/munge/munge.key
sudo chown munge:munge /etc/munge/munge.key
sudo chmod 400 /etc/munge/munge.key

sudo systemctl enable munge
sudo systemctl restart munge
```

---

## Probar MUNGE entre nodos

```bash
# desde MASTER
munge -n | ssh cpdb@worker1 unmunge
```

---

# ⚙️ 6) CONFIGURAR SLURM

## 🔵 En MASTER

```bash
sudo mkdir -p /etc/slurm
sudo nano /etc/slurm/slurm.conf
```

### 📄 slurm.conf

```ini
ClusterName=cluster1
SlurmctldHost=master

MpiDefault=none
ProctrackType=proctrack/pgid
ReturnToService=2
SlurmUser=slurm

StateSaveLocation=/var/spool/slurmctld
SlurmdSpoolDir=/var/spool/slurmd

AuthType=auth/munge
CryptoType=crypto/munge

SlurmctldPort=6817
SlurmdPort=6818

SwitchType=switch/none
SchedulerType=sched/backfill

SelectType=select/cons_tres
SelectTypeParameters=CR_Core

MailProg=/usr/bin/mail

NodeName=worker1 NodeAddr=192.168.220.130 NodeHostname=worker1 CPUs=2 RealMemory=2000 State=UNKNOWN

PartitionName=debug Nodes=worker1 Default=YES MaxTime=INFINITE State=UP
```

---

#  7) CREAR DIRECTORIOS

## 🔵 MASTER

```bash
sudo mkdir -p /var/spool/slurmctld
sudo chown slurm:slurm /var/spool/slurmctld
```

## 🟢 WORKER

```bash
sudo mkdir -p /var/spool/slurmd
sudo chown slurm:slurm /var/spool/slurmd
```

---

#  8) COPIAR CONFIG AL WORKER

```bash
# desde MASTER
sudo scp /etc/slurm/slurm.conf cpdb@worker1:/tmp/slurm.conf
```

```bash
# en WORKER
sudo mkdir -p /etc/slurm
sudo mv /tmp/slurm.conf /etc/slurm/slurm.conf
```

---

#  9) LEVANTAR SERVICIOS

## 🔵 MASTER

```bash
sudo systemctl enable slurmctld
sudo systemctl restart slurmctld
sudo systemctl status slurmctld
```

## 🟢 WORKER

```bash
sudo systemctl enable slurmd
sudo systemctl restart slurmd
sudo systemctl status slurmd
```

---

#  10) VERIFICACIÓN FINAL

## Desde MASTER

```bash
sinfo
scontrol show nodes
```

---

#  11) PRUEBA DE EJECUCIÓN

```bash
srun -N1 -n1 hostname
```

✔ Resultado esperado:

```text
worker1
```

---

---

# ✅ ESTADO FINAL

Si todo está bien:

```bash
sinfo
```

Debe mostrar:

```text
debug* up infinite 1 idle worker1
```

---


```bash
sudo journalctl -u slurmd -xe --no-pager
sudo journalctl -u slurmctld -xe --no-pager
```
# Para agregar un nodo clonando 
````markdown
# Agregar un worker clonado a Slurm

## 1. En el clon, cambiar hostname
```bash
sudo hostnamectl set-hostname worker2
echo worker2 | sudo tee /etc/hostname
````

## 2. Ajustar `/etc/hosts` con el nuevo nodo y actualizarlo en todos lados como corresponda 

```bash
sudo nano /etc/hosts
```

```text
127.0.0.1 localhost 
127.0.1.1 worker2   //Depende del rol del nodo

192.168.220.129 master
192.168.220.130 worker1
192.168.220.131 worker2
```

## 3. Verificar que el clon tenga IP distinta

```bash
ip a
```

## 4. En el master, agregar el nodo a `slurm.conf`

```bash
sudo nano /etc/slurm/slurm.conf
```

```ini
NodeName=worker1 NodeAddr=192.168.220.130 NodeHostname=worker1 CPUs=2 RealMemory=2000 State=UNKNOWN
NodeName=worker2 NodeAddr=192.168.220.131 NodeHostname=worker2 CPUs=2 RealMemory=2000 State=UNKNOWN

PartitionName=debug Nodes=worker1,worker2 Default=YES MaxTime=INFINITE State=UP
```

## 5. Copiar config al clon

```bash
sudo scp /etc/slurm/slurm.conf cpdb@worker2:/tmp/slurm.conf
```

En `worker2`:

```bash
sudo mkdir -p /etc/slurm /var/spool/slurmd
sudo mv /tmp/slurm.conf /etc/slurm/slurm.conf
sudo chown slurm:slurm /var/spool/slurmd
```

## 6. Levantar servicios

En `worker2`:

```bash
sudo systemctl restart munge
sudo systemctl enable slurmd
sudo systemctl restart slurmd
```

En `master`:

```bash
sudo systemctl restart slurmctld
```

## 7. Probar

En `master`:

```bash
sinfo
srun -N2 -n2 hostname
```

