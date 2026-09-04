import os
import sys
from pathlib import Path

from testcontainers.community.postgres import PostgresContainer


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
TEST_APPS = ("users", "tasks", "comments")
sys.path.insert(0, str(SRC_ROOT))


def main() -> None:
    with PostgresContainer(
        "postgres:18",
        username="test_user",
        password="test_password",
        dbname="test_db",
    ) as postgres:
        os.environ.update(
            {
                "SECRET_KEY": "ci-test-secret-key-with-at-least-32-bytes",
                "DEBUG": "false",
                "ALLOWED_HOSTS": "localhost",
                "POSTGRES_DB": "test_db",
                "POSTGRES_USER": "test_user",
                "POSTGRES_PASSWORD": "test_password",
                "POSTGRES_HOST": postgres.get_container_host_ip(),
                "POSTGRES_PORT": str(postgres.get_exposed_port(5432)),
            }
        )

        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "test", *TEST_APPS, *sys.argv[1:]]
        )


if __name__ == "__main__":
    main()
