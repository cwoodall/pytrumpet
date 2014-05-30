import multiprocessing as mp
import time

def f(freq):
    for i in range(10):
        freq.value = i
        time.sleep(1)
# Create shared memory using multiprocessing.Value class, which allows for
# the creation of shared memory between two processes.

# https://docs.python.org/2/library/multiprocessing.html
if __name__ == '__main__':
    freq = mp.Value('d', -1.0)
    p = mp.Process(target=f, args=(freq,))
    p.start()
    while freq.value < 9:
        print freq.value
    p.join()
