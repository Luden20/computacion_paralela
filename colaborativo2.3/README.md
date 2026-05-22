

## Activar entorno virtual

source ~/ray-dna/bin/activate
Antes de cualquier cosa, se activó un entorno virtual de Python llamado ray-dna. Esto es una buena práctica porque aísla las dependencias del proyecto del resto del sistema operativo, evitando conflictos entre versiones de librerías.

El clúster se compuso de tres nodos físicos/virtuales: ha1 (nodo maestro), ha2 y ha3 (nodos esclavos). Se utilizó Ray, un framework de Python para computación distribuida.

Con esto levantamos el cluster
En ha1 (nodo maestro)
```bash
source ~/ray-dna/bin/activate
ray stop
ray start --head \--node-ip-address=192.168.253.128 \--port=6379 \--dashboard-host=0.0.0.0 \--dashboard-port=8265 \--object-manager-port=8076 \--node-manager-port=8077 \--runtime-env-agent-port=8078 \--metrics-export-port=8080 \--ray-client-server-port=10001 \--dashboard-agent-listen-port=52365 \--dashboard-agent-grpc-port=52366 \--min-worker-port=10002 \--max-worker-port=10100
```
Este comando inicia Ray como nodo cabeza del clúster. El parámetro --head indica que este nodo será el coordinador central. El puerto 6379 es el punto de entrada al que los demás nodos se conectarán. El dashboard en el puerto 8265 permite monitorear visualmente el estado del clúster en tiempo real. Los demás puertos (8076, 8077, 8078, etc.) son canales internos que Ray usa para gestión de objetos, workers, métricas y agentes.

En ha2 (primer nodo esclavo)
```bash
source ~/ray-dna/bin/activate && ray stop --force && ray start --address='192.168.253.128:6379' --node-ip-address=192.168.253.129 --object-manager-port=8076 --node-manager-port=8077 --runtime-env-agent-port=8078 --metrics-export-port=8080 --dashboard-agent-listen-port=52365 --dashboard-agent-grpc-port=52366 --min-worker-port=10002 --max-worker-port=10100
``` 
En ha3 (Segundo nodo esclavo)
```bash
source ~/ray-dna/bin/activate && ray stop --force && ray start --address='192.168.253.128:6379' --node-ip-address=192.168.253.130 --object-manager-port=8076 --node-manager-port=8077 --runtime-env-agent-port=8078 --metrics-export-port=8080 --dashboard-agent-listen-port=52365 --dashboard-agent-grpc-port=52366 --min-worker-port=10002 --max-worker-port=10100
```
Los nodos ha2 (192.168.253.129) y ha3 (192.168.253.130) se unen al clúster apuntando a la dirección del nodo maestro. A partir de este momento, Ray puede distribuir tareas entre los tres nodos de forma automática. El comando ray stop --force previo asegura que no haya instancias anteriores de Ray corriendo que puedan causar conflictos.

Vamos a tomar como base los script del laboratorio en clase, pero con modificaciones. Para poder sincronizar los scripts usaremos la cli de Github.

```bash
sudo dnf install git -y

sudo dnf install 'dnf-command(config-manager)'

sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo

sudo dnf install gh
```
Con este repo clonado ejecutamos de esta forma 
```bash
python src/main.py --input data/dna_200mb.txt --patterns ATGCGT,TATA,GATTACA --chunk-mb 32 --output results/distribuido_200mb.json
```

El script principal recibe cuatro parámetros clave:

--input: el archivo de ADN a procesar (en formato de texto con bases A, T, C, G).
--patterns: las secuencias genéticas que se buscan dentro del ADN (ATGCGT, TATA, GATTACA).
--chunk-mb 32: el archivo se divide en fragmentos de 32 MB cada uno, que son distribuidos entre los nodos del clúster para procesarse en paralelo.
--output: el archivo JSON donde se consolidan los resultados de todos los nodos.

Internamente, el script implementa el patrón divide y vencerás propio de la computación distribuida: fragmentar el archivo → distribuir fragmentos → procesar en paralelo → consolidar resultados.

Vamos a generar 3 archivos, uno de 200mb, otro de 1gb y uno mas grande de 10 gb para poder comparar los resultados.

| Archivo de entrada | Patrones | Chunk MB | Núcleos | Tiempo secuencial (s) | Tiempo distribuido (s) | Speedup | Eficiencia |
|---|---|---:|---:|---:|---:|---:|---:|
| data/dna_200mb.txt | ATGCGT, TATA, GATTACA | 32 | 6 | 3.2311 | 4.3855 | 0.7368 | 0.1228 |
| data/dna_1gb.txt | ATGCGT, TATA, GATTACA | 32 | 6 | 19.1811 | 13.1015 | 1.4640 | 0.3660 |
| data/dna_10gb.txt | ATGCGT, TATA, GATTACA | 32 | 6 | 227.3990 | 159.2666 | 1.4278 | 0.2380 |
|

Como mencion, durante la ejecucion de l archivo de 10GB se testeo (sin querer realmente) lo que se hace en un proceso de desconexion de un cluster durante una tarea. Los cluster tienen 2 CPU cada uno y 4GB de RAM, los cuales al parecer eran demasiado justos porque tanto ha2 y ha3 se saturaron y los procesos de hearbeat no funcionaron correctamente lo que provoco que se desconectaran, rapidamente se los volvio a conectar y estos de inmediato asumieron mas carga.

Con 200 MB, el procesamiento distribuido fue más lento que el secuencial. Esto se explica por la Ley de Amdahl: cuando el volumen de datos es pequeño, el overhead de comunicación entre nodos (serialización de datos, transferencia en red, coordinación de Ray) supera el beneficio de paralelizar. No vale la pena distribuir una tarea que tarda apenas 3 segundos.

Con 1 GB y 10 GB, el procesamiento distribuido supera claramente al secuencial, logrando un speedup de ~1.43–1.46x. A mayor volumen de datos, la fracción paralela del trabajo domina sobre el overhead fijo de comunicación, y la distribución comienza a rendir sus beneficios.
La eficiencia (speedup / número de núcleos) es relativamente baja (~0.24–0.37) porque los nodos tenían solo 2 CPU y 4 GB de RAM cada uno, lo cual resultó ser un recurso bastante ajustado para este tipo de carga.

Con esto en cuenta , el tiempo distribuido sigue siendo mejor que el secuencial y con pruebas mas intensivas se podria mejorar aun mas . El secuencial es mejor solo con el archivo de 200mb, esto se debe a que en esa escala de datos el overhead de la comunicacion entre procesos es mayor que el beneficio que se obtiene al paralelizar la tarea. Al aumentar la fraccion paralela, los resultados mejoran en tiempo.

Durante la ejecución del archivo de 10 GB, ha2 y ha3 se desconectaron por saturación de recursos. Los procesos de heartbeat de Ray (señales periódicas que cada nodo envía al maestro para indicar que sigue activo) fallaron porque la CPU y RAM estaban al límite.
Lo destacable es que al reconectarlos, Ray los reintegró automáticamente al clúster y les asignó nuevas cargas de trabajo de inmediato, sin necesidad de reiniciar el proceso completo. Esto demostró en la práctica uno de los principios fundamentales de la computación distribuida: la tolerancia a fallos y la recuperación automática ante caída de nodos.
El tiempo final de 159 segundos, a pesar de las desconexiones, sigue siendo menor que los 227 segundos del procesamiento secuencial, lo cual valida la robustez del sistema bajo condiciones adversas.
