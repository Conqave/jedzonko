#!/bin/bash
set -euo pipefail
mariadb --user=root --password="${MARIADB_ROOT_PASSWORD}" <<SQL
GRANT ALL PRIVILEGES ON \`test\_%\`.* TO '${MARIADB_USER}'@'%';
FLUSH PRIVILEGES;
SQL
