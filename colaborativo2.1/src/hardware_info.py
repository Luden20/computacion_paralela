import psutil
import platform

def get_hardware_info():
    info = {}
    
    # CPU info
    info["cpu_model"] = platform.processor()
    info["cpu_cores"] = psutil.cpu_count(logical=False)
    info["cpu_threads"] = psutil.cpu_count(logical=True)
    freq = psutil.cpu_freq()
    
    info["cpu_freq_ghz"] = round(freq.max / 1000, 2) if freq else 0

    # FLOPS teóricos aproximados de CPU
    # fórmula simple: FLOPS = núcleos * GHz * instrucciones por ciclo
    info["cpu_flops_theoretical"] = (
        info["cpu_cores"]
        * info["cpu_freq_ghz"]
        * 10**9
        * 16  # aprox. SIMD AVX2 (puede variar)
    )

    # GPU (solo detecta si NVIDIA está presente)
    try:
        import subprocess
        result = subprocess.check_output(["nvidia-smi", "-q"], stderr=subprocess.STDOUT)
        info["gpu_available"] = True
    except:
        info["gpu_available"] = False

    return info
