import time
import numpy as np


def run_benchmark(size=1000):
    """
    Ejecuta un benchmark de multiplicación de matrices (size x size) con NumPy.
    Retorna los FLOPS reales medidos.
    """
    A = np.random.rand(size, size)
    B = np.random.rand(size, size)

    start = time.time()
    _ = np.dot(A, B)
    elapsed = time.time() - start

    # Operaciones de punto flotante: ~2 × N³ (multiply-add por elemento)
    flops = 2 * (size ** 3)
    return flops / elapsed