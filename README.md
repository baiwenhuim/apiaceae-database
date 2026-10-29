# Apiaceae Database

This repository contains the Django application, database models and migrations,
related scripts, and project documentation. Local datasets, database dumps,
generated files, caches, and bulky assets are intentionally excluded.

## Configuration

Set these environment variables before running Django:

- `DJANGO_SECRET_KEY`: a unique, private Django secret key
- `DJANGO_DEBUG`: optional; set to `true` for local development (defaults to `false`)
- `MYSQL_DB_NAME`: MySQL database name
- `MYSQL_USER`: MySQL username
- `MYSQL_PASSWORD`: MySQL password
- `MYSQL_HOST`: optional; defaults to `127.0.0.1`
- `MYSQL_PORT`: optional; defaults to `3306`

Do not commit credentials or local `.env` files.
