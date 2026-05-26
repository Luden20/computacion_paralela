# Computación distribuida en Ray
Este proyecto implementa un sistema de procesamiento distribuido de secuencias de ADN utilizando Ray sobre un cluster conformado por 3 máquinas virtuales en Linux.
El objetivo fue comparar el rendimiento secuencial y distribuido utilizando archivos de longitudes variables mediante métricas como speedup, eficiencia y tolerancia a fallos.

---

## Objetivo del Laboratorio

El objetivo de este laboratorio es diseñar e implementar un sistema de computación distribuida capaz de analizar y procesar una cadena de ADN de aproximadamente 1 GB, distribuyendo la carga de trabajo entre tres nodos virtuales. La idea central es que en lugar de que una sola máquina procese todo el archivo, el trabajo se reparte entre varias máquinas que trabajan en paralelo, reduciendo el tiempo total de procesamiento.

| Nodo | Rol | IP |
|---|---|---|
| ha1 | Nodo maestro / head node de Ray | 192.168.253.128 |
| ha2 | Nodo trabajador | 192.168.56.12 |
| ha3 | Nodo trabajador | 192.168.56.13 |

El sistema realiza las siguientes tareas:
- **Generación de una cadena de ADN de 1 GB**: se crea un archivo de texto con secuencias aleatorias de las bases A, T, C y G.
- **Fragmentación del archivo**: el archivo grande se divide en trozos más pequeños (chunks) para distribuirlos.
- **Conteo de bases A/T/C/G**: cada nodo cuenta cuántas veces aparece cada base en su fragmento.
- **Búsqueda de patrones genéticos**: se buscan subcadenas específicas como ATGCGT, TATA o GATTACA.
- **Consolidación de resultados**: los resultados parciales de cada nodo se suman para obtener el resultado global.
- **Comparación entre ejecución secuencial y distribuida**: se mide el tiempo de ambos enfoques para calcular el speedup.
- **Medición de speedup y eficiencia**: se evalúa qué tan útil fue distribuir el trabajo.
- **Validación de integridad**: se verifica que los resultados distribuidos sean idénticos a los secuenciales.
- **Prueba básica de tolerancia a fallos**: se observa cómo Ray reacciona cuando un nodo se desconecta.

---

## Relación con el laboratorio anterior

Este laboratorio parte del entorno creado previamente con **VirtualBox + CentOS Stream 9**, donde ya existen los nodos ha1 y ha2. En el laboratorio anterior se configuró la red Host-Only para la comunicación entre nodos, utilizando el rango de IPs `192.168.56.x`, mientras que la interfaz NAT se mantiene para salida a internet.

Para este laboratorio se agrega un tercer nodo ha3 con IP `192.168.56.13`. Es importante entender que la IP virtual `192.168.56.100` que se usó en el laboratorio de alta disponibilidad con Pacemaker **no se debe usar para Ray**, ya que esa IP puede moverse dinámicamente entre nodos y Ray necesita una dirección fija y estable para el nodo maestro.

---

## Verificación del entorno

Estos pasos se realizan **antes de instalar Ray**. Es fundamental asegurarse de que los tres nodos se pueden comunicar entre sí, tienen los nombres correctos y las IPs esperadas. Si esta base no está bien configurada, Ray no podrá formar el clúster.

### Verificar hostname

El hostname es el nombre con el que cada máquina se identifica en la red. En un clúster es importante que cada nodo tenga un nombre único y reconocible. Se verifica así en cada nodo:

```bash
hostname
```

Resultados esperados: `ha1` en el primer nodo, `ha2` en el segundo y `ha3` en el tercero. Si ha3 todavía no tiene el nombre correcto (por ejemplo, si fue clonado de otra VM y heredó su nombre), se corrige con:

```bash
sudo hostnamectl set-hostname ha3
exec bash
```

El comando `hostnamectl set-hostname` cambia el hostname de forma permanente en sistemas con systemd. El `exec bash` recarga la sesión de terminal para que el cambio se refleje de inmediato sin necesidad de cerrar sesión.

### Verificar direcciones IP

