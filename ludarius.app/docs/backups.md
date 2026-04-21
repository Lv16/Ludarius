# Database backups

The project has Django management commands for database backup and restore.

## Create a backup

```powershell
python manage.py backup_db
```

By default, files are written to `backups/database/`. Override this with:

```powershell
python manage.py backup_db --output-dir D:\ludarius-backups\database
```

Keep only the newest backups in the target directory:

```powershell
python manage.py backup_db --keep-last 7
```

Each backup also writes a `.json` metadata file with creation time, source,
format, and SHA-256 checksum.

## Restore a backup

Restore is destructive and requires explicit confirmation:

```powershell
python manage.py restore_db backups\database\ludarius-default-20260421-120000-000000.sqlite3 --confirm
```

For PostgreSQL backups, pass the `.dump` file:

```powershell
python manage.py restore_db D:\ludarius-backups\database\ludarius-default-20260421-120000-000000.dump --confirm
```

The restore command verifies the checksum when the matching metadata file is
available next to the backup.

## Production notes

- Never commit database backups. The project ignores `backups/` in Git.
- Set `DATABASE_BACKUP_DIR` in production to a persistent location outside the deploy folder.
- PostgreSQL backup and restore require `pg_dump` and `pg_restore` available in `PATH`.
- Store production backups outside the app server when possible, for example in the hosting provider backup storage or an encrypted object storage bucket.
- Test a restore periodically in a separate staging database before relying on the backup routine.

## Scheduling

Use the host scheduler rather than keeping a backup loop inside Django.

Windows Task Scheduler example action:

```powershell
powershell.exe -ExecutionPolicy Bypass -Command "cd C:\Ludarius\ludarius.app; .\.venv\Scripts\python.exe manage.py backup_db --keep-last 14"
```

Linux cron example:

```cron
15 3 * * * cd /app/ludarius.app && ./.venv/bin/python manage.py backup_db --keep-last 14 >> /var/log/ludarius-backup.log 2>&1
```
