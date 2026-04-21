import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path


class BackupError(Exception):
    pass


def create_sqlite_backup(source_path: str | Path, backup_dir: str | Path, label: str = "default") -> Path:
    source_value = str(source_path)
    if source_value == ":memory:" or source_value.startswith("file:"):
        raise BackupError("Cannot back up an in-memory SQLite database.")

    source = Path(source_path)
    if not source.exists():
        raise BackupError(f"SQLite database file does not exist: {source}")

    destination_dir = Path(backup_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    backup_path = destination_dir / f"ludarius-{label}-{timestamp}.sqlite3"

    source_connection = None
    backup_connection = None
    try:
        source_connection = sqlite3.connect(source)
        backup_connection = sqlite3.connect(backup_path)
        source_connection.backup(backup_connection)
    except sqlite3.Error as exc:
        backup_path.unlink(missing_ok=True)
        raise BackupError(f"Could not create SQLite backup: {exc}") from exc
    finally:
        if backup_connection is not None:
            backup_connection.close()
        if source_connection is not None:
            source_connection.close()

    _write_metadata(
        backup_path=backup_path,
        engine="sqlite",
        source=str(source),
        backup_format="sqlite3-copy",
    )
    return backup_path


def restore_sqlite_backup(backup_path: str | Path, target_path: str | Path) -> Path:
    target_value = str(target_path)
    if target_value == ":memory:" or target_value.startswith("file:"):
        raise BackupError("Cannot restore an in-memory SQLite database.")

    backup = Path(backup_path)
    target = Path(target_path)
    if not backup.exists():
        raise BackupError(f"Backup file does not exist: {backup}")

    verify_backup_checksum(backup)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, target)
    return target


def create_postgres_backup(db_settings: dict, backup_dir: str | Path, label: str = "default") -> Path:
    destination_dir = Path(backup_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    backup_path = destination_dir / f"ludarius-{label}-{timestamp}.dump"

    command = _pg_dump_command(db_settings, backup_path)
    _run_postgres_command(command, db_settings)
    _write_metadata(
        backup_path=backup_path,
        engine="postgresql",
        source=_postgres_source(db_settings),
        backup_format="pg_dump-custom",
    )
    return backup_path


def restore_postgres_backup(db_settings: dict, backup_path: str | Path):
    backup = Path(backup_path)
    if not backup.exists():
        raise BackupError(f"Backup file does not exist: {backup}")
    verify_backup_checksum(backup)
    command = _pg_restore_command(db_settings, backup)
    _run_postgres_command(command, db_settings)


def prune_backups(backup_dir: str | Path, keep_last: int):
    if keep_last <= 0:
        return []

    directory = Path(backup_dir)
    if not directory.exists():
        return []

    backup_files = sorted(
        [
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix in {".sqlite3", ".dump"}
        ],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    removed = []
    for old_backup in backup_files[keep_last:]:
        metadata = old_backup.with_suffix(old_backup.suffix + ".json")
        old_backup.unlink(missing_ok=True)
        metadata.unlink(missing_ok=True)
        removed.append(old_backup)
    return removed


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_backup_checksum(backup_path: str | Path) -> bool:
    backup = Path(backup_path)
    metadata_path = backup.with_suffix(backup.suffix + ".json")
    if not metadata_path.exists():
        return False

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BackupError(f"Backup metadata is invalid: {metadata_path}") from exc

    expected_hash = metadata.get("sha256")
    if not expected_hash:
        raise BackupError(f"Backup metadata does not include sha256: {metadata_path}")

    actual_hash = sha256_file(backup)
    if actual_hash != expected_hash:
        raise BackupError("Backup checksum does not match metadata.")
    return True


def _write_metadata(backup_path: Path, engine: str, source: str, backup_format: str):
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "engine": engine,
        "source": source,
        "format": backup_format,
        "backup_file": backup_path.name,
        "sha256": sha256_file(backup_path),
    }
    metadata_path = backup_path.with_suffix(backup_path.suffix + ".json")
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")


def _pg_dump_command(db_settings: dict, backup_path: Path) -> list[str]:
    command = [
        "pg_dump",
        "--format=custom",
        "--no-owner",
        "--no-acl",
        "--file",
        str(backup_path),
    ]
    command.extend(_postgres_connection_args(db_settings))
    return command


def _pg_restore_command(db_settings: dict, backup_path: Path) -> list[str]:
    command = [
        "pg_restore",
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-acl",
        "--dbname",
        db_settings["NAME"],
        str(backup_path),
    ]
    command.extend(_postgres_connection_args(db_settings, include_db_name=False))
    return command


def _postgres_connection_args(db_settings: dict, include_db_name: bool = True) -> list[str]:
    args = []
    if db_settings.get("HOST"):
        args.extend(["--host", str(db_settings["HOST"])])
    if db_settings.get("PORT"):
        args.extend(["--port", str(db_settings["PORT"])])
    if db_settings.get("USER"):
        args.extend(["--username", str(db_settings["USER"])])
    if include_db_name:
        args.append(str(db_settings["NAME"]))
    return args


def _run_postgres_command(command: list[str], db_settings: dict):
    env = os.environ.copy()
    if db_settings.get("PASSWORD"):
        env["PGPASSWORD"] = str(db_settings["PASSWORD"])
    try:
        subprocess.run(command, check=True, env=env, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise BackupError("PostgreSQL backup tools are not installed or not in PATH.") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise BackupError(detail or "PostgreSQL backup command failed.") from exc


def _postgres_source(db_settings: dict) -> str:
    user = db_settings.get("USER") or ""
    host = db_settings.get("HOST") or "localhost"
    port = db_settings.get("PORT") or "5432"
    name = db_settings.get("NAME") or ""
    user_part = f"{user}@" if user else ""
    return f"postgresql://{user_part}{host}:{port}/{name}"
