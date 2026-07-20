from collections.abc import Callable
import json

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


def _clear_cross_name_duplicate_matches(connection: Connection) -> None:
    rows = connection.execute(
        text(
            "SELECT r.id, r.parsed_payload, c.name AS candidate_name "
            "FROM resume_files r JOIN candidates c ON c.id = r.duplicate_candidate_id "
            "WHERE r.parse_status = 'possible_duplicate'"
        )
    ).mappings()
    for row in rows:
        payload = row["parsed_payload"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        parsed_name = "".join((payload.get("name") or "").split()).casefold()
        candidate_name = "".join((row["candidate_name"] or "").split()).casefold()
        if parsed_name and candidate_name and parsed_name != candidate_name:
            connection.execute(
                text(
                    "UPDATE resume_files SET duplicate_candidate_id = NULL, "
                    "parse_status = 'pending_confirmation' WHERE id = :resume_id"
                ),
                {"resume_id": row["id"]},
            )


def _add_screening_approval_role(connection: Connection) -> None:
    columns = {
        column["name"]
        for column in inspect(connection).get_columns("screening_assessments")
    }
    if "human_role" not in columns:
        connection.execute(
            text("ALTER TABLE screening_assessments ADD COLUMN human_role VARCHAR(40)")
        )


MIGRATIONS: list[tuple[int, str, Callable[[Connection], None]]] = [
    (1, "create_recruitflow_schema", _create_initial_schema),
    (2, "add_screening_approval_identity", _add_screening_approval_identity),
    (3, "clear_cross_name_duplicate_matches", _clear_cross_name_duplicate_matches),
    (4, "add_screening_approval_role", _add_screening_approval_role),
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
