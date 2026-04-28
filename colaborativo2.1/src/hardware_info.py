import psutil
import platform

def get_hardware_info():
    info = {}
    
    # Información del sistema
    info["cpu_system"] = platform.system()
    info["cpu_arch"] = platform.machine()
    info["ram_total_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    info["ram_available_gb"] = round(psutil.virtual_memory().available / (1024 ** 3), 2)

    # Información de CPU
    info["cpu_model"] = platform.processor()
    info["cpu_cores"] = psutil.cpu_count(logical=False)
    info["cpu_threads"] = psutil.cpu_count(logical=True)
    freq = psutil.cpu_freq()

    info["cpu_freq_ghz"] = round(freq.max / 1000, 2) if freq else 0

    # GPU (solo detecta NVIDIA si existe)
    try:
        import subprocess
        result = subprocess.check_output(["nvidia-smi", "-q"], stderr=subprocess.STDOUT)
        info["gpu_nvidia_detected"] = True
    except Exception:
        info["gpu_nvidia_detected"] = False

    return info
