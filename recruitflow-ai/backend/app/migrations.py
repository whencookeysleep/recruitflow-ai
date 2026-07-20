from collections.abc import Callable

from sqlalchemy import Connection, Engine, MetaData, Table, Column, Integer, String, inspect, select, text

from app.database import Base


metadata = MetaData()
schema_migrations = Table(
    "schema_migrations",
    metadata,
    Column("version", Integer, primary_key=True),
    Column("name", String(160), nullable=False),
)


def _create_initial_schema(connection: Connection) -> None:
    Base.metadata.create_all(bind=connection)


def _add_screening_approval_identity(connection: Connection) -> None:
    columns = {
        column["name"]
        for column in inspect(connection).get_columns("screening_assessments")
    }
    if "human_username" not in columns:
        connection.execute(
            text("ALTER TABLE screening_assessments ADD COLUMN human_username VARCHAR(120)")
        )
    if "human_role" not in columns:
        connection.execute(
            text("ALTER TABLE screening_assessments ADD COLUMN human_role VARCHAR(40)")
        )


MIGRATIONS: list[tuple[int, str, Callable[[Connection], None]]] = [
    (1, "create_recruitflow_schema", _create_initial_schema),
    (2, "add_screening_approval_identity", _add_screening_approval_identity),
]


def run_migrations(engine: Engine) -> None:
    with engine.begin() as connection:
        schema_migrations.create(bind=connection, checkfirst=True)
        applied = set(connection.scalars(select(schema_migrations.c.version)).all())
        for version, name, migration in MIGRATIONS:
            if version in applied:
                continue
            migration(connection)
            connection.execute(schema_migrations.insert().values(version=version, name=name))