Cada nodo debe tener asignada una IP estática en la red Host-Only para que la comunicación entre ellos sea siempre predecible. Se revisa con:

```bash
ip a
```

Este comando muestra todas las interfaces de red del sistema y sus IPs asignadas. Se debe verificar:

| Nodo | IP esperada |
|---|---|
| ha1 | 192.168.253.128 |
| ha2 | 192.168.56.12 |
| ha3 | 192.168.56.13 |

Si ha3 aún no tiene IP estática en la red Host-Only, primero se identifican las conexiones de red disponibles:

```bash
nmcli con show
nmcli device status
```

`nmcli` es la herramienta de línea de comandos para gestionar NetworkManager en CentOS/RHEL. `nmcli con show` lista todas las conexiones configuradas con sus nombres y UUIDs. `nmcli device status` muestra los dispositivos de red físicos y su estado actual (conectado, desconectado, etc.). Con esa información se identifica cuál es la interfaz de la red Host-Only (generalmente `enp0s8`, pero puede variar según la configuración de VirtualBox).

Una vez identificada la interfaz, se configura la IP estática:

```bash
sudo nmcli con mod "enp0s8" ipv4.addresses 192.168.56.13/24
sudo nmcli con mod "enp0s8" ipv4.method manual
sudo nmcli con mod "enp0s8" ipv4.gateway ""
sudo nmcli con mod "enp0s8" ipv4.dns ""
sudo nmcli con up "enp0s8"
```

- `ipv4.addresses 192.168.56.13/24`: asigna la IP `192.168.56.13` con máscara `/24` (es decir, `255.255.255.0`), lo que significa que todos los nodos en el rango `192.168.56.x` están en la misma red y pueden comunicarse directamente.
- `ipv4.method manual`: indica que la IP es estática y no se obtendrá por DHCP. Sin esto, la IP podría cambiar al reiniciar.
- `ipv4.gateway ""` y `ipv4.dns ""`: se dejan vacíos porque esta interfaz es solo para comunicación interna entre nodos, no para salida a internet. La salida a internet se hace por la interfaz NAT.
- `nmcli con up "enp0s8"`: aplica los cambios y levanta la conexión.

### Configurar /etc/hosts

El archivo `/etc/hosts` es una tabla local de resolución de nombres. Cuando una aplicación quiere conectarse a `ha2`, el sistema operativo primero consulta este archivo antes de preguntar a un servidor DNS. Esto es crucial en un clúster porque garantiza que los nombres `ha1`, `ha2` y `ha3` siempre resuelvan a las IPs correctas, sin depender de infraestructura DNS externa.

Se edita en los tres nodos:

```bash
sudo nano /etc/hosts
```

Se agregan o verifican estas líneas:

```
192.168.253.128 ha1
192.168.56.12 ha2
192.168.56.13 ha3
192.168.56.100 cluster-vip
```

Guardar con `Ctrl+O`, confirmar con `Enter`, salir con `Ctrl+X`.

Con esto configurado, comandos como `ping ha2` o `ssh ha3` funcionan usando nombres en lugar de IPs, lo que hace la administración del clúster más cómoda y menos propensa a errores tipográficos.

### Probar comunicación entre nodos

Una vez configuradas las IPs y el archivo hosts, se verifica que los nodos efectivamente se pueden alcanzar entre sí:

```bash
# Desde ha1
ping -c 4 ha2
ping -c 4 ha3

# Desde ha2
ping -c 4 ha1
ping -c 4 ha3

# Desde ha3
ping -c 4 ha1
ping -c 4 ha2
```

El flag `-c 4` indica que se envían exactamente 4 paquetes ICMP y luego se detiene (sin él, ping corre indefinidamente). El resultado esperado es `4 packets transmitted, 4 received, 0% packet loss`, lo que confirma que no hay pérdida de paquetes y la latencia es baja.

Si algún ping falla, se diagnostica con:

```bash
ip a              # verificar que la IP está asignada correctamente
cat /etc/hosts    # verificar que el nombre resuelve a la IP correcta
nmcli device status  # verificar que la interfaz de red está activa
```

