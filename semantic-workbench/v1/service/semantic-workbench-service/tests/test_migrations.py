import os

import alembic.config
import pytest


def test_migration_cycle(db_url: str, service_dir: str, monkeypatch: pytest.MonkeyPatch) -> None:
    if not db_url.startswith("postgresql"):
        pytest.skip(f"postgres migration test skipped for db url {db_url}")

    monkeypatch.chdir(os.path.join(service_dir, "semantic-workbench-service"))

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
