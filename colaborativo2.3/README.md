

## Activar entorno virtual

source ~/ray-dna/bin/activate

Con esto levantamos el cluster
En ha1
```bash
source ~/ray-dna/bin/activate
ray stop
ray start --head \--node-ip-address=192.168.253.128 \--port=6379 \--dashboard-host=0.0.0.0 \--dashboard-port=8265 \--object-manager-port=8076 \--node-manager-port=8077 \--runtime-env-agent-port=8078 \--metrics-export-port=8080 \--ray-client-server-port=10001 \--dashboard-agent-listen-port=52365 \--dashboard-agent-grpc-port=52366 \--min-worker-port=10002 \--max-worker-port=10100
```

En ha2
```bash
source ~/ray-dna/bin/activate && ray stop --force && ray start --address='192.168.253.128:6379' --node-ip-address=192.168.253.129 --object-manager-port=8076 --node-manager-port=8077 --runtime-env-agent-port=8078 --metrics-export-port=8080 --dashboard-agent-listen-port=52365 --dashboard-agent-grpc-port=52366 --min-worker-port=10002 --max-worker-port=10100
``` 
En ha3
```bash
source ~/ray-dna/bin/activate && ray stop --force && ray start --address='192.168.253.128:6379' --node-ip-address=192.168.253.130 --object-manager-port=8076 --node-manager-port=8077 --runtime-env-agent-port=8078 --metrics-export-port=8080 --dashboard-agent-listen-port=52365 --dashboard-agent-grpc-port=52366 --min-worker-port=10002 --max-worker-port=10100
```

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

Vamos a generar 3 archivos, uno de 200mb, otro de 1gb y uno mas grande de 10 gb para poder comparar los resultados.

| Archivo de entrada | Patrones | Chunk MB | Núcleos | Tiempo secuencial (s) | Tiempo distribuido (s) | Speedup | Eficiencia |
|---|---|---:|---:|---:|---:|---:|---:|
| data/dna_200mb.txt | ATGCGT, TATA, GATTACA | 32 | 6 | 3.2311 | 4.3855 | 0.7368 | 0.1228 |
| data/dna_1gb.txt | ATGCGT, TATA, GATTACA | 32 | 6 | 19.1811 | 13.1015 | 1.4640 | 0.3660 |
| data/dna_10gb.txt | ATGCGT, TATA, GATTACA | 32 | 6 | 227.3990 | 159.2666 | 1.4278 | 0.2380 |
|

Como mencion, durante la ejecucion de l archivo de 10GB se testeo (sin querer realmente) lo que se hace en un proceso de desconexion de un cluster durante una tarea. Los cluster tienen 2 CPU cada uno y 4GB de RAM, los cuales al parecer eran demasiado justos porque tanto ha2 y ha3 se saturaron y los procesos de hearbeat no funcionaron correctamente lo que provoco que se desconectaran, rapidamente se los volvio a conectar y estos de inmediato asumieron mas carga.

Con esto en cuenta , el tiempo distribuido sigue siendo mejor que el secuencial y con pruebas mas intensivas se podria mejorar aun mas . El secuencial es mejor solo con el archivo de 200mb, esto se debe a que en esa escala de datos el overhead de la comunicacion entre procesos es mayor que el beneficio que se obtiene al paralelizar la tarea. Al aumentar la fraccion paralela, los resultados mejoran en tiempo.