---

## Instalación de dependencias

Una vez verificada la comunicación entre nodos, se instalan las herramientas necesarias. Esto se ejecuta en **los tres nodos** (ha1, ha2 y ha3), ya que todos necesitan las mismas dependencias para poder ejecutar código Python y formar parte del clúster Ray.

```bash
sudo dnf update -y
sudo dnf install -y python3 python3-pip python3-devel gcc make wget curl nano vim net-tools bind-utils nmap-ncat firewalld
```

- `dnf update -y`: actualiza todos los paquetes del sistema a sus versiones más recientes. El `-y` confirma automáticamente todas las preguntas para no tener que hacerlo manualmente.
- `python3`: el intérprete de Python 3, necesario para ejecutar Ray y los scripts del laboratorio.
- `python3-pip`: el gestor de paquetes de Python, necesario para instalar Ray con `pip install`.
- `python3-devel`: cabeceras y archivos de desarrollo de Python, necesarios para compilar extensiones nativas que algunos paquetes de Ray usan.
- `gcc` y `make`: compilador de C y herramienta de construcción, requeridos para compilar dependencias con código nativo.
- `wget` y `curl`: herramientas para descargar archivos desde la terminal.
- `nano` y `vim`: editores de texto para modificar archivos de configuración.
- `net-tools`: incluye comandos clásicos como `ifconfig` y `netstat` para diagnóstico de red.
- `bind-utils`: incluye `nslookup` y `dig` para diagnosticar resolución de nombres DNS.
- `nmap-ncat`: incluye `nc` (netcat), que se usa más adelante para probar conectividad a puertos específicos de Ray.
- `firewalld`: el servicio de firewall de CentOS que se configura para abrir los puertos que Ray necesita.

Habilitar el firewall si no está activo:

```bash
sudo systemctl enable --now firewalld
```

`systemctl enable` hace que el servicio se inicie automáticamente en cada arranque del sistema. `--now` además lo inicia de inmediato sin esperar al próximo reinicio.

### Crear entorno virtual e instalar Ray

Un entorno virtual de Python es un directorio aislado que contiene su propia instalación de Python y sus propios paquetes. Esto evita conflictos entre versiones de librerías y mantiene el sistema operativo limpio. Se crea y activa así:

```bash
python3 -m venv ~/ray-dna
source ~/ray-dna/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -U "ray[default]"
```

- `python3 -m venv ~/ray-dna`: crea el entorno virtual en la carpeta `ray-dna` dentro del home del usuario. Dentro de esa carpeta se instalarán todos los paquetes de Python de este proyecto.
- `source ~/ray-dna/bin/activate`: activa el entorno virtual. Después de esto, cualquier comando `python` o `pip` usará el entorno aislado en lugar del sistema. El prompt del terminal cambia para mostrar `(ray-dna)` indicando que el entorno está activo.
- `pip install --upgrade pip setuptools wheel`: actualiza las herramientas base del entorno antes de instalar Ray, para evitar errores de compatibilidad durante la instalación.
- `pip install -U "ray[default]"`: instala Ray con todas sus dependencias estándar. La notación `[default]` incluye el dashboard web y otras herramientas útiles. La flag `-U` asegura que se instale la versión más reciente.

Verificar que Ray quedó correctamente instalado:

```bash
python -c "import ray; print(ray.__version__)"
```

Esto importa Ray en Python e imprime su versión. Si no da error, la instalación fue exitosa.

---

## Configuración de firewall para Ray

Ray usa múltiples puertos para la comunicación interna entre sus componentes. Por defecto, el firewall de CentOS bloquea todos los puertos que no estén explícitamente permitidos. Este laboratorio fija puertos específicos (en lugar de dejar que Ray los elija aleatoriamente) para poder abrirlos de forma controlada en el firewall.

Ejecutar en **ha1, ha2 y ha3**:

```bash
sudo firewall-cmd --permanent --add-port=6379/tcp
sudo firewall-cmd --permanent --add-port=8265/tcp
sudo firewall-cmd --permanent --add-port=8076-8078/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --permanent --add-port=10001-10100/tcp
sudo firewall-cmd --permanent --add-port=52365-52366/tcp
sudo firewall-cmd --reload
```

