# Resumen de benchmarks

Archivo analizado completo en todas las ejecuciones.

## Ejecuciones

```text
backend                                                                                      input_path  input_bases  processors  repeat  time_seconds  bases_per_second   invalids  invalids_per_second   count_A   count_C   count_G   count_T  avg_cpu_percent  peak_cpu_percent  peak_memory_mb  avg_gpu_util_percent  peak_gpu_util_percent  peak_gpu_memory_mb  samples
    CPU C:\RepositoriosTesis\computacion_paralela\colaborativo2\GCA_000001405.29_GRCh38.p14_genomic.fna   3298912062        16.0       1     40.192326      8.207816e+07 1353096152         3.366553e+07 558708442 413632783 414016300 559458385        93.749788        104.218873     1400.203125                   NaN                    NaN                 NaN      180
    GPU C:\RepositoriosTesis\computacion_paralela\colaborativo2\GCA_000001405.29_GRCh38.p14_genomic.fna   3298912062         NaN       1      1.278415      2.580471e+09 1353096152         1.058417e+09 558708442 413632783 414016300 559458385         6.178187          7.049080     7515.433594                 1.375                   93.0              6460.0      232
```

## Promedios por backend

```text
backend  repeticiones  tiempo_promedio_s  tiempo_min_s  tiempo_max_s  max_memoria_mb  cpu_promedio_pct  gpu_promedio_pct  errores_por_segundo  throughput_bases_s
    CPU             1          40.192326     40.192326     40.192326     1400.203125         93.749788               NaN         3.366553e+07        8.207816e+07
    GPU             1           1.278415      1.278415      1.278415     7515.433594          6.178187             1.375         1.058417e+09        2.580471e+09
```