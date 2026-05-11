"""
run_migrations.py — runs Alembic migrations before the server starts.
"""
import sys

sys.path.insert(0, "/usr/local/lib/python3.12/site-packages")

from alembic.config import Config, command  # noqa: E402

cfg = Config("/app/alembic.ini")
cfg.set_main_option("script_location", "/app/alembic")
command.upgrade(cfg, "head")
print("✅ Migrations completed successfully")