- `--permanent`: hace que la regla persista después de reiniciar el sistema. Sin esta flag, la regla solo dura hasta el próximo reinicio.
- `--add-port=6379/tcp`: abre el puerto 6379, que es el puerto principal del nodo cabeza de Ray (el GCS - Global Control Store). Los nodos trabajadores se conectan a este puerto para unirse al clúster.
- `--add-port=8265/tcp`: abre el puerto del dashboard web de Ray, que permite monitorear el clúster desde un navegador.
- `--add-port=8076-8078/tcp`: abre un rango de puertos para el Object Manager (transferencia de objetos entre nodos), el Node Manager (coordinación de workers) y el Runtime Env Agent (gestión del entorno de ejecución).
- `--add-port=8080/tcp`: puerto para exportación de métricas de Ray.
- `--add-port=10001-10100/tcp`: rango de puertos para los workers de Ray. Cada worker ocupa un puerto de este rango.
- `--add-port=52365-52366/tcp`: puertos para el agente del dashboard.
- `--reload`: aplica los cambios al firewall activo sin necesidad de reiniciar el servicio.

Verificar que todos los puertos quedaron abiertos:

```bash
sudo firewall-cmd --list-ports
```

Deben aparecer: `6379/tcp 8265/tcp 8076-8078/tcp 8080/tcp 10001-10100/tcp 52365-52366/tcp`

---

## Inicialización del Clúster Ray

Con el entorno preparado, se inicia el clúster Ray. El clúster tiene una arquitectura jerárquica: hay un nodo maestro (head node) que coordina todo, y nodos trabajadores que ejecutan las tareas. El nodo maestro se inicia primero, y luego los trabajadores se conectan a él.

### Nodo Maestro ha1

El nodo maestro es el cerebro del clúster. Mantiene el estado global, asigna tareas a los workers, y expone el dashboard. Se inicia con:

```bash
source ~/ray-dna/bin/activate
ray stop
ray start --head \
  --node-ip-address=192.168.253.128 \
  --port=6379 \
  --dashboard-host=0.0.0.0 \
  --dashboard-port=8265 \
  --object-manager-port=8076 \
  --node-manager-port=8077 \
  --runtime-env-agent-port=8078 \
  --metrics-export-port=8080 \
  --ray-client-server-port=10001 \
  --dashboard-agent-listen-port=52365 \
  --dashboard-agent-grpc-port=52366 \
  --min-worker-port=10002 \
  --max-worker-port=10100
```

Explicación de cada parámetro:

- `ray stop`: detiene cualquier instancia de Ray que pudiera estar corriendo antes de iniciar una nueva. Evita conflictos con procesos anteriores.
- `--head`: le indica a Ray que este nodo será el coordinador central del clúster. Sin esta flag, Ray intentaría unirse a un clúster existente en lugar de crear uno nuevo.
- `--node-ip-address=192.168.253.128`: especifica la IP que los demás nodos usarán para conectarse a este nodo maestro. Es importante usar la IP de la red interna del clúster, no la IP de la NAT.
- `--port=6379`: el puerto del GCS (Global Control Store), que es el servicio central de Ray que mantiene el estado del clúster. Los workers se conectan a este puerto al unirse.
- `--dashboard-host=0.0.0.0`: indica que el dashboard web debe escuchar en todas las interfaces de red (no solo en localhost), permitiendo acceder a él desde la máquina anfitrión.
- `--dashboard-port=8265`: el puerto donde se sirve el dashboard web. Se accede desde el navegador en `http://192.168.253.128:8265`.
- `--object-manager-port=8076`: puerto para el Object Manager, el componente que transfiere objetos (datos) entre nodos cuando una tarea necesita datos que están en otro nodo.
- `--node-manager-port=8077`: puerto para el Node Manager, que coordina el ciclo de vida de los workers en este nodo (cuántos levantar, cuándo terminarlos, etc.).
- `--runtime-env-agent-port=8078`: puerto para el agente que gestiona el entorno de ejecución de las tareas (variables de entorno, dependencias, etc.).
- `--metrics-export-port=8080`: puerto por donde Ray exporta métricas de rendimiento (uso de CPU, memoria, número de tareas, etc.).
- `--ray-client-server-port=10001`: puerto para el Ray Client, que permite conectarse al clúster desde código Python externo al clúster.
- `--dashboard-agent-listen-port=52365` y `--dashboard-agent-grpc-port=52366`: puertos que usa el agente del dashboard en cada nodo para comunicarse con el proceso central del dashboard.
- `--min-worker-port=10002` y `--max-worker-port=10100`: define el rango de puertos disponibles para los procesos worker de Ray. Cada worker ocupa un puerto único dentro de este rango.

