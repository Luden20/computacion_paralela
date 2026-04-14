# Parcial 1 Final

Comparador de ADN para archivos `.fna` / `.fasta` con dos rutas de ejecución:

- `cpu/`: comparación exacta usando paralelismo en CPU.
- `gpu/`: comparación exacta por lotes usando CuPy en GPU, con reporte de progreso por etapas.

Los archivos grandes `GCA_*.fna` y `GCF_*.fna` se mantienen en la raíz del proyecto y no forman parte de la lógica del código.

## Estructura

```text
parcial1/
├── cpu/
│   ├── compare_dna_cpu.py
│   ├── compare_dna_cpu.cpp
│   ├── compare_dna_cpu_linux
│   └── compare_dna_cpu_windows.exe
├── gpu/
│   ├── compare_dna_gpu.py
│   ├── requirements.txt
│   └── converter/
│       ├── fasta_to_binary_converter.cpp
│       ├── fasta_to_binary_converter_windows.exe
│       ├── build_windows_converter.txt
│       └── CMakeLists.txt
├── GCA_000001405.29_GRCh38.p14_genomic.fna
├── GCF_000001405.40_GRCh38.p14_genomic.fna
├── differences.json
└── execution_time.json
```

## Cómo funciona

### Ruta CPU

`cpu/compare_dna_cpu.py` divide la comparación en bloques, reparte el trabajo entre varios procesos y escribe diferencias temporales en disco para no saturar RAM. Al final consolida todo en un solo `differences.json`.

`cpu/compare_dna_cpu.cpp` hace la misma idea desde C++, también en paralelo y escribiendo el resultado final en JSON.

### Ruta GPU

`gpu/compare_dna_gpu.py` lee ambas secuencias en streaming, agrupa líneas comparables en lotes y usa CuPy para comparar muchas columnas al mismo tiempo en GPU. Las diferencias se escriben directo a disco y el script muestra:

- etapa actual del proceso;
- porcentaje de progreso;
- líneas comparables acumuladas;
- diferencias acumuladas.

La carpeta `gpu/converter/` quedó organizada como convertidor legado. La implementación GPU actual ya no depende de ese convertidor para la comparación exacta, pero se conserva como utilidad auxiliar y referencia.

## Salidas

Tanto CPU como GPU generan en la raíz del proyecto:

- `differences.json`: arreglo JSON con el formato `[posicion_global_del_byte, columna_en_la_linea, caracter_archivo_1, caracter_archivo_2]`.
- `execution_time.json`: resumen con archivo 1, archivo 2, tiempo total y cantidad total de diferencias.

> Aviso: `differences.json` puede crecer muchísimo si los genomas difieren bastante.

## Uso

Abre terminal en la raíz de `parcial1`.

### CPU en Python

```bash
python cpu/compare_dna_cpu.py \
  --file1 GCA_000001405.29_GRCh38.p14_genomic.fna \
  --file2 GCF_000001405.40_GRCh38.p14_genomic.fna \
  --workers 8
```

### CPU en C++

Linux:

```bash
./cpu/compare_dna_cpu_linux \
  --file1 GCA_000001405.29_GRCh38.p14_genomic.fna \
  --file2 GCF_000001405.40_GRCh38.p14_genomic.fna \
  --workers 8
```

Windows:

```powershell
.\cpu\compare_dna_cpu_windows.exe `
  --file1 GCA_000001405.29_GRCh38.p14_genomic.fna `
  --file2 GCF_000001405.40_GRCh38.p14_genomic.fna `
  --workers 8
```

Si necesitas recompilar el comparador C++:

```bash
g++ cpu/compare_dna_cpu.cpp -O2 -std=c++20 -o cpu/compare_dna_cpu_linux
```

### GPU con CuPy

Primero instala las dependencias del entorno GPU:

```bash
pip install -r gpu/requirements.txt
```

Luego ejecuta:

```bash
python gpu/compare_dna_gpu.py \
  --file1 GCA_000001405.29_GRCh38.p14_genomic.fna \
  --file2 GCF_000001405.40_GRCh38.p14_genomic.fna
```

`--converter-path` sigue existiendo solo por compatibilidad, pero ya no es obligatorio.

## Notas

- Ejecuta los comandos desde la raíz de `parcial1` para que la salida quede centralizada.
- Los `.fna` no se modifican.
- Si CuPy o CUDA no están disponibles, la ruta GPU va a fallar al inicio con un mensaje explícito.
