"""
Restore database backups from Cloudflare R2 (S3) or local storage.

Behavior:
 - --list : list backups
 - --latest : restore most recent backup
 - --file <name> : restore specific backup
 - Uses presigned URL + requests to avoid botocore checksum/content-length issues with R2
 - Detects gzip by magic bytes and only extracts when actually gzipped
 - If file is plain SQL (starts with b'--' etc.) it will be fed to psql directly
"""

import gzip
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

import boto3
from botocore.config import Config
import requests

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)

# Optional django-storages imports
try:
    from django.core.files.storage import storages
    from storages.backends.s3boto3 import S3Boto3Storage
except Exception:
    storages = {}
    S3Boto3Storage = None  # type: ignore


# -----------------------
# Helpers
# -----------------------
def _get_storage_backend() -> Tuple[str, object]:
    try:
        st = storages["dbbackup"]
        return "django_storage", st
    except Exception:
        pass

    cfg = getattr(settings, "STORAGES", {}).get("dbbackup")
    if not cfg:
        raise RuntimeError("No 'dbbackup' storage configured (storages[...] or settings.STORAGES['dbbackup']).")

    backend_path = cfg.get("BACKEND", "")
    opts = cfg.get("OPTIONS", {}) or {}

    access_key = opts.get("access_key") or os.getenv("BACKUP_R2_ACCESS_KEY_ID")
    secret_key = opts.get("secret_key") or os.getenv("BACKUP_R2_SECRET_ACCESS_KEY")
    bucket_name = opts.get("bucket_name") or os.getenv("BACKUP_R2_BUCKET_NAME")
    endpoint_url = opts.get("endpoint_url") or opts.get("endpoint") or os.getenv("BACKUP_R2_ENDPOINT")
    region_name = opts.get("region_name") or os.getenv("BACKUP_R2_REGION")
    prefix = opts.get("location") or opts.get("prefix") or ""

    if "s3boto3" in backend_path.lower() or "s3" in backend_path.lower():
        return "s3_dict", {
            "access_key": access_key,
            "secret_key": secret_key,
            "bucket_name": bucket_name,
            "endpoint_url": endpoint_url,
            "region_name": region_name,
            "prefix": prefix,
        }

    location = opts.get("location") or os.getenv("DBBACKUP_LOCAL_DIR") or str(Path(settings.BASE_DIR) / "backups")
    return "local_dict", {"location": location}


def _build_s3_client(cfg: dict):
    botocore_cfg = Config(
        signature_version="s3v4",
        s3={
            "addressing_style": "path",
            "checksum_validation": False,
        }
    )
    client_args = {
        "aws_access_key_id": cfg.get("access_key"),
        "aws_secret_access_key": cfg.get("secret_key"),
        "config": botocore_cfg,
    }
    if cfg.get("region_name"):
        client_args["region_name"] = cfg.get("region_name")
    if cfg.get("endpoint_url"):
        client_args["endpoint_url"] = cfg.get("endpoint_url")
    return boto3.client("s3", **client_args)


def _normalize_key(prefix: str, filename: str) -> str:
    prefix = (prefix or "").strip()
    if not prefix:
        return filename
    return f"{prefix.rstrip('/')}/{filename}"


def _is_gzip_file(path: Path) -> bool:
    """Return True if file at path starts with gzip magic bytes."""
    try:
        with open(path, "rb") as f:
            magic = f.read(2)
        return magic == b"\x1f\x8b"
    except Exception:
        return False