Verificar que el nodo maestro quedó activo:

```bash
ray status
```

También se puede abrir el dashboard desde el navegador del equipo anfitrión:
```
http://192.168.253.128:8265
```

**Pregunta del laboratorio — ¿Qué hacen estas opciones?**
- `--node-ip-address`: le dice a Ray en qué IP tiene que escuchar y a la que los demás nodos se conectarán. Sin esto, Ray podría usar una IP incorrecta si el nodo tiene múltiples interfaces.
- `--dashboard-host`: define en qué interfaz escucha el dashboard. Con `0.0.0.0` acepta conexiones desde cualquier IP, no solo desde localhost.
- `--dashboard-port`: el número de puerto donde el dashboard web estará disponible.
- `--object-manager-port`: el canal por donde se transfieren los objetos (datos) entre nodos del clúster.
- `--node-manager-port`: el canal por donde se coordina la gestión de los workers locales del nodo.
- `--min-worker-port` / `--max-worker-port`: delimitan el rango de puertos usados por los workers, lo que es necesario para poder abrirlos correctamente en el firewall.

---

### Nodo Trabajador ha2

Los nodos trabajadores no tienen estado global; su único rol es recibir y ejecutar tareas que el nodo maestro les asigna. Se unen al clúster apuntando a la IP y puerto del maestro:

```bash
source ~/ray-dna/bin/activate && ray stop --force && ray start \
  --address='192.168.253.128:6379' \
  --node-ip-address=192.168.253.129 \
  --object-manager-port=8076 \
  --node-manager-port=8077 \
  --runtime-env-agent-port=8078 \
  --metrics-export-port=8080 \
  --dashboard-agent-listen-port=52365 \
  --dashboard-agent-grpc-port=52366 \
  --min-worker-port=10002 \
  --max-worker-port=10100
```

- `ray stop --force`: fuerza la detención de cualquier proceso Ray activo antes de unirse. La flag `--force` es más agresiva que `ray stop` y mata los procesos inmediatamente si no responden.
- `--address='192.168.253.128:6379'`: la dirección del nodo maestro. Esto le dice a Ray "únete al clúster cuyo head node está en esa IP y puerto".
- `--node-ip-address=192.168.253.129`: la IP propia de ha2. Ray necesita saber en qué IP escuchar para que el maestro pueda comunicarse de vuelta con este nodo.
- El resto de los puertos tienen el mismo rol que en el nodo maestro, pero ahora aplican a este nodo trabajador.

---

### Nodo Trabajador ha3

Igual que ha2, pero con su propia IP:

```bash
source ~/ray-dna/bin/activate && ray stop --force && ray start \
  --address='192.168.253.128:6379' \
  --node-ip-address=192.168.253.130 \
  --object-manager-port=8076 \
  --node-manager-port=8077 \
  --runtime-env-agent-port=8078 \
  --metrics-export-port=8080 \
  --dashboard-agent-listen-port=52365 \
  --dashboard-agent-grpc-port=52366 \
  --min-worker-port=10002 \
  --max-worker-port=10100
```

Una vez que ha2 y ha3 se unen, Ray puede distribuir tareas entre los tres nodos de forma automática y transparente. El programador no necesita especificar en qué nodo corre cada tarea; Ray lo decide según la disponibilidad de recursos.

### Verificar el clúster

