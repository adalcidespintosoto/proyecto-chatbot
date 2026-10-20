"""Sanitize source PDF/PPTX/DOCX files to Markdown, then index that output.

Initial clean migration (stop UniMon first):
    python scripts/ingest_sanitized_documents.py --rebuild

Incremental scan (also used by the application upload endpoints):
    python scripts/ingest_sanitized_documents.py

The clean migration builds and validates an isolated Chroma database before
backing up and replacing the active database. The Golden Cache is backed up
but never cleared or rewritten by this ingestion pipeline.
"""

from __future__ import annotations

import argparse
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
import gc
import hashlib
import json
import logging
import os
import socket
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import chromadb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.services.sanitized_documents import (
    expected_source_markers,
    format_extracted_source,
    load_document_prompt,
    split_markdown_for_rag,
)
from scripts import sanitize_rag_corpus as sanitizer

LOGGER = logging.getLogger("unimon.ingest_sanitized_documents")
PROMPT_PATH = PROJECT_ROOT / "docs" / "PROMPT_TRANSFORMACION_DOCUMENTOS_RAG.md"
SUPPORTED_EXTENSIONS = {".pdf", ".pptx", ".docx"}
WEB_SOURCE_PREFIXES = ("Web_",)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_manifest(path: Path) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for item in sorted(path.rglob("*")):
        if item.is_file():
            files[item.relative_to(path).as_posix()] = {
                "bytes": item.stat().st_size,
                "sha256": _file_sha256(item),
            }
    return files


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _source_key(path: Path, docs_dir: Path) -> str:
    try:
        return path.resolve().relative_to(docs_dir.resolve()).as_posix()
    except ValueError:
        return path.name


def _safe_markdown_path(output_dir: Path, record: dict[str, Any]) -> Path:
    relative = record.get("markdown_relative_path")
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError("El registro no contiene una ruta de Markdown válida.")
    root = output_dir.resolve()
    target = (root / relative).resolve()
    if target == root or root not in target.parents:
        raise ValueError("La ruta Markdown del manifiesto sale de SANITIZED_DOCS_DIR.")
    return target


def _paths_overlap(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def _discover_sources(docs_dir: Path, file_path: str | None = None) -> list[Path]:
    if file_path:
        path = Path(file_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"No existe el documento: {path}")
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError("La ingesta Markdown admite documentos PDF y PPTX.")
        return [path]
    if not docs_dir.exists():
        raise FileNotFoundError(f"No existe el directorio de documentos: {docs_dir}")
    return sorted(
        (
            path for path in docs_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
        ),
        key=lambda path: path.as_posix().casefold(),
    )


def _display_sources(paths: list[Path], docs_dir: Path) -> dict[str, str]:
    keys = {path: _source_key(path, docs_dir) for path in paths}
    basenames = Counter(path.name for path in paths)
    return {
        keys[path]: path.name if basenames[path.name] == 1 else keys[path]
        for path in paths
    }


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schema_version": 2, "records": {}}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or not isinstance(manifest.get("records", {}), dict):
            raise ValueError("estructura inesperada")
        manifest.setdefault("schema_version", 2)
        manifest.setdefault("records", {})
        return manifest
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"El manifiesto de Markdown no se puede leer ({path}): {exc}") from exc


