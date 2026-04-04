# Resumen de benchmarks

Archivo analizado completo en todas las ejecuciones.

## Ejecuciones

```text
backend                                                                                       input_path  input_bases  processors  repeat  time_seconds  bases_per_second   invalids  invalids_per_second   count_A   count_C   count_G   count_T  avg_cpu_percent  peak_cpu_percent  peak_memory_mb  avg_gpu_util_percent  peak_gpu_util_percent  peak_gpu_memory_mb  samples
    CPU C:\DevStuff\University\computaion_paralela\colaborativo2\GCF_000001405.40_GRCh38.p14_genomic.fna   3298430636        16.0       1     86.216350      3.825760e+07 1352989787         1.569296e+07 558619211 413530454 413917617 559373567        72.531730         94.206982     1356.484375                   NaN                    NaN                 NaN      360
    GPU C:\DevStuff\University\computaion_paralela\colaborativo2\GCF_000001405.40_GRCh38.p14_genomic.fna   3298430636         NaN       1      1.036628      3.181884e+09 1352989787         1.305183e+09 558619211 413530454 413917617 559373567         6.613419          8.277112     7532.253906             28.257732                  100.0              7685.0      291
```

## Promedios por backend

```text
backend  repeticiones  tiempo_promedio_s  tiempo_min_s  tiempo_max_s  max_memoria_mb  cpu_promedio_pct  gpu_promedio_pct  errores_por_segundo  throughput_bases_s
    CPU             1          86.216350     86.216350     86.216350     1356.484375         72.531730               NaN         1.569296e+07        3.825760e+07
    GPU             1           1.036628      1.036628      1.036628     7532.253906          6.613419         28.257732         1.305183e+09        3.181884e+09
```