Desde ha1:

```bash
ray status
```

Debe mostrar los tres nodos activos con sus recursos disponibles (CPU, memoria). También se puede verificar la conectividad al puerto del maestro desde ha2 o ha3:

```bash
nc -vz ha1 6379
# Resultado esperado: Connection to ha1 6379 port [tcp/*] succeeded!
```

`nc` (netcat) intenta abrir una conexión TCP al host y puerto indicados. Si tiene éxito, significa que el puerto está abierto y accesible, confirmando que el firewall está bien configurado y el nodo maestro está escuchando.

---

## Preparar directorio de trabajo

Este paso se realiza **únicamente en ha1**, ya que es el nodo desde donde se ejecutarán todos los scripts. Los nodos trabajadores no necesitan tener los archivos de datos ni los scripts; Ray se encarga de distribuir el código y los datos a los workers automáticamente.

```bash
mkdir -p ~/dna-distribuido/{src,data,results}
cd ~/dna-distribuido
```

- `mkdir -p`: crea el directorio y todos sus padres si no existen. La flag `-p` evita errores si el directorio ya existe.
- `~/dna-distribuido/{src,data,results}`: usa la expansión de llaves de bash para crear tres subdirectorios de una vez: `src` para los scripts Python, `data` para los archivos de ADN, y `results` para los JSONs con resultados.

Estructura esperada:
```
dna-distribuido/
├── data/      ← archivos de ADN generados
├── results/   ← JSONs con resultados de cada ejecución
└── src/       ← scripts Python del proyecto
```

---

## Generar archivos de ADN

Para este laboratorio no se usan secuencias de ADN reales, sino archivos generados aleatoriamente con las cuatro bases nucleotídicas (A, T, C, G). El script `generador.py` se descarga del aula virtual y se coloca en `src/`.

```bash
source ~/ray-dna/bin/activate

# Primero probar con 200 MB
python src/generador.py --output data/dna_200mb.txt --size-mb 200

# Luego generar 1 GB
python src/generador.py --output data/dna_1gb.txt --size-mb 1024
```

- `--output`: ruta donde se guardará el archivo generado.
- `--size-mb`: tamaño del archivo en megabytes. 200 MB sirve para pruebas rápidas; 1024 MB (1 GB) es el tamaño objetivo del laboratorio.

El generador produce texto plano con caracteres A, T, C y G distribuidos uniformemente al azar. Se generan primero 200 MB para verificar que todo funciona correctamente antes de esperar los minutos que toma generar 1 GB.

Verificar que los archivos fueron creados:

```bash
ls -lh data/
```

`ls -lh` lista los archivos en formato largo (`-l`) con tamaños en formato legible por humanos (`-h`, por ejemplo `1.0G` en lugar de `1073741824`).

---

## Consideraciones importantes

### La IP virtual del laboratorio HA no se usa para Ray

En el laboratorio anterior de alta disponibilidad se creó una IP virtual `192.168.56.100` gestionada por Pacemaker. Esta IP se asigna dinámicamente al nodo que esté activo en ese momento y puede "flotar" entre ha1 y ha2. **Esta IP no se debe usar como dirección del nodo maestro de Ray**, porque Ray necesita una dirección fija. Si Ray se inicia apuntando a `192.168.56.100` y esa IP se mueve a otro nodo por un failover de Pacemaker, el clúster Ray se rompería.

Para Ray siempre se usa la IP física y estable de ha1: `192.168.253.128`.

### Ray no convierte el sistema en alta disponibilidad

Ray es un framework de **cómputo distribuido**, no de **alta disponibilidad**. La diferencia es importante:

- **Alta disponibilidad (Pacemaker/Corosync)**: si un nodo falla, el servicio migra automáticamente a otro nodo. El servicio sigue disponible para los usuarios.
- **Cómputo distribuido (Ray)**: el trabajo se reparte entre nodos para ejecutarse más rápido. Si el nodo maestro (ha1) falla, el clúster Ray completo se detiene.

