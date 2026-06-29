import os
import uuid
from pathlib import Path

import dropbox
from dotenv import load_dotenv
from dropbox.files import WriteMode

import generador
import secuential_process


BASE_DROPBOX_DIR = "/ADN_CLOUD_GRUPO_AA"
BASE_DIRS = [
    BASE_DROPBOX_DIR,
    f"{BASE_DROPBOX_DIR}/cadenas_originales",
    f"{BASE_DROPBOX_DIR}/resultados",
    f"{BASE_DROPBOX_DIR}/reportes",
    f"{BASE_DROPBOX_DIR}/logs",
]

def listar(dbx, ruta):
    try:
        result = dbx.files_list_folder(ruta,recursive=True)
        for entry in result.entries:
            print(f"- {entry.name}")
    except dropbox.exceptions.ApiError as e:
        if e.error.is_path() and e.error.get_path().is_not_found():
            print(f"No se encontró la carpeta: {ruta}")
        else:
            raise
def crear_estructura(dbx, rutas):
    for ruta in rutas:
        try:
            dbx.files_create_folder_v2(ruta)
            print(f"✓ Creada: {ruta}")
        except dropbox.exceptions.ApiError as e:
            if e.error.is_path() and e.error.get_path().is_conflict():
                print(f"- Ya existe: {ruta}")
            else:
                raise


def subir_archivo(dbx, local_path, remote_path):
    with open(local_path, "rb") as file:
        dbx.files_upload(file.read(), remote_path, mode=WriteMode("overwrite"))
    print(f"↑ Subido: {remote_path}")


def main():
    load_dotenv()

    access_token = os.getenv("ACCESS_TOKEN")
    if not access_token:
        raise ValueError("Falta ACCESS_TOKEN en el archivo .env")

    dbx = dropbox.Dropbox(access_token)
    crear_estructura(dbx, BASE_DIRS)

    job_uuid = str(uuid.uuid4())
    remote_job_dir = f"{BASE_DROPBOX_DIR}/{job_uuid}"
    crear_estructura(dbx, [remote_job_dir])

    input_path = Path("aux/cadenas_originales") / f"cadena_100mb_{job_uuid}.txt"
    output_path = Path("aux/resultados") / f"secuencial_{job_uuid}.json"

    generador.generate_dna_file(input_path, 100, 4)
    secuential_process.main(input=str(input_path), output=str(output_path))

    subir_archivo(dbx, input_path, f"{remote_job_dir}/{input_path.name}")
    subir_archivo(dbx, output_path, f"{remote_job_dir}/{output_path.name}")
    listar(dbx, remote_job_dir)


if __name__ == "__main__":
    main()
