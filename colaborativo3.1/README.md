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


Para el despliegue en Google Cloud Platform, usaremos el servicio de Cloud Run, que nos permite desplegar aplicaciones en contenedores de una forma sencilla y escalable.
## Set up
Creación del Grupo de Recursos

El primer paso consistió en crear un grupo de recursos llamado rg-adn-eastus.

![img](./img/azure/rg.png)

El grupo de recursos funciona como un contenedor lógico donde Azure organiza todos los recursos relacionados con el proyecto. Esto facilita la administración, monitoreo y eliminación conjunta de los recursos utilizados por la aplicación.


### Creación del App Service Plan

Luego se creó un App Service Plan llamado ADNPlan.

az appservice plan create \
  --name ADNPlan \
  --resource-group rg-adn-eastus \
  --location eastus \
  --is-linux \
  --sku F1

![img](./img/azure/plan_creado.png)

Este recurso representa la infraestructura de cómputo donde se ejecutará la aplicación. En nuestro caso se utilizó la capa gratuita F1 sobre Linux.

El App Service Plan define aspectos como:

Sistema operativo.
CPU disponible.
Memoria disponible.
Región de despliegue.
Nivel de servicio contratado.

Puede entenderse como el servidor administrado sobre el cual Azure ejecutará nuestra aplicación.




### Creación de la Web App

Una vez disponible la infraestructura, se creó la aplicación web llamada dna-api-oalozada.

az webapp create \
  --resource-group rg-adn-eastus \
  --plan ADNPlan \
  --name dna-api-oalozada \
  --deployment-container-image-name luren12/dna-analisis-api:v2


![img](./img/azure/app_service_creado.png)

La Web App es el recurso encargado de descargar y ejecutar la imagen Docker publicada previamente en Docker Hub.

La imagen utilizada fue:

luren12/dna-analisis-api:v2

Durante la creación, Azure generó automáticamente una URL pública para acceder al servicio.




Configuración del Contenedor

Posteriormente se configuró explícitamente la imagen Docker utilizada por la aplicación.

az webapp config container set \
  --resource-group rg-adn-eastus \
  --name dna-api-oalozada \
  --container-image-name luren12/dna-analisis-api:v2




Configuración del Puerto

Debido a que FastAPI escucha en el puerto 8000 dentro del contenedor, fue necesario indicar este puerto a Azure.

az webapp config appsettings set \
  --resource-group rg-adn-eastus \
  --name dna-api-oalozada \
  --settings WEBSITES_PORT=8000

Finalmente se reinició la aplicación para aplicar los cambios.

az webapp restart \
  --resource-group rg-adn-eastus \
  --name dna-api-oalozada




Arquitectura Resultante

Los recursos quedaron organizados de la siguiente forma:

Grupo de Recursos
└── rg-adn-eastus
    │
    ├── App Service Plan
    │     └── ADNPlan
    │          └── Linux Free (F1)
    │
    └── Web App
          └── dna-api-oalozada
                └── Imagen Docker:
                    luren12/dna-analisis-api:v2

La aplicación quedó disponible públicamente mediante:

https://dna-api-oalozada.azurewebsites.net

y la documentación Swagger mediante:

https://dna-api-oalozada.azurewebsites.net/docs

## Pruebas
Para validar el funcionamiento del despliegue se utilizó el mismo archivo FASTA empleado.

Hicimos la misma pruena con Postman que hicimos en AWS, con el mismo archivo de 20 mb. El resultado fue el siguiente:
![img](./img/azure/postman.png)
Como resultado del modelo de uso de CPU virtuales por segundo, no tenemos un limite estricto como en AWS por lo que la respuesta fue mucho mas rapida para el arhcivo de 20 mb.


La prueba consistió en enviar un archivo mediante una petición POST al endpoint /analizar utilizando Postman.

https://dna-api-oalozada.azurewebsites.net/analizar


Luego comprobamos el usao de recursos.

![img](./img/azure/metrics2.png)


# Despliegue en IBM Cloud

Para el despliegue en IBM Cloud usaremos el servicio de **Code Engine**, que permite desplegar aplicaciones en contenedores de forma serverless y escalable, similar a Google Cloud Run.

## Set up

### Acceso a Code Engine

Ingresar a https://cloud.ibm.com con cuenta y desde el catálogo buscar **Code Engine**, o navegar directamente desde el menú lateral en **Navigation Menu → Code Engine**.