Ray sí tiene tolerancia a fallos para los nodos **trabajadores**: si ha2 o ha3 se caen, Ray puede reintentar las tareas que estaban ejecutando en esos nodos usando el parámetro `max_retries`. Pero esto no hace que el sistema sea altamente disponible; solo evita que un fallo temporal de un worker arruine toda la ejecución.

---

## Configuración de GitHub CLI

Para sincronizar los scripts del laboratorio se usa la CLI de GitHub, que permite clonar repositorios y gestionar código directamente desde la terminal.

```bash
sudo dnf install git -y

sudo dnf install 'dnf-command(config-manager)'

sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo

sudo dnf install gh
```

- `dnf install git`: instala Git, el sistema de control de versiones necesario para clonar repositorios.
- `dnf install 'dnf-command(config-manager)'`: instala el plugin `config-manager` de dnf, que permite agregar repositorios externos desde la línea de comandos.
- `dnf config-manager --add-repo`: agrega el repositorio oficial de GitHub CLI al sistema, para que dnf pueda descargar e instalar `gh`.
- `dnf install gh`: instala la herramienta `gh`, la interfaz de línea de comandos oficial de GitHub.

---

## Ejecución del Proyecto

Con el repositorio clonado en ha1, el script principal se ejecuta así:

```bash
python src/main.py --input data/dna_200mb.txt --patterns ATGCGT,TATA,GATTACA --chunk-mb 32 --output results/distribuido_200mb.json
```

---

## Implementación secuencial y distribuida

Los scripts `secuencial.py` y `dna_ray.py` se obtienen del aula virtual y se colocan en `src/` de ha1.

### Ejecución secuencial

La versión secuencial procesa el archivo completo en un solo nodo, sin distribuir trabajo. Sirve como línea base para comparar cuánto tiempo tarda el enfoque tradicional:


Aunque se usa `--chunk-mb 32`, en la versión secuencial los chunks se procesan uno por uno en el mismo proceso, sin paralelismo. Este parámetro existe para que la comparación con la versión distribuida sea justa (ambas usan los mismos tamaños de fragmento).

### Ejecución distribuida

La versión distribuida usa Ray para enviar cada chunk a un nodo diferente del clúster. Todos los chunks se procesan en paralelo, y al final los resultados parciales se suman:



Internamente el script implementa el patrón **divide y vencerás**:
1. **Fragmentar**: divide el archivo en trozos de 32 MB.
2. **Distribuir**: envía cada trozo a un nodo del clúster usando `ray.remote`.
3. **Procesar en paralelo**: cada nodo cuenta bases y busca patrones en su trozo de forma simultánea.
4. **Consolidar**: el nodo maestro recoge los resultados parciales y los suma para obtener el resultado global.

Verificar que la carga se distribuyó entre los nodos:

```bash
cat results/distribuido_200mb.json
```

Debe aparecer una sección como esta:
```json
"chunks_processed_by_worker": {
    "ha1": 2,
    "ha2": 2,
    "ha3": 3
}
```

Esto confirma que los tres nodos procesaron chunks, no solo uno. Los números pueden variar según cómo Ray asignó los fragmentos.

Durante la ejecución del archivo de 1 GB se puede monitorear el clúster en tiempo real desde el navegador en `http://192.168.253.128:8265`, donde se puede observar: nodos activos, uso de CPU por nodo, tareas en vuelo y distribución de carga.

---

## Parámetros del Script

El script principal recibe cuatro parámetros clave:

- `--input`: ruta al archivo de ADN a procesar (texto plano con bases A, T, C, G).
- `--patterns`: las secuencias genéticas a buscar, separadas por comas (ATGCGT, TATA, GATTACA). Cada patrón se busca en cada fragmento de forma independiente.
- `--chunk-mb 32`: tamaño de cada fragmento en megabytes. Un valor de 32 MB significa que un archivo de 1 GB se divide en ~32 chunks. Fragmentos más pequeños permiten mayor paralelismo pero aumentan el overhead de coordinación.
- `--output`: ruta donde se guarda el JSON con los resultados consolidados de todos los nodos.

---

## Archivos a Utilizar

Se generaron 3 archivos de diferentes tamaños para comparar el comportamiento del sistema bajo distintas cargas:

