

## Activar entorno virtual

source ~/ray-dna/bin/activate


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
python src/dna_ray.py --input data/dna_200mb.txt --patterns ATGCGT,TATA,GATTACA --chunk-mb 32 --output results/distribuido_200mb.json
```