"""
run_migrations.py — runs Alembic migrations avoiding the local /app/alembic folder
conflict with the installed alembic package.
"""
import sys

sys.path.insert(0, "/usr/local/lib/python3.12/site-packages")

from alembic.config import Config, command  # noqa: E402

cfg = Config("/app/alembic.ini")
cfg.set_main_option("script_location", "/app/alembic")
command.upgrade(cfg, "head")
print("✅ Migrations completed successfully")