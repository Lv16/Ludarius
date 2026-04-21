import json
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase
from django.test import TestCase
from django.urls import reverse

from core.backups import (
    BackupError,
    create_sqlite_backup,
    prune_backups,
    restore_sqlite_backup,
    sha256_file,
    verify_backup_checksum,
)


class HealthCheckTests(TestCase):
    def test_health_check_returns_ok(self):
        response = self.client.get(reverse("health_check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertTrue(response.json()["checks"]["database"])
        self.assertTrue(response.json()["checks"]["cache"])

    def test_request_id_header_is_added(self):
        response = self.client.get(reverse("health_check"))

        self.assertTrue(response.headers["X-Request-ID"])

    def test_request_id_header_can_be_provided_by_client(self):
        response = self.client.get(reverse("health_check"), headers={"X-Request-ID": "test-request-id"})

        self.assertEqual(response.headers["X-Request-ID"], "test-request-id")


class DatabaseBackupTests(SimpleTestCase):
    def test_sqlite_backup_and_restore_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "db.sqlite3"
            backup_dir = temp_path / "backups"

            with closing(sqlite3.connect(source)) as connection:
                connection.execute("CREATE TABLE notes (value TEXT NOT NULL)")
                connection.execute("INSERT INTO notes (value) VALUES (?)", ("before",))
                connection.commit()

            backup_path = create_sqlite_backup(source, backup_dir, label="test")
            metadata_path = backup_path.with_suffix(backup_path.suffix + ".json")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

            self.assertEqual(metadata["engine"], "sqlite")
            self.assertEqual(metadata["sha256"], sha256_file(backup_path))
            self.assertTrue(verify_backup_checksum(backup_path))

            with closing(sqlite3.connect(source)) as connection:
                connection.execute("DELETE FROM notes")
                connection.execute("INSERT INTO notes (value) VALUES (?)", ("after",))
                connection.commit()

            restored_path = restore_sqlite_backup(backup_path, source)

            self.assertEqual(restored_path, source)
            with closing(sqlite3.connect(source)) as connection:
                value = connection.execute("SELECT value FROM notes").fetchone()[0]
            self.assertEqual(value, "before")

    def test_sqlite_restore_rejects_tampered_backup(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "db.sqlite3"
            backup_dir = temp_path / "backups"

            with closing(sqlite3.connect(source)) as connection:
                connection.execute("CREATE TABLE notes (value TEXT NOT NULL)")
                connection.commit()

            backup_path = create_sqlite_backup(source, backup_dir, label="test")
            backup_path.write_bytes(backup_path.read_bytes() + b"tampered")

            with self.assertRaisesMessage(BackupError, "checksum"):
                restore_sqlite_backup(backup_path, source)

    def test_prune_backups_keeps_newest_files_and_metadata(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir)
            backups = []
            for index in range(3):
                backup_path = backup_dir / f"backup-{index}.sqlite3"
                backup_path.write_text(str(index), encoding="utf-8")
                backup_path.with_suffix(backup_path.suffix + ".json").write_text("{}", encoding="utf-8")
                os.utime(backup_path, (index, index))
                backups.append(backup_path)

            removed = prune_backups(backup_dir, keep_last=2)

            self.assertEqual(removed, [backups[0]])
            self.assertFalse(backups[0].exists())
            self.assertFalse(backups[0].with_suffix(backups[0].suffix + ".json").exists())
            self.assertTrue(backups[1].exists())
            self.assertTrue(backups[2].exists())

    def test_restore_command_requires_explicit_confirmation(self):
        with self.assertRaisesMessage(CommandError, "Restore is destructive"):
            call_command("restore_db", "backup.sqlite3")
