from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.utils import ConnectionDoesNotExist

from core.backups import BackupError, create_postgres_backup, create_sqlite_backup, prune_backups


class Command(BaseCommand):
    help = "Create a database backup."

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="default",
            help="Database alias from Django DATABASES. Defaults to 'default'.",
        )
        parser.add_argument(
            "--output-dir",
            default=settings.DATABASE_BACKUP_DIR,
            help="Directory where the backup file and metadata will be saved.",
        )
        parser.add_argument(
            "--keep-last",
            type=int,
            default=0,
            help="Keep only the newest N backups in the output directory. Disabled by default.",
        )

    def handle(self, *args, **options):
        alias = options["database"]
        output_dir = Path(options["output_dir"])

        try:
            connection = connections[alias]
        except ConnectionDoesNotExist as exc:
            raise CommandError(f"Database alias does not exist: {alias}") from exc

        db_settings = connection.settings_dict
        engine = db_settings["ENGINE"]

        try:
            if "sqlite3" in engine:
                connection.close()
                backup_path = create_sqlite_backup(db_settings["NAME"], output_dir, label=alias)
            elif "postgresql" in engine:
                backup_path = create_postgres_backup(db_settings, output_dir, label=alias)
            else:
                raise CommandError(f"Unsupported database engine for backups: {engine}")

            removed_backups = prune_backups(output_dir, options["keep_last"])
        except BackupError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Backup created: {backup_path}"))
        if removed_backups:
            self.stdout.write(f"Pruned {len(removed_backups)} old backup(s).")