| Archivo de entrada | Patrones | Chunk MB | Núcleos | Tiempo secuencial (s) | Tiempo distribuido (s) | Speedup | Eficiencia |
|---|---|---:|---:|---:|---:|---:|---:|
| data/dna_200mb.txt | ATGCGT, TATA, GATTACA | 32 | 6 | 3.2311 | 4.3855 | 0.7368 | 0.1228 |
| data/dna_1gb.txt | ATGCGT, TATA, GATTACA | 32 | 6 | 19.1811 | 13.1015 | 1.4640 | 0.3660 |
| data/dna_10gb.txt | ATGCGT, TATA, GATTACA | 32 | 6 | 227.3990 | 159.2666 | 1.4278 | 0.2380 |

Durante la ejecución del archivo de 10 GB ocurrió una desconexión inesperada de nodos debido a saturación de recursos. Cada nodo contaba con 2 CPU y 4 GB de RAM, recursos que resultaron insuficientes bajo cargas elevadas. Como consecuencia, los procesos de heartbeat dejaron de responder correctamente y los nodos ha2 y ha3 fueron desconectados temporalmente del clúster. Posteriormente, los nodos fueron reintegrados y asumieron nuevamente carga de trabajo de manera automática.

---

## Análisis de Resultados

### 200 MB

Con 200 MB, el procesamiento distribuido fue **más lento** que el secuencial (4.38 s vs 3.23 s, speedup de 0.74). Esto se explica por la **Ley de Amdahl**: cuando el volumen de datos es pequeño, el overhead de comunicación entre nodos supera el beneficio de paralelizar.

El overhead de Ray incluye:
- Serializar los datos de cada chunk para enviarlos por la red.
- Transferir los chunks a los nodos trabajadores.
- Coordinar qué worker procesa qué chunk.
- Recoger y deserializar los resultados parciales.

Cuando la tarea tarda apenas 3 segundos, todo ese overhead representa una fracción significativa del tiempo total. No vale la pena distribuir una tarea tan pequeña.

---

### 1 GB y 10 GB

Con 1 GB y 10 GB, el procesamiento distribuido supera claramente al secuencial, logrando un **speedup de ~1.43–1.46x**. A mayor volumen de datos, la fracción paralela del trabajo domina sobre el overhead fijo de comunicación, y la distribución comienza a rendir sus beneficios.

La **eficiencia** (speedup / número de núcleos) es relativamente baja (~0.24–0.37) porque cada nodo tenía solo 2 CPU y 4 GB de RAM. Con más recursos por nodo (o más nodos), el speedup y la eficiencia mejorarían. La eficiencia perfecta sería 1.0, lo que significaría que cada núcleo adicional aporta exactamente su capacidad máxima al rendimiento total.

Con esto en cuenta, el tiempo distribuido sigue siendo mejor que el secuencial y con pruebas más intensivas se podría mejorar aún más. El secuencial es mejor solo con el archivo de 200 MB, ya que en esa escala el overhead de la comunicación entre procesos es mayor que el beneficio que se obtiene al paralelizar la tarea. Al aumentar la fracción paralela, los resultados mejoran en tiempo.

---

## Tolerancia a Fallos

Durante la ejecución del archivo de 10 GB, ha2 y ha3 se desconectaron por saturación de recursos. Los procesos de **heartbeat** de Ray (señales periódicas que cada nodo envía al maestro para indicar que sigue activo) fallaron porque la CPU y RAM estaban al límite y los procesos no podían responder a tiempo.

Lo destacable es que al reconectarlos, Ray los **reintegró automáticamente** al clúster y les asignó nuevas cargas de trabajo de inmediato, sin necesidad de reiniciar el proceso completo. Esto demostró en la práctica uno de los principios fundamentales de la computación distribuida: la tolerancia a fallos y la recuperación automática ante caída de nodos.

El tiempo final de 159 segundos, a pesar de las desconexiones, sigue siendo menor que los 227 segundos del procesamiento secuencial, lo cual valida la robustez del sistema bajo condiciones adversas.
