import matplotlib.pyplot as plt
import os
import json
from datetime import datetime

def cargar_historico():
    """Carga el histórico de ejecuciones desde el archivo JSON"""
    archivo_historico = "report/historico_ejecutores.json"
    if os.path.exists(archivo_historico):
        try:
            with open(archivo_historico, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def guardar_historico(historico):
    """Guarda el histórico de ejecuciones en un archivo JSON"""
    archivo_historico = "report/historico_ejecutores.json"
    with open(archivo_historico, "w", encoding="utf-8") as f:
        json.dump(historico, f, indent=2, ensure_ascii=False)

def generate_report_and_plot(hw_info, flops_real, nombre_usuario):
    os.makedirs("report", exist_ok=True)

    cpu_theoretical = hw_info["cpu_flops_theoretical"]
    
    # Cargar y actualizar histórico
    historico = cargar_historico()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    historico.append({
        "nombre": nombre_usuario,
        "fecha": timestamp,
        "flops_reales": flops_real,
        "cpu_model": hw_info['cpu_model']
    })
    guardar_historico(historico)

    # ------- PLOT -------
    plt.figure(figsize=(8,5))
    plt.bar(["Teórico CPU", "Real"], [cpu_theoretical, flops_real])
    plt.ylabel("FLOPS")
    plt.title("Desempeño de Cómputo (CPU)")
    plt.savefig("report/resultados.png")
    plt.close()

    # ------- REPORTE -------
    with open("report/reporte.txt", "w", encoding="utf-8") as f:
        f.write("===== REPORTE DE RENDIMIENTO =====\n\n")
        f.write(f"Ejecutado por: {nombre_usuario}\n")
        f.write(f"Fecha: {timestamp}\n\n")
        f.write(f"CPU detectada: {hw_info['cpu_model']}\n")
        f.write(f"Núcleos: {hw_info['cpu_cores']} | Hilos: {hw_info['cpu_threads']}\n")
        f.write(f"Frecuencia máxima: {hw_info['cpu_freq_ghz']} GHz\n\n")
        
        f.write("--- GPU ---\n")
        f.write("GPU detectada: SI\n" if hw_info["gpu_available"] else "GPU detectada: NO\n")
        
        f.write("\n--- FLOPS ---\n")
        f.write(f"FLOPS teóricos CPU: {cpu_theoretical:,.2f}\n")
        f.write(f"FLOPS reales CPU: {flops_real:,.2f}\n")
        
        # Agregar histórico de personas anteriores
        f.write("\n--- HISTÓRICO DE EJECUTORES ---\n")
        if len(historico) > 1:
            f.write(f"Total de ejecuciones: {len(historico)}\n\n")
            f.write("Ejecutores anteriores:\n")
            for i, entrada in enumerate(historico[:-1], 1):
                f.write(f"  {i}. {entrada['nombre']} - {entrada['fecha']} (FLOPS: {entrada['flops_reales']:,.2f})\n")
        else:
            f.write("Primera ejecución registrada.\n")
