# Colaborativo 3.1 — API de Análisis de ADN

En este colaborativo buscamos desplegar el programa de analisis de ADN como un servicio dockerizado. Para esto reusaremos el codigo del colaborativo anterior pero del metodo secuencial, porque no es posible paralelizarlo usando contenedores, para una implementacion de ese estilo necesitariamos servicios en la nube mas complejos.

Para poder usar el programa por medio de la red tuvimos que construir por encima del programa reutilizado una API REST usando FastAPI, que expone un unico endpoint. Este funcion de la siguiente forma:
## Endpoint

`POST /analizar`

| Campo | Tipo | Default | Descripción |
|---|---|---|---|
| `file` | archivo | — | Secuencia de ADN (`.fasta`, `.fna`, etc.) |
| `patterns` | string | `ATGCGT,TATA,GATTACA` | Patrones a buscar, separados por coma |
| `chunk_mb` | int | `32` | Tamaño de chunk en MB para el procesamiento |
## Correr con Docker

Para poder correr todo esto de forma facil y transportable entre entornos hemos desarrollado una Dockerfile.

```Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py secuential_process.py ./

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

```
Esta expone el puerto 8000 y abstrae toda la complejidad del despliegue, en el proceso tambien instalando las librerias necesarias. 
Las imagenes se buildean y corren de la siguiente forma:

**Build:**
```bash
docker build -t luren12/dna-analisis-api:v2 .
```

**Run:**
```bash
docker run -p 8000:8000 luren12/dna-analisis-api:v2
```

**Llamar la API:**
```bash
curl -X POST http://localhost:8000/analizar \
  -F "file=@secuencia.fasta" \
  -F "patterns=ATGCGT,TATA,GATTACA" \
  -F "chunk_mb=32"
```

La documentación interactiva queda disponible en `http://localhost:8000/docs`.

## Publicar en Docker Hub
Para que esto sea transportable tenemos que publicar la imagen en el hub publico de docker. De la siguiente forma:
**Login:**
```bash
docker login
```

**Tag (si se buildeó sin el prefijo del usuario):**
```bash
docker tag dna-analisis-api:v2 luren12/dna-analisis-api:v2
```

**Push:**
```bash
docker push luren12/dna-analisis-api:v2
```

**Pull desde cualquier máquina:**
```bash
docker pull luren12/dna-analisis-api:v2
```
 Una vez la imagen esté en Docker Hub, cualquier persona puede usarla sin necesidad de construirla localmente, facilitando la distribución y uso del servicio de análisis de ADN.
 ![img](./img/docker/hub.png)
 Con todo esto podemos desplegarlo facilmente en cualquier nube.

# Despliegue en AWS
Para el despliegue en AWS, usaremos el servicio de contenedores de Lightsail. Este servicio nos facilita el despliegue de aplicaciones en contenedores de una forma mas sencilla que otros servicios del propio AWS.

## Set up

Primero vamos a seleccionar el servicio de contenedores en Lightsail.
![img](./img/aws/select-ser.png)
Luego vamos a seleccionar la capacidad del contenedor. Para este caso seleccionaremos la mas basica con un solo nodo.
![img](./img/aws/set-cap.png)
Luego en el aparatado de imagen simplemente usaremos la imagen que publicamos en Docker Hub. Ademas de configurar el puerto 8000 para que quede expuesto.
![img](./img/aws/set-img.png)
Luego registramos el endpoint por el cual se va a acceder a la API, en este caso usaremos `/analizar`.
![img](./img/aws/set-publicurl.png)
Luego de configurar quedo de la siguiete forma:
![img](./img/aws/conf1.png)
![img](./img/aws/conf2.png)
## Prueba
Como los recursos a los que tenemos acceso son limitados es obvio que el programa no va a poder procesar grandes cantidades de archivos. Si tuvieramos un presupuesto mas alto podriamos asignar un contenedor con mas poder de procesamiento y memoria, lo que nos permitira poder procesar archivos pesados. Con esto en cuenta, reutilizando el generador de archivos del colaborativo anterior, generamos un archivo de 20 mb.
![img](./img/aws/api.png)
Este simple test tuvo la siguiente utilizacion de recursos:
### CPU
![img](./img/aws/cpu.png)
### Memoria
![img](./img/aws/memory.png)
Podemos ver que pese a ser un archivo relativamente pequeño, el programa consume toda la memoria disponible, pero si tuvieramos un presupuesto mas grande podriamos asignar un contenedor con mas memoria y asi poder procesar archivos mas grandes.

## Conclusiones de AWS
El despliegue en AWS fue bastante sencillo porque usamos la alternativa de Lightsail que es mucho mas sencilla que otros servicios de AWS que nos dan mas control pero tambien requieren mas configuracion. 

# Despliegue en Google Cloud Platform
Para el despliegue en Google Cloud Platform, usaremos el servicio de Cloud Run, que nos permite desplegar aplicaciones en contenedores de una forma sencilla y escalable.
## Set up
![img](./img/google/home.png)
Para esto configuraremos de la siguiente forma:
![img](./img/google/conf1.png)
![img](./img/google/conf2.png)
Nota: No nos fijamos al momento de configurar el servicio de configurar el puerto por que se escucha, por lo que luego de desplegar el servicio tuvimos que configurar el puerto 8000 para que quede expuesto.
![img](./img/google/fix.png)
Algo a resaltar es que Cloud Run no nos alquila poder de computo fijo como AWS que corre con un EC2 por debajo, sino que nos cobra por uso de CPU virtual por segundo, lo que signifca que no establecemos limites fisicos, solo se nos cobra lo que se use. 

Como resultado de esto tenemos una aplicacion contenerizada corriendo en Google Cloud Run, con un endpoint publico al cual se puede acceder desde cualquier parte del mundo. Algo a destacar es que en el proceso de configuracion podiamos seleccionar la cantidad minima  y maxima de nodos, algo que en lightsail no podiamos hacer. Esto permite que el servicio de contendores pueda desescalar a 0 cuando no se usa.El maximo configurado fue de 3.

Con esto el resultado de creacion fue el siguiente ![img](./img/google/creating.png)
## Pruebas
Hicimos la misma pruena con Postman que hicimos en AWS, con el mismo archivo de 20 mb. El resultado fue el siguiente:
![img](./img/google/postman.png)
Como resultado del modelo de uso de CPU virtuales por segundo, no tenemos un limite estricto como en AWS por lo que la respuesta fue mucho mas rapida para el arhcivo de 20 mb, tardando alrededor de 3 segundos mientras en AWS tardo alrededor de 54 segundos. Una gran diferencia.

Con la curiosidad de ver que pasaria con el archivo de 1GB se lo enviamos.
![img](./img/google/postman1gb.png)
El resultado fue inesperado, no fallo por falta de memoria como en AWS donde el contendor se saturo y no pudo ni responder. En Google Cloud Run el servicio luego de 1 minuto y 9 segundos respondio con que el archivo es demasiado largo para procesar. Es decir igual no lo proceso, pero no murio por falta de memoria, lo que es un gran punto a favor de este servicio.
Con estas pruebas obtuvimos las siguientes metricas:
![img](./img/google/metrics.png)
![img](./img/google/metrics2.png)
![img](./img/google/metrics3.png)
# Despliegue en Azure
# Despliegue en Oracle Cloud
