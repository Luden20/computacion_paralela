import json
import os
from datetime import datetime
import matplotlib.pyplot as plt

HISTORICO_PATH = "report/historico.json"

def cargar_historico():
    """Carga el archivo JSON histórico, o crea uno vacío."""
    if not os.path.exists(HISTORICO_PATH):
        return []
    with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def guardar_historico(data):
    """Guarda el historial actualizado."""
    with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def generate_report_and_plot(hw_info, flops_real, nombre_usuario):
    os.makedirs("report", exist_ok=True)

    cpu_theoretical = hw_info["cpu_flops_theoretical"]
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ============================
    # 1) Actualizar JSON histórico
    # ============================
    historico = cargar_historico()

    entrada = {
        "usuario": nombre_usuario,
        "fecha": timestamp,
        "hardware_info": hw_info,
        "flops_reales": flops_real,
        "flops_teoricos": cpu_theoretical,
        "eficiencia_cpu_pct": (flops_real / cpu_theoretical) * 100 if cpu_theoretical > 0 else None
    }

    # Si ya existe una entrada idéntica, no duplicar
    if entrada not in historico:
        historico.append(entrada)

    guardar_historico(historico)

    # ============================
    # 2) Gráfico
    # ============================
    plt.figure(figsize=(8, 5))
    plt.bar(["Teórico CPU", "Real"], [cpu_theoretical, flops_real])
    plt.ylabel("FLOPS")
    plt.title("Desempeño de Cómputo (CPU)")
    plt.savefig("report/resultados.png")
    plt.close()

    # ============================
    # 3) Reporte en TXT
    # ============================
    with open("report/reporte.txt", "w", encoding="utf-8") as f:
        f.write("===== REPORTE DE RENDIMIENTO =====\n\n")
        f.write(f"Ejecutado por: {nombre_usuario}\n")
        f.write(f"Fecha: {timestamp}\n\n")

        f.write("---- HARDWARE DETECTADO ----\n")
        for k, v in hw_info.items():
            f.write(f"{k}: {v}\n")

        f.write("\n---- RESULTADOS ----\n")
        f.write(f"FLOPS teóricos CPU: {cpu_theoretical:.2e}\n")
        f.write(f"FLOPS reales CPU:   {flops_real:.2e}\n")

        eficiencia = (flops_real / cpu_theoretical) * 100 if cpu_theoretical > 0 else 0
        f.write(f"Eficiencia CPU:     {eficiencia:.2f}%\n\n")

        f.write("Gráfico guardado en: report/resultados.png\n")
        f.write("Histórico actualizado en: report/historico.json\n")
