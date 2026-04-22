import time
import numpy as np

def run_benchmark(size=1000):
    A = np.random.rand(size, size)
    B = np.random.rand(size, size)

    start = time.time()
    C = np.dot(A, B)
    end = time.time()

    # operaciones aproximadas
    flops = 2 * (size ** 3)
    seconds = end - start

    return flops / seconds
