from sqlalchemy import create_engine, inspect, text

from app.migrations import run_migrations


def test_existing_database_applies_duplicate_cleanup_and_approval_role() -> None:
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE candidates (id INTEGER PRIMARY KEY, name VARCHAR(120))"))
        connection.execute(
            text(
                "CREATE TABLE resume_files ("
                "id INTEGER PRIMARY KEY, parsed_payload JSON, "
                "duplicate_candidate_id INTEGER, parse_status VARCHAR(80))"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE screening_assessments ("
                "id INTEGER PRIMARY KEY, human_username VARCHAR(120))"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE schema_migrations ("
                "version INTEGER PRIMARY KEY, name VARCHAR(160) NOT NULL)"
            )
        )
        connection.execute(
            text(
                "INSERT INTO schema_migrations (version, name) VALUES "
                "(1, 'create_recruitflow_schema'), "
                "(2, 'add_screening_approval_identity')"
            )
        )
        connection.execute(text("INSERT INTO candidates (id, name) VALUES (1, 'Alice')"))
        connection.execute(
            text(
                "INSERT INTO resume_files "
                "(id, parsed_payload, duplicate_candidate_id, parse_status) "
                "VALUES (1, '{\"name\": \"Bob\"}', 1, 'possible_duplicate')"
            )
        )

    run_migrations(engine)

    with engine.connect() as connection:
        resume = connection.execute(
            text(
                "SELECT duplicate_candidate_id, parse_status "
                "FROM resume_files WHERE id = 1"
            )
        ).one()
        versions = set(connection.scalars(text("SELECT version FROM schema_migrations")))
        columns = {column["name"] for column in inspect(connection).get_columns("screening_assessments")}

    assert resume.duplicate_candidate_id is None
    assert resume.parse_status == "pending_confirmation"
    assert versions == {1, 2, 3, 4}
    assert "human_role" in columns
