"""
Subida de fotos de perfil a Azure Blob Storage.

Requiere AZURE_STORAGE_CONNECTION_STRING. El contenedor (por defecto "fotos")
se crea solo si no existe.

- AZURE_STORAGE_PUBLICO=true  -> el contenedor es público y se guarda la URL "limpia".
- AZURE_STORAGE_PUBLICO=false (por defecto) -> la URL lleva un token SAS de solo
  lectura válido por un año. Funciona aunque la cuenta no permita acceso anónimo,
  que es lo normal en Azure for Students.
"""
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone

from app.config import AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER

logging.getLogger("azure").setLevel(logging.WARNING)

TIPOS_PERMITIDOS = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
TAMANO_MAXIMO = 5 * 1024 * 1024  # 5 MB


class AlmacenamientoNoConfigurado(Exception):
    pass


def subir_foto(usuario_id: int, contenido: bytes, content_type: str) -> str:
    if not AZURE_STORAGE_CONNECTION_STRING:
        raise AlmacenamientoNoConfigurado("Falta AZURE_STORAGE_CONNECTION_STRING")

    from azure.core.exceptions import ResourceExistsError
    from azure.storage.blob import BlobSasPermissions, BlobServiceClient, ContentSettings, generate_blob_sas

    servicio = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    contenedor = servicio.get_container_client(AZURE_STORAGE_CONTAINER)
    try:
        contenedor.create_container()
    except ResourceExistsError:
        pass

    extension = TIPOS_PERMITIDOS[content_type]
    nombre = f"usuario-{usuario_id}/{uuid.uuid4().hex}.{extension}"
    blob = contenedor.get_blob_client(nombre)
    blob.upload_blob(contenido, overwrite=True, content_settings=ContentSettings(content_type=content_type))

    if os.getenv("AZURE_STORAGE_PUBLICO", "false").lower() == "true":
        return blob.url

    sas = generate_blob_sas(
        account_name=servicio.account_name,
        container_name=AZURE_STORAGE_CONTAINER,
        blob_name=nombre,
        account_key=servicio.credential.account_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(days=365),
    )
    return f"{blob.url}?{sas}"
