import json
import os
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import FastAPI, File, Form, UploadFile
from secuential_process import procesar
from starlette.concurrency import run_in_threadpool

app = FastAPI()


@app.post("/analizar")
async def analizar(
    file: Annotated[UploadFile, File()],
    patterns: Annotated[str, Form()] = "ATGCGT,TATA,GATTACA",
    chunk_mb: Annotated[int, Form()] = 32,
):
    temp_dir = Path("uploads")
    results_dir = Path("results")

    temp_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    input_path = temp_dir / f"{uuid4()}_{file.filename}"
    output_path = results_dir / f"{uuid4()}_secuencial.json"

    try:
        with open(input_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
        await run_in_threadpool(
            procesar,
            input=str(input_path),
            patterns=patterns,
            chunk_mb=chunk_mb,
            output=str(output_path),
        )
        with open(output_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        return result

    finally:
        if input_path.exists():
            os.remove(input_path)
        if output_path.exists():
            os.remove(output_path)
