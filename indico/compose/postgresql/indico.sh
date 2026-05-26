set -eu

# The official postgres image already creates the role and database from
# POSTGRES_USER / POSTGRES_DB in .env. All this init script has to do is
# install the extensions Indico requires.
psql -v ON_ERROR_STOP=1 --username "${POSTGRES_USER}" --dbname "${POSTGRES_DB}" <<-EOSQL
  CREATE EXTENSION unaccent;
  CREATE EXTENSION pg_trgm;
EOSQL
