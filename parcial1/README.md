# Comparador de ADN Paralelo

Este script realiza una comparación carácter por carácter entre dos secuencias de ADN (archivos `.fna` / `.fasta`) dividiendo el trabajo en múltiples procesos (Parallel Processing) para disminuir el tiempo de ejecución de estos análisis masivos.

Para evitar desbordamientos de memoria RAM (debido al gran tamaño de los genomas y la posibilidad de millones de diferencias por usar bases de datos distintas), el script trabaja transmitiendo las diferencias directamente al disco duro en tiempo real.

## Requisitos

- **Python 3.x**
- No requiere dependencias externas, ya que hace uso de librerías nativas (`concurrent.futures`, `json`, `argparse`, `os`).

## Uso Básico

Abre tu terminal (o PowerShell / CMD) en la carpeta del proyecto y ejecuta el siguiente comando:

```powershell
python main.py --file1 "ruta/archivo1.fna" --file2 "ruta/archivo2.fna" --workers 8
```

### Argumentos:
- `--file1`: Ruta del primer archivo del genoma que quieres comparar. **(Requerido)**
- `--file2`: Ruta del segundo archivo del genoma para realizar la comparación. **(Requerido)**
- `--workers`: Cantidad de procesos de CPU que se asignarán. Si no estás seguro de cuántos núcleos tiene tu PC, puedes omitir este parámetro y usará un valor por defecto.

**Ejemplo completo:**
```powershell
python main.py --file1 "GCA_000001405.29_GRCh38.p14_genomic.fna" --file2 "GCF_000001405.40_GRCh38.p14_genomic.fna" --workers 8
```

## Salidas (Resultados)

Al terminar el proceso, se generarán automáticamente dos archivos en la carpeta del script:

1. **`execution_time.json`**: Guarda un resumen corto con los nombres de los dos archivos evaluados, el tiempo total que demoró la ejecución en paralelismo, y la cantidad total de diferencias encontradas.
2. **`differences.json`**: Contiene la matriz (en formato JSON) con todas las características divergentes entre las cadenas biológicas. Por cada diferencia encontrada verás el siguiente formato:
   `[posición_global_del_byte, columna_en_la_línea, carácter_f1, carácter_f2]`

> **Aviso Importante:** Dependiendo de cuán ajenas sean las dos genéticas analizadas, el archivo `differences.json` puede engordar de tamaño significativamente, consumiendo varios Gigabytes de tu disco duro. 
