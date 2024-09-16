import pathlib

import alembic.config
import pytest
import semantic_workbench_service
from semantic_workbench_service.config import DBSettings


def test_migration_cycle(db_settings: DBSettings, monkeypatch: pytest.MonkeyPatch) -> None:
    if not db_settings.url.startswith("postgresql"):
        pytest.skip(f"postgres migration test skipped for db url {db_settings.url}")

    monkeypatch.setattr(semantic_workbench_service.settings, "db", db_settings)

    monkeypatch.chdir(pathlib.Path(__file__).parent / "..")

    """Test that all migrations can upgrade and downgrade without error."""

    # upgrade to head
    alembic.config.main(argv=["--raiseerr", "upgrade", "head"])

    # check that the current revision is head
    alembic.config.main(argv=["--raiseerr", "check"])

    # downgrade to base
    alembic.config.main(argv=["--raiseerr", "downgrade", "base"])

    # and upgrade back to head
    alembic.config.main(argv=["--raiseerr", "upgrade", "head"])

    # check that the current revision is head
    alembic.config.main(argv=["--raiseerr", "check"])