### Crear el Proyecto

El primer paso es crear un proyecto que contendrá la aplicación. Hacer clic en **Projects → Create Project** y completar:

| Campo | Valor |
|---|---|
| Name | `dna-api-proyecto` |
| Location | Dallas (us-south) |

Una vez creado, seleccionarlo para entrar al panel del proyecto.

<img width="1192" height="578" alt="image" src="https://github.com/user-attachments/assets/f5daf2b4-7ffa-4fc3-8dc0-e9a1be77e87a" />

### Crear la Aplicación

Dentro del proyecto, navegar a **Applications → Create Application** y completar los campos:

**Sección General:**

| Campo | Valor |
|---|---|
| Name | `dna-api` |

<img width="907" height="549" alt="image" src="https://github.com/user-attachments/assets/8b9b889b-40eb-4af7-a69d-5d0c87928c3e" />


**Sección Code:**

Seleccionar **Container image** como fuente e ingresar:

| Campo | Valor |
|---|---|
| Image reference | `docker.io/luren12/dna-analisis-api:v2` |

Como la imagen es pública no se requieren credenciales adicionales.

<img width="425" height="493" alt="image" src="https://github.com/user-attachments/assets/4148f56e-968b-4891-a204-20b23e569b25" />

<img width="460" height="338" alt="image" src="https://github.com/user-attachments/assets/04f34b4e-232b-40d2-b73b-88dfc8e8e1cf" />



**Sección Resources & Scaling:**

| Campo | Valor |
|---|---|
| CPU | 1 vCPU |
| Memory | 4 GB |
| Min scale | `0` |
| Max scale | `3` |

<img width="675" height="439" alt="image" src="https://github.com/user-attachments/assets/c3785917-58d6-4d80-b2d0-b526a3cb42af" />


**Sección Ports:**

| Campo | Valor |
|---|---|
| Port | `8000` |
| Protocol | HTTP1 |

<img width="672" height="283" alt="image" src="https://github.com/user-attachments/assets/55f1ce49-e29e-466c-8fdb-f31b5e8e4627" />


Finalmente hacer clic en **Create** y esperar a que el despliegue quede en estado **Ready**.

<img width="1278" height="554" alt="image" src="https://github.com/user-attachments/assets/48c3ae91-c173-4453-b333-2273c71c4289" />


### Resultado

Una vez desplegado, la consola muestra la URL pública generada automáticamente en el panel de la aplicación:

**https://dna-api.2atpo9b2jtb1.us-south.codeengine.appdomain.cloud**


<img width="1276" height="541" alt="image" src="https://github.com/user-attachments/assets/d64856a1-1491-4623-bff1-5736e0e4e744" />


Los endpoints quedan disponibles en:

-*https://dna-api.2atpo9b2jtb1.us-south.codeengine.appdomain.cloud/analizar*

-*https://dna-api.2atpo9b2jtb1.us-south.codeengine.appdomain.cloud/docs*

## Pruebas

El proceso de pruebas es el mismo que en los despliegues anteriores — enviar el archivo de 20 MB al endpoint `/analizar` via Postman. Paso a paso:

---

**1. Abrir Postman y crear una nueva request**
- Método: `POST`
- URL: `https://dna-api.2atpo9b2jtb1.us-south.codeengine.appdomain.cloud/analizar`

---

<img width="876" height="628" alt="image" src="https://github.com/user-attachments/assets/ea28ba1c-4b31-40ef-bc0e-b28057094710" />


**2. Configurar el Body**
- Ir a la pestaña **Body**
- Seleccionar **form-data**
- Agregar los siguientes campos:

| Key | Type | Value |
|---|---|---|
| `file` | File | seleccionar `dna_20mb.txt` desde tu máquina |
| `patterns` | Text | `ATGCGT,TATA,GATTACA` |
| `chunk_mb` | Text | `32` |

<img width="849" height="195" alt="image" src="https://github.com/user-attachments/assets/cd4b8646-ae82-45cb-9427-156ac32a860d" />

---




**4. Verificar la respuesta**


