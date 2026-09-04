import os
import sys

from testcontainers.community.postgres import PostgresContainer


def main() -> None:
    with PostgresContainer(
        "postgres:18",
        username="test_user",
        password="test_password",
        dbname="test_db",
    ) as postgres:
        os.environ.update(
            {
                "SECRET_KEY": "ci-test-secret-key",
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

        execute_from_command_line(["manage.py", "test", *sys.argv[1:]])


if __name__ == "__main__":
    main()
