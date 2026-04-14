import argparse
import os
import time
import json
from collections import Counter
from itertools import repeat
from concurrent.futures import ProcessPoolExecutor, as_completed
from enum import Enum
from dataclasses import dataclass

# Estructuras de datos para los resultados
class ExecutionType(Enum):
    CPU = "CPU"
    GPU = "GPU"

@dataclass
class DnaComparison:
    differences: list
    time_taken: float
    execution_type: ExecutionType

def process_chunk(file1, file2, limits):
    """
    Procesa un bloque de los archivos y busca diferencias carácter por carácter,
    omitiendo las líneas de cabecera (que empiezan con '>').
    """
    start, end = limits
    differences = []

    try:
        with open(file1, 'rb') as f1, open(file2, 'rb') as f2:
            f1.seek(start)
            f2.seek(start)
            
            # Si no es el inicio del archivo, descartamos la línea actual para 
            # asegurar que empezamos al inicio de una línea completa (opcional según el formato)
            if start != 0:
                f1.readline()
                f2.readline()

            while f1.tell() < end or f2.tell() < end:
                line1 = f1.readline()
                line2 = f2.readline()
                
                if not line1 and not line2:
                    break

                # Decodificamos las líneas (maneja archivo agotado)
                s1 = line1.decode('utf-8', errors='ignore').strip() if line1 else ""
                s2 = line2.decode('utf-8', errors='ignore').strip() if line2 else ""

                # Ignorar cabeceras FASTA (solo si ambas existen o una existe y no es el final)
                if (s1.startswith('>') or s2.startswith('>')):
                    continue

                # Comparar base por base
                max_len = max(len(s1), len(s2))
                for j in range(max_len):
                    char1 = s1[j] if j < len(s1) else None
                    char2 = s2[j] if j < len(s2) else None
                    
                    if char1 != char2:
                        # Guardamos la posición aproximada y los caracteres
                        differences.append((f1.tell(), j, char1, char2))
    except Exception as e:
        print(f"Error procesando chunk {limits}: {e}")
        
    return differences

def cpu_calculation(path1, path2, num_processes):
    if not os.path.exists(path1) or not os.path.exists(path2):
        raise FileNotFoundError("Uno de los archivos especificados no existe.")

    print(f"Iniciando comparación en paralelo con {num_processes} workers...")
    size1 = os.path.getsize(path1)
    size2 = os.path.getsize(path2)
    max_file_size = max(size1, size2)
    
    # Para reportar progreso cada 10%, dividimos en 100 trozos
    total_chunks = 100
    chunk_size = (max_file_size // total_chunks) + 1
    chunks = [(i, min(i + chunk_size, max_file_size)) for i in range(0, max_file_size, chunk_size)]

    all_differences = []
    worker_count = max(1, num_processes)
    
    with ProcessPoolExecutor(max_workers=worker_count) as executor:
        start_time = time.perf_counter()
        
        # Usamos submit para rastrear el progreso de cada chunk
        futures = {executor.submit(process_chunk, path1, path2, chunk): chunk for chunk in chunks}
        
        completed_count = 0
        last_reported_percent = -1
        
        for future in as_completed(futures):
            try:
                res_chunk = future.result()
                all_differences.extend(res_chunk)
                completed_count += 1
                
                # Calcular porcentaje
                percent = int((completed_count / total_chunks) * 100)
                if percent % 10 == 0 and percent != last_reported_percent:
                    print(f"Progreso: {percent}% completado...")
                    last_reported_percent = percent
                    
            except Exception as e:
                print(f"Error en un worker: {e}")
            
        end_time = time.perf_counter()

    return DnaComparison(all_differences, end_time - start_time, ExecutionType.CPU)

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
        print(f"Total de diferencias: {len(res.differences)}")
        
        # Guardar en JSON
        print("\nGuardando resultados en JSON...")
        with open("differences.json", "w") as f_diff:
            json.dump(res.differences, f_diff, indent=4)
        
        with open("execution_time.json", "w") as f_time:
            json.dump({
                "file1": args.file1,
                "file2": args.file2,
                "time_taken": res.time_taken,
                "total_differences": len(res.differences)
            }, f_time, indent=4)
        
        print("Archivos 'differences.json' y 'execution_time.json' generados.")

        if res.differences:
            print("\nPrimeras diferencias encontradas (Offset, Columna, Valor1, Valor2):")
            for diff in res.differences[:15]:
                v1 = diff[2] if diff[2] else "[VACÍO]"
                v2 = diff[3] if diff[3] else "[VACÍO]"
                print(f" -> Pos: {diff[0]} | Col: {diff[1]} | '{v1}' vs '{v2}'")
        else:
            print("\n¡Los archivos son idénticos en sus secuencias!")

    except Exception as e:
        print(f"Error durante la ejecución: {e}")