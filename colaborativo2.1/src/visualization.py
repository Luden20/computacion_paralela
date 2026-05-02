import json
import os
from datetime import datetime
import matplotlib.pyplot as plt

HISTORICO_PATH = "report/historico.json"


def cargar_historico():
    """Carga el historial JSON o devuelve lista vacía si no existe."""
    if not os.path.exists(HISTORICO_PATH):
        return []
    with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def guardar_historico(data):
    """Persiste el historial actualizado en disco."""
    with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def generate_report_and_plot(hw_info, flops_real, nombre_usuario):
    """
    Genera:
      - report/historico.json  (acumulativo por usuario)
      - report/resultados.png  (gráfico de barras)
      - report/reporte.txt     (reporte de texto)
    """
    os.makedirs("report", exist_ok=True)

    cpu_theoretical = hw_info["cpu_flops_theoretical"]
    eficiencia = (flops_real / cpu_theoretical * 100) if cpu_theoretical > 0 else 0
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── 1. Historial acumulativo ──────────────────────────────────────────────
    historico = cargar_historico()
    entrada = {
        "usuario": nombre_usuario,
        "fecha": timestamp,
        "hardware": {
            "cpu_model": hw_info["cpu_model"],
            "cpu_cores": hw_info["cpu_cores"],
            "cpu_threads": hw_info["cpu_threads"],
            "cpu_freq_ghz": hw_info["cpu_freq_ghz"],
            "ram_total_gb": hw_info["ram_total_gb"],
            "gpu_model": hw_info["gpu_model"],
        },
        "flops_teoricos": cpu_theoretical,
        "flops_reales": flops_real,
        "eficiencia_pct": round(eficiencia, 2),
    }
    historico.append(entrada)
    guardar_historico(historico)

    # ── 2. Gráfico de barras ──────────────────────────────────────────────────
    etiquetas = ["Teórico CPU", "Real CPU"]
    valores = [cpu_theoretical, flops_real]
    colores = ["#4C72B0", "#55A868"]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(etiquetas, valores, color=colores, width=0.5)
    ax.set_ylabel("FLOPS", fontsize=12)
    ax.set_title(f"Desempeño de Cómputo — {nombre_usuario}\n{timestamp}", fontsize=13)
    ax.bar_label(bars, fmt="%.2e", padding=4, fontsize=10)

    # Línea de eficiencia como anotación
    ax.annotate(
        f"Eficiencia: {eficiencia:.1f}%",
        xy=(1, flops_real),
        xytext=(1.15, (cpu_theoretical + flops_real) / 2),
        arrowprops=dict(arrowstyle="->"),
        fontsize=10,
    )

    plt.tight_layout()
    plt.savefig("report/resultados.png", dpi=150)
    plt.close()

    # ── 3. Reporte TXT ────────────────────────────────────────────────────────
    with open("report/reporte.txt", "w", encoding="utf-8") as f:
        f.write("===== REPORTE DE RENDIMIENTO =====\n\n")
        f.write(f"Ejecutado por : {nombre_usuario}\n")
        f.write(f"Fecha         : {timestamp}\n\n")

        f.write("---- HARDWARE DETECTADO ----\n")
        f.write(f"CPU Modelo    : {hw_info['cpu_model']}\n")
        f.write(f"Arquitectura  : {hw_info['cpu_arch']}\n")
        f.write(f"Núcleos       : {hw_info['cpu_cores']}\n")
        f.write(f"Hilos         : {hw_info['cpu_threads']}\n")
        f.write(f"Frecuencia    : {hw_info['cpu_freq_ghz']} GHz\n")
        f.write(f"RAM Total     : {hw_info['ram_total_gb']} GB\n")
        f.write(f"RAM Disponible: {hw_info['ram_available_gb']} GB\n")
        f.write(f"GPU           : {hw_info['gpu_model']}\n\n")

        f.write("---- RESULTADOS ----\n")
        f.write(f"FLOPS teóricos CPU : {cpu_theoretical:.4e}\n")
        f.write(f"FLOPS reales CPU   : {flops_real:.4e}\n")
        f.write(f"Eficiencia CPU     : {eficiencia:.2f}%\n\n")

        f.write("Gráfico    : report/resultados.png\n")
        f.write("Histórico  : report/historico.json\n")
        f.write("\n===== FIN DEL REPORTE =====\n")

    print(f"  → Historial : {HISTORICO_PATH}  ({len(historico)} entrada(s))")
    print(f"  → Gráfico   : report/resultados.png")
    print(f"  → Reporte   : report/reporte.txt")