```json
{
    "mode": "sequential",
    "file": "dna_20mb.txt",
    "file_size_bytes": 20971520,
    "chunk_size_bytes": 33554432,
    "chunks": 1,
    "patterns": ["ATGCGT", "TATA", "GATTACA"],
    "elapsed_seconds": 5.21,
    "base_counts": {
        "A": 1234567,
        "T": 1234567,
        "C": 1234567,
        "G": 1234567
    },
    "pattern_counts": {
        "ATGCGT": 123,
        "TATA": 456,
        "GATTACA": 78
    },
    "other_symbols": 0,
    "total_processed_symbols": 20971520
}
```
<img width="874" height="619" alt="image" src="https://github.com/user-attachments/assets/2591eccd-425e-4e72-bd87-714299f30de4" />

---

**5. Verificar la documentación interactiva (opcional)**



<img width="1290" height="551" alt="image" src="https://github.com/user-attachments/assets/479d05e9-8f2d-4c09-ad10-4cc4b458a9c1" />


Abrir en el navegador:

https://dna-api.2atpo9b2jtb1.us-south.codeengine.appdomain.cloud/docs

<img width="1323" height="506" alt="image" src="https://github.com/user-attachments/assets/23aa4d2b-952a-493c-aab5-c2a6138124e1" />


<img width="1254" height="515" alt="image" src="https://github.com/user-attachments/assets/484e9f17-eb7b-4df3-82e0-5fa4a8e0b037" />

<img width="1247" height="616" alt="image" src="https://github.com/user-attachments/assets/41e50d7d-b77d-4ee8-b76f-262eb91a31ce" />


El valor clave a observar es `elapsed_seconds`. Dado que IBM Code Engine usa el mismo modelo de CPU virtual por segundo que GCP, se espera un tiempo de respuesta cercano al de Google Cloud Run y muy por debajo de AWS Lightsail, con la diferencia de que el primer request puede ser algo más lento si la instancia escaló a 0 por inactividad.

## Conclusiones de IBM Cloud

Code Engine resultó el servicio más parecido a Google Cloud Run dentro de este grupo de despliegues:

- **Escalado:** Al igual que GCP, desescala a 0 instancias cuando no hay tráfico, por lo que no se incurre en costos en períodos de inactividad.
- **URL automática:** Asigna un dominio HTTPS automático sin configuración adicional de red, a diferencia de OCI que requiere configurar VCN y Security Lists manualmente.
- **Modelo de cobro:** Se factura por tiempo de CPU y memoria efectivamente usados durante la ejecución, no por capacidad reservada como en AWS Lightsail o Azure F1.
- **Cold start:** Al desescalar a 0, el primer request tras un período de inactividad puede tardar unos segundos adicionales antes de responder, algo que no ocurre en DigitalOcean o AWS donde el contenedor corre continuamente.
- **Capa gratuita:** IBM Cloud ofrece una cuota mensual gratuita de 50 GB-s de memoria y 10 vCPU-s en Code Engine, suficiente para pruebas como las realizadas con el archivo de 20 MB.

# Comparativa General de Proveedores

## Planes y Costos

| Proveedor | Servicio usado | Tier gratuito | Costo mínimo de producción | Modelo de cobro |
|---|---|---|---|---|
| **AWS** | Lightsail Containers | 3 meses gratis (plan Micro $10/mes) | **$10/mes** (Micro: 0.25 vCPU, 0.5 GB RAM) | Tarifa plana mensual por nodo reservado |
| **Google Cloud** | Cloud Run | Permanente: 180k vCPU-s, 360k GB-s, 2M requests/mes | ~**$0–$14/mes** según tráfico | Por vCPU-segundo ($0.000024/vCPU-s) + por GB-segundo + por millón de requests |
| **Azure** | App Service (Web App for Containers) | F1 gratis (infraestructura compartida, sin SLA, límite de CPU diario) | **$13–$14/mes** (plan B1: 1 vCPU, 1.75 GB RAM dedicados) | Tarifa plana mensual por plan; F1 no es apto para producción |
| **IBM Cloud** | Code Engine | Mensual: 100k vCPU-s + 200k GB-s | ~**$0–$5/mes** para cargas ligeras | Por vCPU-segundo + por GB-segundo; escala a 0 |

---

## Modelo de Uso del Servicio

