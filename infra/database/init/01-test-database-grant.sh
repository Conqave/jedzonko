#!/bin/bash
# Django creates a throwaway `test_<database>` schema when running the backend test suite.
set -euo pipefail
mariadb --user=root --password="${MARIADB_ROOT_PASSWORD}" <<SQL
GRANT ALL PRIVILEGES ON \`test\_%\`.* TO '${MARIADB_USER}'@'%';
FLUSH PRIVILEGES;
SQL