# -----------------------
# Command
# -----------------------
class Command(BaseCommand):
    help = "Restore database from Cloudflare R2 (S3) or local storage"

    def add_arguments(self, parser):
        parser.add_argument("--list", action="store_true", help="List available backups")
        parser.add_argument("--latest", action="store_true", help="Restore most recent backup")
        parser.add_argument("--file", type=str, help="Restore a specific backup file")

    def handle(self, *args, **options):
        try:
            backend_type, backend = _get_storage_backend()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Storage config error: {exc}"))
            logger.exception("Storage config error")
            return

        if options.get("list"):
            return self._list_backups(backend_type, backend)
        if options.get("latest"):
            return self._restore_latest(backend_type, backend)

        filename = options.get("file")
        if not filename:
            self.stdout.write(self.style.WARNING("Please specify --list, --latest, or --file FILENAME"))
            return

        return self._restore_specific(backend_type, backend, filename)

    # ------------------------
    # list
    # ------------------------
    def _list_backups(self, backend_type: str, backend):
        self.stdout.write(self.style.WARNING("Fetching backup list..."))
        try:
            ext = (".psql", ".psql.gz", ".sql", ".sql.gz", ".dump", ".dump.gz")
            if backend_type == "django_storage":
                storage = backend
                _, files = storage.listdir("")
                backups = [f for f in files if f.endswith(ext)]
                if not backups:
                    self.stdout.write(self.style.WARNING("No backup files found"))
                    return
                for idx, fn in enumerate(sorted(backups, reverse=True), 1):
                    try:
                        size = storage.size(fn) or 0
                    except Exception:
                        size = 0
                    try:
                        mod = storage.get_modified_time(fn)
                        modified_str = mod.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        modified_str = "unknown"
                    self.stdout.write(
                        f"{idx}. {fn}\n   Size: {(size / (1024 * 1024)):.2f} MB\n   Modified: {modified_str}\n")
                return

            if backend_type == "s3_dict":
                cfg = backend
                client = _build_s3_client(cfg)
                paginator = client.get_paginator("list_objects_v2")
                page_iter = paginator.paginate(Bucket=cfg["bucket_name"], Prefix=cfg.get("prefix") or "")
                found = []
                for page in page_iter:
                    for obj in page.get("Contents", []):
                        name = obj["Key"].split("/")[-1]
                        if name.endswith(ext):
                            found.append((name, obj.get("Size"), obj.get("LastModified")))
                if not found:
                    self.stdout.write(self.style.WARNING("No backup files found in remote bucket"))
                    return
                for idx, (name, size, modified) in enumerate(sorted(found, key=lambda x: x[0], reverse=True), 1):
                    size_mb = (size or 0) / (1024 * 1024)
                    mod_str = modified.strftime("%Y-%m-%d %H:%M:%S") if modified else "unknown"
                    self.stdout.write(f"{idx}. {name}\n   Size: {size_mb:.2f} MB\n   Modified: {mod_str}\n")
                return

            if backend_type == "local_dict":
                loc = backend.get("location")
                p = Path(loc)
                if not p.exists():
                    self.stdout.write(self.style.WARNING(f"No local backup directory: {loc}"))
                    return
                matches = sorted([f for f in p.iterdir() if f.is_file() and f.name.endswith(ext)], reverse=True)
                if not matches:
                    self.stdout.write(self.style.WARNING("No local backups found"))
                    return
                for idx, fp in enumerate(matches, 1):
                    size_mb = fp.stat().st_size / (1024 * 1024)
                    self.stdout.write(f"{idx}. {fp.name}\n   Size: {size_mb:.2f} MB\n   Path: {str(fp)}\n")
                return

            self.stdout.write(self.style.ERROR("Unsupported backend for listing"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"List failed: {e}"))
            logger.exception("List backups error")

    # ------------------------
    # latest
    # ------------------------
    def _restore_latest(self, backend_type: str, backend):
        self.stdout.write(self.style.WARNING("Finding latest backup..."))
        try:
            names = []
            ext_tuple = (".psql", ".psql.gz", ".sql", ".sql.gz", ".dump", ".dump.gz")
            if backend_type == "django_storage":
                storage = backend
                _, files = storage.listdir("")
                names = [f for f in files if f.endswith(ext_tuple)]
            elif backend_type == "s3_dict":
                cfg = backend
                client = _build_s3_client(cfg)
                resp = client.list_objects_v2(Bucket=cfg["bucket_name"], Prefix=cfg.get("prefix") or "")
                names = [obj["Key"].split("/")[-1] for obj in resp.get("Contents", [])]
                names = [n for n in names if n.endswith(ext_tuple)]
            else:
                loc = backend.get("location")
                p = Path(loc)
                names = [f.name for f in p.iterdir() if f.is_file() and f.name.endswith(ext_tuple)]

            if not names:
                self.stdout.write(self.style.ERROR("No backup files found"))
                return

            latest = sorted(names, reverse=True)[0]
            self.stdout.write(self.style.SUCCESS(f"Latest backup: {latest}"))
            confirm = input("\nThis will OVERWRITE your current database. Type 'yes' to continue: ")
            if confirm.lower() != "yes":
                self.stdout.write(self.style.WARNING("Restore cancelled"))
                return
            self._restore_specific(backend_type, backend, latest)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Failed to determine latest backup: {e}"))
            logger.exception("Restore latest error")

    # ------------------------
    # specific
    # ------------------------
    def _restore_specific(self, backend_type: str, backend, filename: str):
        self.stdout.write(self.style.WARNING(f"Restoring backup: {filename}"))
        tmpdir = Path(tempfile.mkdtemp(prefix="dbrestore_"))
        local_path = tmpdir / filename

        try:
            # DOWNLOAD / COPY
            if backend_type == "django_storage":
                storage = backend
                if S3Boto3Storage is not None and isinstance(storage, S3Boto3Storage):
                    cfg = getattr(settings, "STORAGES", {}).get("dbbackup", {}) or {}
                    opts = cfg.get("OPTIONS", {}) or {}
                    s3_cfg = {
                        "access_key": opts.get("access_key") or os.getenv("BACKUP_R2_ACCESS_KEY_ID"),
                        "secret_key": opts.get("secret_key") or os.getenv("BACKUP_R2_SECRET_ACCESS_KEY"),
                        "bucket_name": opts.get("bucket_name") or os.getenv("BACKUP_R2_BUCKET_NAME"),
                        "endpoint_url": opts.get("endpoint_url") or opts.get("endpoint") or os.getenv(
                            "BACKUP_R2_ENDPOINT"),
                        "prefix": opts.get("location") or "",
                    }
                    client = _build_s3_client(s3_cfg)
                    key = _normalize_key(s3_cfg.get("prefix") or getattr(storage, "location", "") or "", filename)

                    # Try presigned URL download first (bypasses botocore checksum validation)
                    try:
                        presigned = client.generate_presigned_url(
                            "get_object",
                            Params={"Bucket": s3_cfg["bucket_name"], "Key": key},
                            ExpiresIn=3600,
                        )
                        with requests.get(presigned, stream=True, timeout=300) as r:
                            r.raise_for_status()
                            with open(local_path, "wb") as out:
                                for chunk in r.iter_content(chunk_size=8192):
                                    if chunk:
                                        out.write(chunk)
                    except requests.exceptions.HTTPError as presigned_http_err:
                        raise RuntimeError(
                            f"Presigned URL download failed ({presigned_http_err}). "
                            f"Check BACKUP_R2_ACCESS_KEY_ID / BACKUP_R2_SECRET_ACCESS_KEY and BACKUP_R2_ENDPOINT."
                        )
                    except Exception as presigned_exc:
                        # Fallback to direct get_object (may raise checksum error)
                        try:
                            resp = client.get_object(Bucket=s3_cfg["bucket_name"], Key=key)
                            body = resp["Body"].read()
                            local_path.write_bytes(body)
                        except Exception as e:
                            raise RuntimeError(f"S3 download failed: {presigned_exc} / {e}")

                else:
                    # Generic django storage
                    try:
                        with storage.open(filename, "rb") as remote, open(local_path, "wb") as out:
                            shutil.copyfileobj(remote, out)
                    except Exception:
                        loc = getattr(storage, "location", "") or ""
                        alt_key = filename
                        if loc and not filename.startswith(loc):
                            alt_key = f"{loc.rstrip('/')}/{filename}"
                        try:
                            with storage.open(alt_key, "rb") as remote, open(local_path, "wb") as out:
                                shutil.copyfileobj(remote, out)
                        except Exception as e2:
                            raise RuntimeError(f"Failed to download via django storage: {e2}")

            elif backend_type == "s3_dict":
                cfg = backend
                client = _build_s3_client(cfg)
                key = _normalize_key(cfg.get("prefix") or "", filename)
                try:
                    presigned = client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": cfg["bucket_name"], "Key": key},
                        ExpiresIn=3600,
                    )
                    with requests.get(presigned, stream=True, timeout=300) as r:
                        r.raise_for_status()
                        with open(local_path, "wb") as out:
                            for chunk in r.iter_content(chunk_size=8192):
                                if chunk:
                                    out.write(chunk)
                except requests.exceptions.HTTPError as presigned_http_err:
                    raise RuntimeError(
                        f"Presigned URL download failed ({presigned_http_err}). Check R2 credentials and endpoint."
                    )
                except Exception as presigned_exc:
                    try:
                        resp = client.get_object(Bucket=cfg["bucket_name"], Key=key)
                        body = resp["Body"].read()
                        local_path.write_bytes(body)
                    except Exception as e:
                        raise RuntimeError(f"S3 download failed: {presigned_exc} / {e}")

            elif backend_type == "local_dict":
                src = Path(backend.get("location") or settings.BASE_DIR) / filename
                if not src.exists():
                    self.stderr.write(self.style.ERROR(f"Local backup file not found: {src}"))
                    return
                shutil.copy(src, local_path)

            else:
                raise RuntimeError("Unsupported backend type for restore")

            # DETECT gzip by magic bytes; only extract if gz
            if _is_gzip_file(local_path):
                self.stdout.write("Detected gzip archive — extracting...")
                extracted = tmpdir / filename.replace(".gz", "")
                with gzip.open(local_path, "rb") as f_in, open(extracted, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                try:
                    local_path.unlink()
                except Exception:
                    pass
                db_file = extracted
            else:
                # Not gzipped — treat as plain SQL or pg custom dump that psql can handle
                self.stdout.write("File is not gzipped — proceeding to restore directly (plain SQL assumed).")
                db_file = local_path

            # RESTORE via psql
            self.stdout.write(self.style.WARNING("Starting database restore..."))
            db = settings.DATABASES["default"]
            cmd = [
                "psql",
                "-h", db.get("HOST", "localhost"),
                "-p", str(db.get("PORT", 5432)),
                "-U", db.get("USER"),
                "-d", db.get("NAME"),
                "-f", str(db_file),
            ]
            env = os.environ.copy()
            env["PGPASSWORD"] = db.get("PASSWORD", "") or env.get("PGPASSWORD", "")

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode != 0:
                self.stderr.write(self.style.ERROR(f"✗ Restore failed:\n{result.stderr}"))
                logger.error("psql failed: %s", result.stderr)
            else:
                self.stdout.write(self.style.SUCCESS("✓ Database restored successfully"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Restore failed: {e}"))
            logger.exception("Restore specific failed")
        finally:
            # cleanup
            try:
                for p in tmpdir.iterdir():
                    try:
                        p.unlink()
                    except Exception:
                        pass
                tmpdir.rmdir()
            except Exception:
                pass
