"""Validación y escritura acotada de documentos institucionales."""

import os
import re
import tempfile
import unicodedata
import zipfile
from pathlib import Path

from fastapi import HTTPException, UploadFile


ZIP_MARKERS = {
    ".docx": "word/document.xml",
    ".pptx": "ppt/presentation.xml",
    ".xlsx": "xl/workbook.xml",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".md"}
WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}


def validated_filename(name: str | None, allowed_extensions=ALLOWED_EXTENSIONS) -> str:
    if not name:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    # Windows/OneDrive may supply accented characters as a base letter plus a
    # combining mark. Normalize canonically so visually identical filenames
    # pass the same safe-character validation.
    name = unicodedata.normalize("NFC", name)
    if len(name) > 180 or name != Path(name).name:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")
    if (name in {".", ".."} or name.rstrip(" .") != name
            or not re.fullmatch(r"[\w .(),&\-]+", name, flags=re.UNICODE)
            or Path(name).stem.upper() in WINDOWS_RESERVED):
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")
    if Path(name).suffix.lower() not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Tipo de documento no admitido")
    return name


def validate_document(path: Path, extension: str | None = None) -> None:
    ext = extension or path.suffix.lower()
    if ext == ".pdf":
        with path.open("rb") as source:
            if source.read(5) != b"%PDF-":
                raise HTTPException(status_code=400, detail="El contenido no es un PDF válido")
    elif ext in ZIP_MARKERS:
        try:
            with zipfile.ZipFile(path) as archive:
                members = archive.infolist()
                if (len(members) > 3000 or
                        sum(member.file_size for member in members) > 200 * 1024 * 1024 or
                        "[Content_Types].xml" not in archive.namelist() or
                        ZIP_MARKERS[ext] not in archive.namelist()):
                    raise HTTPException(status_code=400, detail="Documento Office inválido o demasiado grande")
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Documento Office inválido") from None
    else:
        try:
            path.read_text(encoding="utf-8")
        except UnicodeError:
            raise HTTPException(status_code=400, detail="El archivo de texto debe ser UTF-8") from None


async def save_upload(file: UploadFile, destination: Path, max_bytes: int) -> int:
    """Guarda en temporal, valida y reemplaza sin seguir symlinks del destino."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    total = 0
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".upload-", delete=False) as output:
            temp_path = Path(output.name)
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(status_code=413, detail="El archivo excede el tamaño permitido")
                output.write(chunk)
        if total == 0:
            raise HTTPException(status_code=400, detail="El archivo está vacío")
        validate_document(temp_path, destination.suffix.lower())
        os.replace(temp_path, destination)
        return total
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
