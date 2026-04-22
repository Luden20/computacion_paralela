import argparse
import os
import time
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from enum import Enum
from dataclasses import dataclass


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DIFFERENCES_JSON_PATH = PROJECT_ROOT / "differences.json"
EXECUTION_TIME_JSON_PATH = PROJECT_ROOT / "execution_time.json"

# Estructuras de datos para los resultados
class ExecutionType(Enum):
    CPU = "CPU"
    GPU = "GPU"

@dataclass
class DnaComparison:
    total_differences: int
    time_taken: float
    execution_type: ExecutionType

def process_chunk(file1, file2, limits):
    """
    Procesa un bloque y escribe las diferencias directamente en disco para no 
    agotar la memoria RAM con archivos de varios Gigabytes.
    """
    start, end = limits
    if start == 0:
        print("[INFO] Primer worker: Iniciando lectura de la secuencia...")
        
    diff_count = 0
    temp_file = PROJECT_ROOT / f"temp_chunk_{start}.json"
    
    try:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2, open(temp_file, 'w') as out_f:
            f1.seek(start)
            f2.seek(start)
            
            if start != 0:
                f1.readline()
                f2.readline()

            out_f.write('[')
            first_entry = True

            while f1.tell() < end or f2.tell() < end:
                line1 = f1.readline()
                line2 = f2.readline()
                
                if not line1 and not line2:
                    break

                s1 = line1.decode('utf-8', errors='ignore').strip() if line1 else ""
                s2 = line2.decode('utf-8', errors='ignore').strip() if line2 else ""

                if (s1.startswith('>') or s2.startswith('>')):
                    continue

                max_len = max(len(s1), len(s2))
                for j in range(max_len):
                    char1 = s1[j] if j < len(s1) else None
                    char2 = s2[j] if j < len(s2) else None
                    
                    if char1 != char2:
                        # Escribimos a disco en vez de guardar en memoria
                        if not first_entry:
                            out_f.write(',')
                        else:
                            first_entry = False
                            
                        # Guardamos un objeto ligero
                        out_f.write(json.dumps([f1.tell(), j, char1, char2]))
                        diff_count += 1
            out_f.write(']')
    except Exception as e:
        print(f"Error procesando chunk {limits}: {e}")
        
    return temp_file, diff_count

def cpu_calculation(path1, path2, num_processes):
    if not os.path.exists(path1) or not os.path.exists(path2):
        raise FileNotFoundError("Uno de los archivos especificados no existe.")

    print(f"Iniciando comparación en paralelo con {num_processes} workers...")
    size1 = os.path.getsize(path1)
    size2 = os.path.getsize(path2)
    max_file_size = max(size1, size2)
    
    # Dividimos el archivo grande en 100 bloques para repartir trabajo y medir avance.
    total_chunks = 100
    chunk_size = (max_file_size // total_chunks) + 1
    chunks = [(i, min(i + chunk_size, max_file_size)) for i in range(0, max_file_size, chunk_size)]

    total_differences = 0
    
    # El JSON final se arma en streaming para no acumular millones de diferencias en RAM.
    print("\nAbriendo archivo final JSON...")
    with DIFFERENCES_JSON_PATH.open("w", encoding="utf-8") as final_json:
        final_json.write('[\n')
        
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            start_time = time.perf_counter()
            
            futures = {executor.submit(process_chunk, path1, path2, chunk): chunk for chunk in chunks}
            
            completed_count = 0
            last_reported_percent = -1
            first_write = True
            
            for future in as_completed(futures):
                try:
                    tmp_file, chunk_diffs = future.result()
                    total_differences += chunk_diffs
                    completed_count += 1
                    
                    # Consolidar cada temporal apenas termina evita dejar muchos archivos pesados sueltos.
                    if tmp_file.exists():
                        with tmp_file.open('r', encoding='utf-8') as tmp_in:
                            content = tmp_in.read()
                            if len(content) > 2: # Si no es solo "[]"
                                if not first_write:
                                    final_json.write(',\n')
                                else:
                                    first_write = False
                                
                                # Quitamos los corchetes exteriores [] del temporal
                                inner_content = content[1:-1]
                                final_json.write(inner_content)
                        tmp_file.unlink()
                    
                    # Calcular porcentaje
                    percent = int((completed_count / total_chunks) * 100)
                    if percent % 10 == 0 and percent != last_reported_percent:
                        print(f"Progreso: {percent}% completado...")
                        last_reported_percent = percent
                        
                except Exception as e:
                    print(f"Error en un worker: {e}")
                
            end_time = time.perf_counter()
            
        final_json.write('\n]')

    return DnaComparison(total_differences, end_time - start_time, ExecutionType.CPU)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Comparador de archivos de ADN en paralelo")
    parser.add_argument("--file1", type=str, required=True, help="Ruta del primer archivo de ADN")
    parser.add_argument("--file2", type=str, required=True, help="Ruta del segundo archivo de ADN")
    parser.add_argument("--workers", type=int, default=4, help="Número de procesos paralelos (default: 4)")
    parser.add_argument("--output", type=str, help="Archivo para guardar resultados (opcional)")

    args = parser.parse_args()

    try:
        res = cpu_calculation(args.file1, args.file2, args.workers)
        
        print("\n" + "="*40)
        print("RESULTADOS DE LA COMPARACIÓN")
        print("="*40)
        print(f"Archivo 1: {os.path.basename(args.file1)}")
        print(f"Archivo 2: {os.path.basename(args.file2)}")
        print(f"Tiempo total: {res.time_taken:.4f} segundos")
        print(f"Total de diferencias: {res.total_differences}")
        
        with EXECUTION_TIME_JSON_PATH.open("w", encoding="utf-8") as f_time:
            json.dump({
                "file1": args.file1,
                "file2": args.file2,
                "time_taken": res.time_taken,
                "total_differences": res.total_differences
            }, f_time, indent=4)
        
        print("\nArchivos 'differences.json' y 'execution_time.json' generados y actualizados correctamente.")

    except Exception as e:
        print(f"Error durante la ejecución: {e}")
