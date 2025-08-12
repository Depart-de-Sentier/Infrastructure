set -eu
createuser indico
createdb --owner indico indico
psql indico -c 'CREATE EXTENSION unaccent; CREATE EXTENSION pg_trgm;'
