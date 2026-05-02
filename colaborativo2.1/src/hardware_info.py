import psutil
import platform


def get_hardware_info():
    """Recopila información del hardware disponible (CPU, RAM, GPU)."""
    info = {}

    # Sistema operativo y arquitectura
    info["cpu_system"] = platform.system()
    info["cpu_arch"] = platform.machine()

    # RAM
    info["ram_total_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    info["ram_available_gb"] = round(psutil.virtual_memory().available / (1024 ** 3), 2)

    # CPU
    info["cpu_model"] = platform.processor()
    info["cpu_cores"] = psutil.cpu_count(logical=False) or 1
    info["cpu_threads"] = psutil.cpu_count(logical=True) or 1
    freq = psutil.cpu_freq()
    info["cpu_freq_ghz"] = round(freq.max / 1000, 2) if freq else 0

    # FLOPS teóricos CPU:
    # Fórmula: cores × frecuencia(Hz) × FLOPs_por_ciclo
    # Se asume 16 FLOPS/ciclo (AVX-256, doble precisión → 4 doubles × 2 ops × 2 puertos)
    flops_por_ciclo = 16
    info["cpu_flops_theoretical"] = (
        info["cpu_cores"] * info["cpu_freq_ghz"] * 1e9 * flops_por_ciclo
    )

    # GPU NVIDIA (nvidia-smi)
    info["gpu_available"] = False
    info["gpu_model"] = "No detectada"
    try:
        import subprocess
        result = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stderr=subprocess.STDOUT
        ).decode().strip()
        if result:
            info["gpu_available"] = True
            info["gpu_model"] = result.split("\n")[0]
    except Exception:
        pass

    return info