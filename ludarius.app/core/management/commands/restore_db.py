from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.utils import ConnectionDoesNotExist

from core.backups import BackupError, restore_postgres_backup, restore_sqlite_backup


class Command(BaseCommand):
    help = "Restore a database backup. This overwrites the target database."

    def add_arguments(self, parser):
        parser.add_argument("backup_path", help="Path to the backup file to restore.")
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias from Django DATABASES. Defaults to 'default'.",
        )
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Required because restore overwrites the target database.",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError("Restore is destructive. Re-run with --confirm when you are sure.")

        alias = options["database"]
        backup_path = Path(options["backup_path"])

        try:
            connection = connections[alias]
        except ConnectionDoesNotExist as exc:
            raise CommandError(f"Database alias does not exist: {alias}") from exc

        db_settings = connection.settings_dict
        engine = db_settings["ENGINE"]

        try:
            if "sqlite3" in engine:
                connection.close()
                restored_path = restore_sqlite_backup(backup_path, db_settings["NAME"])
                self.stdout.write(self.style.SUCCESS(f"SQLite database restored: {restored_path}"))
            elif "postgresql" in engine:
                connection.close()
                restore_postgres_backup(db_settings, backup_path)
                self.stdout.write(self.style.SUCCESS("PostgreSQL database restored."))
            else:
                raise CommandError(f"Unsupported database engine for restore: {engine}")
        except BackupError as exc:
            raise CommandError(str(exc)) from exc
