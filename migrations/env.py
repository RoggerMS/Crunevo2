import logging
from logging.config import fileConfig
from pathlib import Path

from flask import current_app
from alembic import context

config = context.config

# Interpret the config file for Python logging.
config_path = Path(config.config_file_name)
if not config_path.is_absolute():
    config_path = Path(__file__).resolve().parent / config_path

if not config_path.exists():
    raise FileNotFoundError(f"Logging config file not found: {config_path}")

fileConfig(str(config_path))
logger = logging.getLogger("alembic.env")

target_db = None  # Will be defined later with current_app


def get_engine():
    try:
        return current_app.extensions["migrate"].db.get_engine()
    except TypeError:
        return current_app.extensions["migrate"].db.engine


def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace("%", "%%")
    except AttributeError:
        return str(get_engine().url).replace("%", "%%")


def get_metadata():
    if hasattr(target_db, "metadatas"):
        return target_db.metadatas[None]
    return target_db.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=get_metadata(), literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    global target_db
    target_db = current_app.extensions["migrate"].db
    config.set_main_option("sqlalchemy.url", get_engine_url())

    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, "autogenerate", False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info("No changes in schema detected.")

    connectable = get_engine()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            process_revision_directives=process_revision_directives,
            **current_app.extensions["migrate"].configure_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