def _prepare_markdown(
    paths: list[Path],
    docs_dir: Path,
    output_dir: Path,
    force: bool = False,
    use_vision: bool = True,
    workers: int = 2,
    source_texts: dict[str, str] | None = None,
    source_unit_counts: dict[str, int] | None = None,
    source_visual_slide_numbers: dict[str, list[int]] | None = None,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if not 1 <= workers <= 4:
        raise ValueError("workers debe estar entre 1 y 4.")
    settings = get_settings()
    if settings.openai_model.strip() != "gpt-6-luna":
        raise RuntimeError(
            "La transformación está configurada para GPT-6 Luna; "
            f"OPENAI_MODEL actual: {settings.openai_model!r}."
        )
    prompt = load_document_prompt(PROMPT_PATH)
    prompt_hash = sanitizer.sha256_text(prompt)
    manifest_path = output_dir / "manifest.json"
    manifest = _load_manifest(manifest_path)
    current_records: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    displays = _display_sources(paths, docs_dir)

    manifest.update({
        "schema_version": 2,
        "transform_provider": "openai",
        "transform_model": "gpt-6-luna",
        "embedding_model": settings.embedding_model,
        "prompt_path": str(PROMPT_PATH),
        "prompt_sha256": prompt_hash,
        "raw_documents_modified": False,
        "last_scan_started_utc": datetime.now(timezone.utc).isoformat(),
    })

    pending: dict[Future, tuple[int, str, str, str, Path, int, int, int, float]] = {}

    def persist_finished(done: set[Future]) -> None:
        for future in done:
            index, key, display, source_hash, source_file, source_size, source_mtime_ns, extracted_units, started = pending.pop(future)
            record: dict[str, Any] | None = None
            try:
                record = future.result()
                current_stat = source_file.stat()
                if current_stat.st_size != source_size or current_stat.st_mtime_ns != source_mtime_ns:
                    raise RuntimeError("El documento fuente cambió mientras se transformaba; vuelve a ejecutar la ingesta.")
                record.update({"source_path": key, "source": display, "source_filename": Path(key).name})
                if record.get("status") != "success":
                    raise RuntimeError(record.get("error", "El Markdown no superó la validación."))
                record["source_size_bytes"] = source_size
                record["source_mtime_ns"] = source_mtime_ns
                record["extracted_units"] = extracted_units
                manifest["transform_provider"] = record.get("transform_provider", "openai")
                manifest["transform_model"] = record.get("transform_model", "gpt-6-luna")
                manifest["records"][key] = record
                current_records[key] = record
                LOGGER.info(
                    "[%d/%d] Markdown validado y guardado: %s -> %s",
                    index,
                    len(paths),
                    key,
                    output_dir / record["markdown_relative_path"],
                )
            except Exception as exc:
                failures.append(key)
                failed_record = dict(record or {})
                failed_record.update({
                    "status": "failed",
                    "source_path": key,
                    "source": display,
                    "source_filename": Path(key).name,
                    "source_sha256": source_hash,
                    "source_size_bytes": source_size,
                    "source_mtime_ns": source_mtime_ns,
                    "prompt_sha256": prompt_hash,
                    "error": str((record or {}).get("error") or exc)[:1000],
                    "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                })
                failed_record.setdefault("elapsed_seconds", round(time.perf_counter() - started, 3))
                manifest["records"][key] = failed_record
                LOGGER.error("Markdown no aprobado para %s: %s", key, exc)
            _write_json(manifest_path, manifest)

    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="unimon-md-sanitize") as pool:
        for index, path in enumerate(paths, start=1):
            key = _source_key(path, docs_dir)
            display = displays[key]
            source_stat = path.stat()
            source_hash = _file_sha256(path)
            existing = manifest["records"].get(key, {})
            try:
                markdown_path = _safe_markdown_path(output_dir, existing)
            except ValueError:
                markdown_path = output_dir / "__missing__"
            if not force and sanitizer.validate_manifest_record(existing, source_hash, prompt_hash, markdown_path):
                existing.update({
                    "source_path": key,
                    "source": display,
                    "source_filename": path.name,
                    "source_size_bytes": source_stat.st_size,
                    "source_mtime_ns": source_stat.st_mtime_ns,
                })
                current_records[key] = existing
                LOGGER.info("[%d/%d] Markdown vigente; sin llamada al LLM: %s", index, len(paths), key)
                continue

            started = time.perf_counter()
            try:
                rejected_draft: str | None = None
                if (
                    existing.get("status") == "failed"
                    and existing.get("source_sha256") == source_hash
                    and existing.get("prompt_sha256") == prompt_hash
                ):
                    rejected_relative = existing.get("rejected_markdown_relative_path")
                    if not isinstance(rejected_relative, str) or not rejected_relative.strip():
                        # Older manifests did not retain this pointer. The deterministic
                        # filename lets us safely resume from that same source's draft.
                        rejected_relative = str(Path("rejected") / sanitizer.markdown_filename(display))
                    output_root = output_dir.resolve()
                    rejected_path = (output_root / rejected_relative).resolve()
                    if output_root in rejected_path.parents and rejected_path.is_file():
                        expected_hash = existing.get("rejected_markdown_sha256")
                        actual_hash = _file_sha256(rejected_path)
                        if not expected_hash or actual_hash == expected_hash:
                            rejected_draft = rejected_path.read_text(encoding="utf-8")
                            LOGGER.info(
                                "Reutilizando borrador rechazado para reparar solo las citas faltantes: %s",
                                key,
                            )

                LOGGER.info("[%d/%d] Extrayendo fuente: %s", index, len(paths), key)
                extracted = sanitizer.extract_file(path, use_vision=use_vision)
                if not extracted:
                    raise RuntimeError("La extracción no produjo páginas o diapositivas con contenido.")
                markers = expected_source_markers(extracted)
                source_text = format_extracted_source(display, extracted)
                if source_texts is not None:
                    source_texts[key] = source_text
                if source_unit_counts is not None:
                    source_unit_counts[key] = len(extracted)
                if source_visual_slide_numbers is not None:
                    source_visual_slide_numbers[key] = sorted({
                        int(document.metadata.get("slide_number"))
                        for document in extracted
                        if document.metadata.get("slide_number") is not None
                        and (document.metadata.get("has_images") or "[Imagen:" in (document.page_content or ""))
                    })
                future = pool.submit(
                    sanitizer.transform_prepared_source,
                    settings,
                    prompt,
                    display,
                    source_hash,
                    prompt_hash,
                    source_text,
                    markers,
                    output_dir,
                    rejected_draft,
                )
                pending[future] = (
                    index, key, display, source_hash, path.resolve(), source_stat.st_size,
                    source_stat.st_mtime_ns, len(extracted), started,
                )
            except Exception as exc:
                failures.append(key)
                manifest["records"][key] = {
                    "status": "failed",
                    "source_path": key,
                    "source": display,
                    "source_filename": path.name,
                    "source_sha256": source_hash,
                    "source_size_bytes": source_stat.st_size,
                    "source_mtime_ns": source_stat.st_mtime_ns,
                    "prompt_sha256": prompt_hash,
                    "error": str(exc)[:1000],
                    "elapsed_seconds": round(time.perf_counter() - started, 3),
                    "failed_at_utc": datetime.now(timezone.utc).isoformat(),
                }
                LOGGER.exception("Falló la extracción de %s", key)
                _write_json(manifest_path, manifest)

            if len(pending) >= workers * 2:
                persist_finished({next(as_completed(tuple(pending)))})

        for future in as_completed(tuple(pending)):
            persist_finished({future})

    manifest["last_scan_finished_utc"] = datetime.now(timezone.utc).isoformat()
    manifest["documents_seen"] = len(paths)
    manifest["documents_ready"] = len(current_records)
    manifest["documents_failed"] = failures
    _write_json(manifest_path, manifest)
    return current_records, failures


def _collection_and_client(path: Path, create: bool, metadata: dict[str, Any] | None = None):
    client = chromadb.PersistentClient(path=str(path))
    try:
        collection = client.get_collection("langchain")
    except Exception:
        if not create:
            client.close()
            raise
        try:
            collection = client.create_collection("langchain", metadata=metadata or {"hnsw:space": "l2"})
        except Exception:
            client.close()
            raise
    return client, collection


def _active_collection_metadata(path: Path) -> dict[str, Any]:
    client = None
    try:
        client, collection = _collection_and_client(path, create=False)
        metadata = dict(collection.metadata or {})
        return metadata or {"hnsw:space": "l2"}
    except Exception:
        return {"hnsw:space": "l2"}
    finally:
        if client is not None:
            client.close()


def _preserve_public_web_markdown(
    database_path: Path,
    output_dir: Path,
) -> dict[str, dict[str, Any]]:
    """Persist the currently indexed public-web fragments as ordered Markdown files."""
    try:
        client, collection = _collection_and_client(database_path, create=False)
    except Exception as exc:
        if not database_path.exists():
            LOGGER.info("No existe un índice activo desde el cual conservar páginas web.")
            return {}
        raise RuntimeError(
            f"No se pudieron leer las fuentes web del índice activo {database_path}; "
            "se cancela el rebuild para evitar perderlas."
        ) from exc

    try:
        count = collection.count()
        if not count:
            return {}
        rows = collection.get(include=["documents", "metadatas"], limit=count)
    finally:
        client.close()
    grouped: dict[str, list[tuple[dict[str, Any], str]]] = {}
    for document, raw_metadata in zip(rows.get("documents") or [], rows.get("metadatas") or []):
        metadata = raw_metadata or {}
        source = str(metadata.get("source", ""))
        is_web = (
            source.startswith(WEB_SOURCE_PREFIXES)
            or metadata.get("source_type") in {"public_web", "public_web_ui"}
            or metadata.get("source_origin_type") in {"public_web", "public_web_ui"}
        )
        if not is_web:
            continue
        if not source.startswith(WEB_SOURCE_PREFIXES):
            raise RuntimeError(f"Fragmento web sin nombre de fuente Web_ verificable: {source!r}")
        if metadata.get("source_type") not in {"public_web", "public_web_ui", "sanitized_markdown"}:
            raise RuntimeError(f"Tipo de fuente web no reconocido para {source}: {metadata.get('source_type')!r}")
        if not isinstance(document, str) or not document.strip():
            raise RuntimeError(f"El fragmento web {source} está vacío; se cancela para no perderlo.")
        grouped.setdefault(source, []).append((metadata, document.strip()))
    del collection, client

    if not grouped:
        LOGGER.info("El RAG activo no contiene fragmentos Web_ para conservar.")
        return {}

    from scripts.ingest_public_web import is_allowed_public_url

    web_records: dict[str, dict[str, Any]] = {}
    web_root = output_dir / "markdown" / "public_web"
    for source, fragments in sorted(grouped.items()):
        ordered = sorted(
            fragments,
            key=lambda item: int(item[0].get("chunk_index", -1)),
        )
        indices = [int(metadata.get("chunk_index", -1)) for metadata, _ in ordered]
        if indices != list(range(len(ordered))):
            raise RuntimeError(
                f"El orden de los fragmentos web no se puede verificar para {source}: {indices[:20]}"
            )

        first_metadata = ordered[0][0]
        source_url = str(first_metadata.get("source_url", ""))
        if not is_allowed_public_url(source_url):
            raise RuntimeError(f"La URL institucional del fragmento web no es válida: {source_url!r}")
        source_type = str(
            first_metadata.get("source_origin_type")
            or first_metadata.get("source_type", "public_web")
        )
        for metadata, _ in ordered:
            if str(metadata.get("source_url", "")) != source_url:
                raise RuntimeError(f"Una fuente web mezcla URLs distintas: {source}")
            fragment_type = str(metadata.get("source_origin_type") or metadata.get("source_type", ""))
            if fragment_type != source_type:
                raise RuntimeError(f"Una fuente web mezcla tipos de fragmento: {source}")

        relative_dir = Path("markdown") / "public_web" / Path(sanitizer.markdown_filename(source)).stem
        fragment_records: list[dict[str, Any]] = []
        source_content: list[str] = []
        for (metadata, content), index in zip(ordered, indices):
            relative_path = relative_dir / f"fragment_{index:04d}.md"
            markdown_path = output_dir / relative_path
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = markdown_path.with_suffix(markdown_path.suffix + ".tmp")
            temporary.write_text(content + "\n", encoding="utf-8")
            temporary.replace(markdown_path)
            digest = _file_sha256(markdown_path)
            source_content.append(content)
            fragment_records.append({
                "markdown_relative_path": relative_path.as_posix(),
                "markdown_sha256": digest,
                "source_chunk_index": index,
                "source_metadata": {
                    field: metadata[field]
                    for field in (
                        "source_url", "source_title", "section", "page_number",
                        "ui_verified", "ui_snapshot_date", "source_origin_type",
                    )
                    if metadata.get(field) is not None
                },
            })

        record_key = f"web::{source}"
        web_records[record_key] = {
            "status": "success",
            "source": source,
            "source_path": record_key,
            "source_filename": source,
            "source_type": source_type,
            "source_url": source_url,
            "source_title": str(first_metadata.get("source_title", source))[:500],
            "section": str(first_metadata.get("section", "Sitio web"))[:200],
            "source_sha256": sanitizer.sha256_text("\n\n".join(source_content)),
            "prompt_sha256": "not_applicable_existing_public_web_snapshot",
            "transform_model": (
                "public_web_ui_map" if source_type == "public_web_ui"
                else "public_web_extractor"
            ),
            "markdown_parts": fragment_records,
            "fragment_count": len(fragment_records),
            "indexed_from_existing_snapshot": True,
        }

    LOGGER.info(
        "Se conservarán %d fragmentos web de %d fuentes como Markdown (%s).",
        sum(record["fragment_count"] for record in web_records.values()),
        len(web_records),
        web_root,
    )
    return web_records


def _iter_record_markdown_parts(record: dict[str, Any]) -> list[dict[str, Any]]:
    parts = record.get("markdown_parts")
    if isinstance(parts, list):
        if not parts:
            raise ValueError("El registro Markdown no contiene fragmentos.")
        return parts
    return [{
        "markdown_relative_path": record.get("markdown_relative_path"),
        "markdown_sha256": record.get("markdown_sha256"),
        "source_metadata": {},
    }]


def _build_markdown_index(
    database_path: Path,
    records: dict[str, dict[str, Any]],
    output_dir: Path,
    expected_sources: set[str],
    collection_metadata: dict[str, Any],
) -> int:
    from app.services.rag_service import get_embedding_model

    database_path.mkdir(parents=True, exist_ok=False)
    client, collection = _collection_and_client(database_path, create=True, metadata=collection_metadata)
    embedder = get_embedding_model()
    chunks_added = 0

    for key, record in sorted(records.items()):
        source_chunk_index = 0
        for part in _iter_record_markdown_parts(record):
            markdown_path = _safe_markdown_path(output_dir, part)
            if not markdown_path.is_file():
                raise RuntimeError(f"Falta el Markdown validado para {key}: {markdown_path}")
            markdown = markdown_path.read_text(encoding="utf-8")
            if _file_sha256(markdown_path) != part.get("markdown_sha256"):
                raise RuntimeError(f"El Markdown cambió después de su validación: {markdown_path}")
            metadata = {
                "source": record["source"],
                "source_filename": record["source_filename"],
                "source_path": key,
                "source_type": record.get("source_type", "sanitized_markdown"),
                "indexed_format": "markdown",
                "source_markdown": part["markdown_relative_path"],
                "source_sha256": record["source_sha256"],
                "prompt_sha256": record["prompt_sha256"],
                "transform_provider": record.get("transform_provider", "openai"),
                "transform_model": record.get("transform_model", "gpt-6-luna"),
            }
            for field in (
                "source_url", "source_title", "section", "page_number",
                "ui_verified", "ui_snapshot_date", "source_origin_type",
            ):
                value = (part.get("source_metadata") or {}).get(field, record.get(field))
                if value is not None:
                    metadata[field] = value
            chunks = split_markdown_for_rag(markdown, metadata)
            if not chunks:
                raise RuntimeError(f"El Markdown no produjo fragmentos indexables: {key}")

            for chunk in chunks:
                chunk.metadata["chunk_index"] = source_chunk_index
                source_chunk_index += 1

            for start in range(0, len(chunks), 48):
                batch = chunks[start:start + 48]
                texts = [chunk.page_content for chunk in batch]
                vectors = embedder.embed_documents([f"passage: {text}" for text in texts])
                ids = [
                    hashlib.sha256(
                        f"{key}:{chunk.metadata['chunk_index']}:{chunk.page_content}".encode("utf-8")
                    ).hexdigest()
                    for chunk in batch
                ]
                collection.upsert(
                    ids=ids,
                    documents=texts,
                    metadatas=[chunk.metadata for chunk in batch],
                    embeddings=vectors,
                )
            chunks_added += len(chunks)
        record["indexed_chunk_count"] = source_chunk_index
        LOGGER.info("Markdown indexado en staging: %s (%d chunks)", key, source_chunk_index)

    count = collection.count()
    rows = collection.get(include=["metadatas"], limit=count)
    actual_sources: set[str] = set()
    invalid_formats: list[str] = []
    for meta in rows.get("metadatas") or []:
        item = meta or {}
        actual_sources.add(str(item.get("source_path", "")))
        if item.get("indexed_format") != "markdown":
            invalid_formats.append(str(item.get("source", "<sin fuente>")))
    if actual_sources != expected_sources or invalid_formats:
        raise RuntimeError(
            "El índice temporal no pasó la verificación: "
            f"faltan={sorted(expected_sources - actual_sources)[:10]}, "
            f"sobran={sorted(actual_sources - expected_sources)[:10]}, "
            f"formatos_no_markdown={invalid_formats[:10]}"
        )

    client.close()
    del collection, client, embedder
    gc.collect()
    return count


def _assert_server_stopped(port: int) -> None:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.25):
            raise RuntimeError(
                f"Hay un servicio escuchando en 127.0.0.1:{port}. "
                "Detén UniMon antes de ejecutar la reconstrucción completa para liberar ChromaDB."
            )
    except OSError:
        return


def _create_verified_backup(active_path: Path, golden_path: Path) -> Path:
    backup_root = Path.home() / "Documents" / "Backups" / "UniMon"
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_dir = backup_root / f"pre_markdown_ingestion_{stamp}"
    backup_dir.mkdir()
    entries: list[dict[str, Any]] = []

    for name, source in (("rag_active_chroma_db", active_path), ("golden_cache", golden_path)):
        if not source.is_dir():
            entries.append({"name": name, "source": str(source), "status": "not_present"})
            continue
        before = _tree_manifest(source)
        destination = backup_dir / name
        import shutil
        shutil.copytree(source, destination)
        after = _tree_manifest(destination)
        if before != after:
            raise RuntimeError(f"La copia de respaldo no coincide (SHA-256): {name}")
        entries.append({
            "name": name,
            "source": str(source),
            "backup": str(destination),
            "file_count": len(after),
            "total_bytes": sum(row["bytes"] for row in after.values()),
            "files": after,
        })

    manifest = {
        "created_local": datetime.now().astimezone().isoformat(),
        "project_branch": os.getenv("GIT_BRANCH", ""),
        "verification": "SHA-256 por archivo; respaldo comparado con su origen",
        "golden_cache_modified": False,
        "databases": entries,
    }
    _write_json(backup_dir / "manifest.json", manifest)
    LOGGER.info("Respaldo verificado antes de promover Markdown: %s", backup_dir)
    return backup_dir


def _promote_candidate(candidate: Path, active_path: Path, backup_dir: Path) -> None:
    previous = active_path.with_name(f".{active_path.name}.previous_markdown_{datetime.now():%Y%m%d_%H%M%S}")
    if previous.exists():
        raise FileExistsError(f"La ruta de rollback ya existe; se cancela la promoción: {previous}")
    moved_previous = False
    if active_path.exists():
        try:
            os.replace(active_path, previous)
        except PermissionError as exc:
            raise RuntimeError(
                "Windows no permitió mover la base Chroma activa. El índice activo sigue intacto; "
                f"se conservaron el candidato {candidate} y el respaldo {backup_dir}. "
                "Cierra UniMon y cualquier otro proceso que tenga abierta esa base, y vuelve a ejecutar --rebuild."
            ) from exc
        moved_previous = True
    try:
        os.replace(candidate, active_path)
    except Exception:
        if moved_previous and previous.exists() and not active_path.exists():
            os.replace(previous, active_path)
        raise

    if moved_previous:
        LOGGER.info("El índice anterior quedó conservado en %s; respaldo verificado: %s", previous, backup_dir)


def _existing_index_state(path: Path) -> tuple[set[str], list[str]]:
    try:
        client, collection = _collection_and_client(path, create=False)
    except Exception:
        return set(), []
    count = collection.count()
    rows = collection.get(include=["metadatas"], limit=count) if count else {"metadatas": []}
    sources: set[str] = set()
    raw_sources: list[str] = []
    for meta in rows.get("metadatas") or []:
        item = meta or {}
        source = str(item.get("source", ""))
        if source:
            sources.add(source)
        if item.get("indexed_format") != "markdown":
            raw_sources.append(source or "<chunk sin fuente>")
    client.close()
    del collection, client
    return sources, sorted(set(raw_sources))


def _delete_indexed_source(collection, source: str) -> int:
    old = collection.get(where={"source": source}, include=["metadatas"])
    ids = old.get("ids") or []
    if ids:
        collection.delete(ids=ids)
    return len(ids)


def _index_incremental(
    active_path: Path,
    output_dir: Path,
    records: dict[str, dict[str, Any]],
) -> int:
    from app.services.rag_service import get_embedding_model

    client, collection = _collection_and_client(active_path, create=True, metadata={"hnsw:space": "l2"})
    embedder = get_embedding_model()
    indexed = 0
    for key, record in sorted(records.items()):
        current = collection.get(where={"source": record["source"]}, include=["metadatas"])
        current_metas = current.get("metadatas") or []
        if current_metas and all(
            meta and meta.get("source_type") == "sanitized_markdown"
            and meta.get("source_sha256") == record["source_sha256"]
            for meta in current_metas
        ):
            record["indexed_sha256"] = record["source_sha256"]
            record["indexed_chunk_count"] = len(current_metas)
            continue

        markdown_path = _safe_markdown_path(output_dir, record)
        if _file_sha256(markdown_path) != record.get("markdown_sha256"):
            raise RuntimeError(f"El Markdown cambió desde su validación: {markdown_path}")
        metadata = {
            "source": record["source"],
            "source_filename": record["source_filename"],
            "source_path": key,
            "source_type": record.get("source_type", "sanitized_markdown"),
            "indexed_format": "markdown",
            "source_markdown": record["markdown_relative_path"],
            "source_sha256": record["source_sha256"],
            "prompt_sha256": record["prompt_sha256"],
            "transform_provider": record.get("transform_provider", "openai"),
            "transform_model": record.get("transform_model", "gpt-6-luna"),
        }
        chunks = split_markdown_for_rag(markdown_path.read_text(encoding="utf-8"), metadata)
        if not chunks:
            raise RuntimeError(f"El Markdown no produjo fragmentos indexables: {key}")
        all_ids: list[str] = []
        for start in range(0, len(chunks), 48):
            batch = chunks[start:start + 48]
            texts = [chunk.page_content for chunk in batch]
            vectors = embedder.embed_documents([f"passage: {text}" for text in texts])
            ids = [
                hashlib.sha256(
                    f"{key}:{chunk.metadata['chunk_index']}:{chunk.page_content}".encode("utf-8")
                ).hexdigest()
                for chunk in batch
            ]
            collection.upsert(
                ids=ids,
                documents=texts,
                metadatas=[chunk.metadata for chunk in batch],
                embeddings=vectors,
            )
            all_ids.extend(ids)
        old_ids = current.get("ids") or []
        new_id_set = set(all_ids)
        obsolete_ids = [item for item in old_ids if item not in new_id_set]
        if obsolete_ids:
            collection.delete(ids=obsolete_ids)
        record["indexed_sha256"] = record["source_sha256"]
        record["indexed_chunk_count"] = len(chunks)
        record["indexed_at_utc"] = datetime.now(timezone.utc).isoformat()
        indexed += len(chunks)
        LOGGER.info("Markdown indexado: %s (%d chunks)", key, len(chunks))
    client.close()
    del collection, client, embedder
    return indexed


def ingest_sanitized_documents(
    docs_path: str | None = None,
    chroma_path: str | None = None,
    sanitized_docs_path: str | None = None,
    file_path: str | None = None,
    incremental: bool = True,
    delete_doc: str | None = None,
    wipe_db: bool = False,
    force: bool = False,
    use_vision: bool = True,
    workers: int = 2,
    vision_model_override: str | None = None,
    min_image_kb_override: int | None = None,
    pre_index_validator: Callable[[Path, Path, str, dict[str, Any]], dict[str, Any] | None] | None = None,
) -> bool:
    """Scan PDF/PPTX/DOCX files, transform changed sources, and index validated Markdown."""
    del incremental  # Every run is hash-based and idempotent; rebuild is explicit via wipe_db.
    settings = get_settings()
    docs_dir = Path(docs_path or settings.docs_dir).resolve()
    active_path = Path(chroma_path or settings.chroma_db_dir).resolve()
    output_dir = Path(sanitized_docs_path or settings.sanitized_docs_dir).resolve()
    golden_path = Path(settings.golden_cache_db_dir).resolve()
    for protected_path in (docs_dir, output_dir, golden_path):
        if _paths_overlap(active_path, protected_path):
            raise ValueError(
                f"La ruta Chroma activa {active_path} se cruza con una ruta protegida: {protected_path}"
            )
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"

    try:
        if wipe_db:
            _assert_server_stopped(int(settings.port))

        if delete_doc:
            client, collection = _collection_and_client(active_path, create=False)
            rows = collection.get(include=["metadatas"], limit=collection.count())
            matches = {
                str((meta or {}).get("source", ""))
                for meta in rows.get("metadatas") or []
                if str((meta or {}).get("source_filename", "")) == Path(delete_doc).name
                or str((meta or {}).get("source", "")) == Path(delete_doc).name
            }
            deleted = sum(_delete_indexed_source(collection, source) for source in matches)
            manifest = _load_manifest(manifest_path)
            for key, record in list(manifest["records"].items()):
                if record.get("source_filename") == Path(delete_doc).name or key == delete_doc:
                    try:
                        markdown = _safe_markdown_path(output_dir, record)
                    except ValueError:
                        markdown = None
                    if markdown and markdown.is_file():
                        markdown.unlink()
                    manifest["records"].pop(key, None)
            _write_json(manifest_path, manifest)
            LOGGER.info("Eliminados %d chunks Markdown de %s", deleted, delete_doc)
            client.close()
            del collection, client
            return True

        sources = _discover_sources(docs_dir, file_path)
        if not sources:
            LOGGER.info("No hay documentos PDF/PPTX/DOCX pendientes en %s", docs_dir)
            return True

        if vision_model_override:
            settings.vision_model = vision_model_override
        if min_image_kb_override is not None:
            settings.vision_min_image_kb = min_image_kb_override

        records, failures = _prepare_markdown(
            paths=sources,
            docs_dir=docs_dir,
            output_dir=output_dir,
            force=force,
            use_vision=use_vision,
            workers=workers,
        )
        if pre_index_validator and records:
            approved_records: dict[str, dict[str, Any]] = {}
            manifest = _load_manifest(manifest_path)
            for key, record in records.items():
                existing_audit = record.get("fidelity_audit") or {}
                if (
                    existing_audit.get("status") == "coincide"
                    and existing_audit.get("source_sha256") == record.get("source_sha256")
                    and existing_audit.get("markdown_sha256") == record.get("markdown_sha256")
                ):
                    approved_records[key] = record
                    continue
                try:
                    audit = pre_index_validator(docs_dir, output_dir, key, record)
                    if audit:
                        if audit.get("status") != "coincide":
                            raise RuntimeError(str(audit.get("summary") or "El Markdown requiere revisión de fidelidad."))
                        audit.update({
                            "source_sha256": record.get("source_sha256"),
                            "markdown_sha256": record.get("markdown_sha256"),
                        })
                        record["fidelity_audit"] = audit
                    approved_records[key] = record
                    manifest["records"][key] = record
                except Exception as exc:
                    failures.append(key)
                    record["fidelity_audit"] = {
                        "status": "revisar",
                        "summary": str(exc)[:1000],
                        "source_sha256": record.get("source_sha256"),
                        "markdown_sha256": record.get("markdown_sha256"),
                    }
                    manifest["records"][key] = record
                    LOGGER.error("No se indexó %s: falló la validación de fidelidad (%s)", key, type(exc).__name__)
            records = approved_records
            _write_json(manifest_path, manifest)
        if failures:
            LOGGER.error("No se indexaron documentos con Markdown fallido: %s", failures)
            if wipe_db:
                return False

        if wipe_db:
            if len(records) != len(sources) or failures:
                LOGGER.error("Rebuild cancelado: no hay Markdown válido para cada documento fuente.")
                return False
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            candidate_path = active_path.parent / "scratch" / f"markdown_chroma_candidate_{stamp}"
            web_records = _preserve_public_web_markdown(active_path, output_dir)
            indexed_records = {**records, **web_records}
            expected_sources = set(indexed_records)
            manifest = _load_manifest(manifest_path)
            manifest["records"].update(web_records)
            manifest["public_web_sources_seen"] = len(web_records)
            manifest["public_web_fragments_preserved"] = sum(
                record["fragment_count"] for record in web_records.values()
            )
            _write_json(manifest_path, manifest)
            metric_metadata = _active_collection_metadata(active_path)
            chunks = _build_markdown_index(
                candidate_path,
                indexed_records,
                output_dir,
                expected_sources,
                metric_metadata,
            )
            del candidate_path
            gc.collect()

            backup_dir = _create_verified_backup(
                active_path,
                golden_path,
            )
            stage = active_path.parent / "scratch" / f"markdown_chroma_candidate_{stamp}"
            _promote_candidate(stage, active_path, backup_dir)
            manifest = _load_manifest(manifest_path)
            for key, record in indexed_records.items():
                record["indexed_sha256"] = record["source_sha256"]
                record["indexed_at_utc"] = datetime.now(timezone.utc).isoformat()
                manifest["records"][key] = record
            manifest["last_indexed_sources"] = sorted(indexed_records)
            manifest["active_chroma_path"] = str(active_path)
            manifest["active_chunks"] = chunks
            manifest["local_documents_indexed"] = len(records)
            manifest["public_web_sources_indexed"] = len(web_records)
            manifest["public_web_fragments_preserved"] = sum(
                record["fragment_count"] for record in web_records.values()
            )
            manifest["promoted_at_utc"] = datetime.now(timezone.utc).isoformat()
            manifest["backup_manifest"] = str(backup_dir / "manifest.json")
            manifest["golden_cache_modified"] = False
            _write_json(manifest_path, manifest)
            LOGGER.info(
                "Reconstrucción Markdown terminada: %d documentos, %d chunks. Golden Cache preservado.",
                len(indexed_records), chunks,
            )
            return True

        indexed_sources, raw_sources = _existing_index_state(active_path)
        if raw_sources:
            LOGGER.error(
                "El RAG activo aún contiene documentos sin sanear (%d). No se mezclarán con Markdown. "
                "Detén UniMon y ejecuta el script con --rebuild.",
                len(raw_sources),
            )
            return False

        # Index only documents that are missing or whose raw source hash changed.
        pending_records = {
            key: record for key, record in records.items()
            if record.get("source") not in indexed_sources
            or record.get("indexed_sha256") != record.get("source_sha256")
        }
        if not pending_records:
            LOGGER.info("No hay documentos nuevos o modificados; todos los Markdown están indexados.")
            return not failures
        indexed_chunks = _index_incremental(active_path, output_dir, pending_records)
        manifest = _load_manifest(manifest_path)
        for key, record in pending_records.items():
            manifest["records"][key] = record
        manifest["last_indexed_sources"] = sorted(set(manifest.get("last_indexed_sources", [])) | set(pending_records))
        manifest["incremental_chunks_added"] = indexed_chunks
        manifest["last_incremental_index_utc"] = datetime.now(timezone.utc).isoformat()
        _write_json(manifest_path, manifest)
        return not failures
    except Exception:
        LOGGER.exception("Falló la ingesta de documentos Markdown.")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--rebuild", action="store_true", help="Reconstruye desde cero en staging y promueve solo tras validar. Requiere detener UniMon.")
    mode.add_argument("--file", help="Procesa e indexa un PDF/PPTX individual desde data/docs.")
    parser.add_argument("--docs-dir", type=Path, help="Directorio de documentos fuente; por defecto, DOCS_DIR.")
    parser.add_argument("--chroma-dir", type=Path, help="Base RAG activa; por defecto, CHROMA_DB_DIR.")
    parser.add_argument("--force", action="store_true", help="Vuelve a transformar con GPT-6 Luna aunque el Markdown vigente pase la validación.")
    parser.add_argument("--no-vision", action="store_true", help="No interpreta imágenes mediante el modelo visual local.")
    parser.add_argument("--workers", type=int, default=2, help="Transformaciones LLM concurrentes, entre 1 y 4 (por defecto: 2).")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    ok = ingest_sanitized_documents(
        docs_path=str(args.docs_dir) if args.docs_dir else None,
        chroma_path=str(args.chroma_dir) if args.chroma_dir else None,
        file_path=args.file,
        wipe_db=args.rebuild,
        force=args.force,
        use_vision=not args.no_vision,
        workers=args.workers,
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
