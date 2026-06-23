from time import perf_counter

from fastapi import FastAPI
from pydantic import BaseModel

from algs.generals import bubbleSort, insertionSort, selection_sort
from algs.merge import mergeSort
from algs.quick import quickSort
from res import Response

app = FastAPI()


class SortBody(BaseModel):
    arr: list[int]


def run_sort(arr: list[int], sorter) -> Response:
    ordered = arr.copy()
    start = perf_counter()
    sorter(ordered)
    elapsed = perf_counter() - start
    return Response(n=len(ordered), arr=ordered, tiempo=elapsed)


@app.post("/bubble")
def bubble(body: SortBody):
    return run_sort(body.arr, bubbleSort)


@app.post("/selection")
def selection(body: SortBody):
    return run_sort(body.arr, selection_sort)


@app.post("/insertion")
def insertion(body: SortBody):
    return run_sort(body.arr, insertionSort)


@app.post("/quick")
def quick(body: SortBody):
    return run_sort(body.arr, lambda arr: quickSort(arr, 0, len(arr) - 1))


@app.post("/merge")
def merge(body: SortBody):
    return run_sort(body.arr, lambda arr: mergeSort(arr, 0, len(arr) - 1))
