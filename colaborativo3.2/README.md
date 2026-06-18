# Colaborativo 3.2 — API de Análisis de ADN

Para este colaborativo replicaremos la dinamica del colaborativo 3.1 pero usaremos proveedores cloud asiaticos y europeos.
El dockerfile que desplegaremos sera el mismo que el colaborativo anterior, y la prueba sera la misma.

# Despliegue Scaleaway (Europa)
En este proveedor vamos a usar el servicio de Serverless Containers, el cual nos permite desplegar contenedores docker sin necesidad de gestionar la infraestructura subyacente. Para esto, primero debemos crear una cuenta en Scaleaway y luego seguir los pasos para configurar nuestro entorno.
## Set up
Luego de crear nuestra cuenta con un metodo de pago valido entraremos al menu de Serverless Container y crearemos uno.
![](./img/scaleaway/home.png)
Primero debemos crear un namespace, que es un concepto parecido al de los grupos de recursos de otros proveedores.
![](./img/scaleaway/creacion-ns.png)
Luego procederemos con la creacion del contenedor, donde usaremos la url de la imagen de docker que usamos en el anterior colaborativo y configuraremos el puerto 8000 como puerto de exposicion.
![](./img/scaleaway/container.png)
Scaleaway es bastante flexxible con la capacidad que podemos darle a cada contenedor y ademas nos permite combinarlo con escalado en base a request. En este caso configuraremos 500mVCPU y 1024 MB  de RAM. Ademas configuramos que pueda desescalar a 0 cuando no haya trafico , y que llegue hasta 5 replicas cuando se requiera.
![](./img/scaleaway/recursos-conf.png)
 Con esto nuestro contenedor ya quedo configurado y listo para usar. 
 ## Pruebas
 Podemos ver como accediendo a la url publica podemos acceder a la documentacion swagger.
 ![](./img/scaleaway/despliegue.png)
  Intentamos usar el archivo de 1 GB pero no dio resultados por mas de 1 minuto entonces se aborto la trasaccion. El resultado para el archivo de 20 mb fue el siguiente:
![](./img/scaleaway/postman.png)
En total tardo 4.19 segundos, lo cual es bastante rapido.

Se intento revisar las metricas de uso , pero Scaleaway usa una integracion con Grafana que no funciono correctmaente, por lo que no se pudieron revisar las metricas de uso del contenedor.
![](./img/scaleaway/metrics.png)
## Conclusiones Scaleaway
Scaleaway es un proveedor bastante facil de usar con un ainterfaz bastante agradable y costos bastante accesibles. Lo negativo del servicio es que este tiene solo centros de datos en europa y su integracion con Grafana no funciono correctamente, lo que impidio revisar las metricas de uso del contenedor. Todo el proceso de levantar el contenedor fue bastante facil y rapido, y el resultado de la prueba fue bastante bueno, con un tiempo de respuesta de 4.19 segundos para el archivo de 20 mb.
