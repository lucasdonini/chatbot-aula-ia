import importlib.util
from pathlib import Path

import pytest

MIGRATIONS_DIR = (
    Path(__file__).resolve().parent.parent.parent / "migrations" / "versions"
)


class TestMigrationFiles:
    @pytest.mark.parametrize("file", sorted(MIGRATIONS_DIR.glob("*.py")))
    def test_migration_files_exist(self, file):
        assert file.exists()
        assert file.stat().st_size > 0

    def test_initial_migration_revision_value(self):
        init = MIGRATIONS_DIR / "4c6c2484039c_initial_schema.py"
        assert init.exists()

        spec = importlib.util.spec_from_file_location("migration_init", init)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.revision == "4c6c2484039c"
        assert module.down_revision is None
        assert hasattr(module, "upgrade")
        assert hasattr(module, "downgrade")

    def test_enum_migration_revision_value(self):
        enum_mig = (
            MIGRATIONS_DIR / "11fc23606c69_convert_dictionary_tables_into_enums.py"
        )
        assert enum_mig.exists()

        spec = importlib.util.spec_from_file_location("migration_enum", enum_mig)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert module.revision == "11fc23606c69"
        assert module.down_revision == "4c6c2484039c"
        assert hasattr(module, "upgrade")
        assert hasattr(module, "downgrade")

    def test_migration_chain_is_linear(self):
        revisions = {}
        for file in sorted(MIGRATIONS_DIR.glob("*.py")):
            spec = importlib.util.spec_from_file_location(file.stem, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            revisions[module.revision] = module.down_revision

        assert "4c6c2484039c" in revisions
        assert revisions["4c6c2484039c"] is None
        head = [rev for rev, down in revisions.items() if down == "4c6c2484039c"]
        assert len(head) == 1
        assert head[0] == "11fc23606c69"


class TestMigrationSchema:
    def test_migration_creates_category_enum(self):
        """The second migration creates PostgreSQL enums category_enum
        and transaction_type_enum. This test verifies the import
        infrastructure loads correctly."""
        from app.domain.model.transaction import Category, TransactionType

        assert len(Category) == 12
        assert len(TransactionType) == 3

    def test_migration_enum_names_match_orm(self):
        """PostgreSQL enum names must match ORM column definitions."""

        from app.infrastructure.postgres.entities.transaction import TransactionORM

        category_col = TransactionORM.__table__.c["category"]
        tt_col = TransactionORM.__table__.c["transaction_type"]

        assert category_col.type.name == "category_enum"
        assert tt_col.type.name == "transaction_type_enum"
