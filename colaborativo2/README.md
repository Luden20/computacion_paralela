# computacion_paralela

## colaborativo2

`colaborativo2.py` tiene dos modos:

1. Ejecucion normal: corre CPU y GPU y muestra los conteos.
2. Benchmark: compara CPU vs GPU sobre el archivo completo y genera CSV, resumen y graficas.

### Uso normal

```bash
.venv/bin/python colaborativo2/colaborativo2.py \
  --file colaborativo2/GCF_000001405.40_GRCh38.p14_genomic.fna \
  --converter-path colaborativo2/c/build/c \
  --processors 8
```

### Uso benchmark

```bash
.venv/bin/python colaborativo2/colaborativo2.py \
  --file colaborativo2/GCF_000001405.40_GRCh38.p14_genomic.fna \
  --converter-path colaborativo2/c/build/c \
  --processors 8 \
  --benchmark \
  --benchmark-repeats 1 \
  --benchmark-output-dir colaborativo2/benchmark_artifacts
```

### Parametros del benchmark

- `--file`: archivo FASTA completo a analizar.
- `--converter-path`: ejecutable en C usado por la ruta GPU para transformar el FASTA.
- `--processors`: numero de procesos para CPU.
- `--benchmark`: activa el modo de comparacion y generacion de artefactos.
- `--benchmark-repeats`: cantidad de repeticiones por backend.
- `--benchmark-output-dir`: directorio donde se guardan resultados y graficas.

### Que genera

Dentro del directorio indicado en `--benchmark-output-dir` se generan:

- `benchmark_results.csv`
- `summary.md`
- `plots/comparacion_tiempos.png`
- `plots/uso_recursos.png`
- `plots/errores_por_segundo.png`
- `plots/rendimiento_global.png`

### Como se miden los tiempos

- CPU: solo se mide el tiempo de ejecucion del `ProcessPoolExecutor`.
- GPU: solo se mide el conteo sobre la matriz ya cargada en GPU.
- La llamada al convertidor en C no entra en el tiempo de GPU del benchmark.

### Notas

- El benchmark usa el archivo completo, no subsets.
- Si ejecutas sin `--benchmark`, no se generan graficas.