| Proveedor | Interfaz principal | Escalado | Cold start | Dificultad de setup |
|---|---|---|---|---|
| **AWS Lightsail** | Consola web gráfica, muy guiada | Manual (nodos fijos) | No (contenedor siempre activo) | Muy fácil |
| **Google Cloud Run** | Consola web + `gcloud` CLI | Automático (0 a N instancias) | Sí (si escala a 0) | Fácil |
| **Azure App Service** | Consola web + `az` CLI | Manual en F1/B1; automático desde P1 | No en tiers básicos (contenedor activo) | Moderado (requiere Resource Group + App Service Plan + Web App) |
| **IBM Code Engine** | Consola web + `ibmcloud` CLI | Automático (0 a N instancias) | Sí (si escala a 0) | Fácil |

---

## Modelo de Pago

| Proveedor | Forma de pago | Requiere tarjeta para free tier | Crédito inicial | Facturación |
|---|---|---|---|---|
| **AWS** | Tarjeta de crédito / débito, PayPal (según región) | Sí | $300 por 30 días | Mensual, con desglose detallado en AWS Cost Explorer |
| **Google Cloud** | Tarjeta, transferencia bancaria (en algunos países) | Sí | $300 por 90 días | Mensual; alertas de presupuesto configurables |
| **Azure** | Tarjeta de crédito / débito | Sí (para tiers pagos; F1 no la requiere) | $200 por 30 días | Mensual; el portal muestra estimados en tiempo real |
| **IBM Cloud** | Tarjeta de crédito / débito | Sí (para PAYG; Lite plan no la requiere) | $200 por 30 días | Mensual; se pueden configurar umbrales de gasto al 80%, 90% y 100% |


**TOMEN EN CUENTA QUE SOLO ACEPTA VISA/MASTERCARD/DINERS Y PAYPAL, NADA DE OTROS PROVEEDORES O DEUNA.**

---

## Desempeño Comparado (archivo de 20 MB)

| Proveedor | Tiempo de respuesta (20 MB) | Resultado con 1 GB | Observaciones |
|---|---|---|---|
| **AWS Lightsail** | ~54 segundos | Falla por falta de memoria | CPU y RAM fijos y limitados en el tier básico |
| **Google Cloud Run** | ~3 segundos | No falla; retorna error controlado tras 69 s | Escalado dinámico de CPU; el mejor rendimiento en pruebas |
| **Azure App Service** | Similar a GCP (F1 compartida) | No probado | F1 tiene throttling agresivo de CPU en infraestructura compartida |
| **IBM Code Engine** | ~5.21 segundos | No probado | Modelo similar a GCP; cold start posible tras inactividad |

---

## ¿Cuál es el mejor para un despliegue real?

### Para una API de análisis de ADN en producción real: Google Cloud Run

**Razón técnica:** Es el único servicio que demostró manejar cargas variables sin fallar ni consumir recursos en exceso. Al escalar dinámicamente y cobrar solo por CPU y memoria efectivamente consumidas, es ideal para una API que recibe peticiones esporádicas de archivos pesados.

**Razón económica:** La capa gratuita cubre 2 millones de requests, 360,000 GB-segundos de memoria y 180,000 vCPU-segundos de cómputo al mes sin expiración, suficiente para un uso académico o prototipo de baja frecuencia completamente gratis. Para tráfico moderado, el costo estimado es de $0 a ~$14/mes, muy por debajo del costo fijo de AWS Lightsail ($10/mes garantizados aunque no se use).

**Razón operativa:** El setup es sencillo (interfaz gráfica + CLI), genera URL HTTPS automática, y el escalado a 0 cuando no hay tráfico evita cargos innecesarios. No requiere configuración de red manual.

---

### No recomendados para producción en este caso de uso

- **AWS Lightsail:** El plan Micro de contenedores cuesta $10/mes con solo 0.25 vCPU y 0.5 GB de RAM, precio fijo comparable al de otros servicios pero con peor desempeño; la API tardó 54 segundos vs 3 segundos en GCP para el mismo archivo.
- **Azure App Service F1:** El tier gratuito corre en infraestructura compartida con throttling agresivo; tras agotar la cuota de CPU los requests retornan 503, sin SLA ni SSL en dominio personalizado. Para producción real se necesita al menos el plan B1 (~$13–$14/mes), que no añade ventajas frente a GCP.
- **IBM Code Engine:** Técnicamente equivalente a GCP Cloud Run, pero con una capa gratuita más pequeña (100k vCPU-s vs 180k de GCP) y un ecosistema más limitado. Es una opción válida si ya se trabaja en entornos enterprise IBM.
