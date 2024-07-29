set -e
echo "Creating database: workbench; user: $POSTGRES_USER"
psql -v ON_ERROR_STOP=1 --no-psqlrc --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOF
    CREATE database workbench;
EOF
