#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"

if [[ -f "${PROJECT_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  source "${PROJECT_ROOT}/.env"
fi

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5433}"
PGUSER="${PGUSER:-exam_admin}"
PGPASSWORD="${PGPASSWORD:-exam_admin}"
PGDATABASE="${PGDATABASE:-exam_tool}"
DB_MODE="${DB_MODE:-auto}"
DOCKER_AUTO_START="${DOCKER_AUTO_START:-true}"

DB_MODE="$(printf '%s' "${DB_MODE}" | tr '[:upper:]' '[:lower:]')"
DOCKER_AUTO_START="$(printf '%s' "${DOCKER_AUTO_START}" | tr '[:upper:]' '[:lower:]')"

escape_sql_literal() {
  local value="$1"
  value=${value//\'/\'\'}
  printf '%s' "${value}"
}

ensure_docker_compose_available() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker is not installed."
    exit 1
  fi

  if ! docker compose version >/dev/null 2>&1; then
    echo "Error: docker compose is not available."
    exit 1
  fi

  if [[ ! -f "${COMPOSE_FILE}" ]]; then
    echo "Error: docker compose file not found at ${COMPOSE_FILE}."
    exit 1
  fi
}

is_docker_postgres_running() {
  docker compose --file "${COMPOSE_FILE}" --project-directory "${PROJECT_ROOT}" ps --status running --services 2>/dev/null | grep -qx 'postgres'
}

ensure_docker_postgres_running() {
  ensure_docker_compose_available

  if is_docker_postgres_running; then
    return
  fi

  if [[ "${DOCKER_AUTO_START}" == "true" ]]; then
    echo "Postgres service is not running. Starting docker compose service 'postgres'..."
    docker compose --file "${COMPOSE_FILE}" --project-directory "${PROJECT_ROOT}" up -d postgres
    return
  fi

  echo "Error: docker compose service 'postgres' is not running."
  echo "Run: docker compose up -d postgres"
  exit 1
}

wait_for_docker_postgres_ready() {
  local attempts=30

  while (( attempts > 0 )); do
    if docker compose --file "${COMPOSE_FILE}" --project-directory "${PROJECT_ROOT}" exec -T postgres pg_isready -U "${PGUSER}" -d "${PGDATABASE}" >/dev/null 2>&1; then
      return
    fi

    sleep 1
    attempts=$((attempts - 1))
  done

  echo "Error: postgres container did not become ready in time."
  exit 1
}

can_connect_local_postgres() {
  PGPASSWORD="${PGPASSWORD}" psql \
    --host "${PGHOST}" \
    --port "${PGPORT}" \
    --username "${PGUSER}" \
    --dbname postgres \
    --set ON_ERROR_STOP=1 \
    --command "SELECT 1;" >/dev/null 2>&1
}

select_run_mode() {
  case "${DB_MODE}" in
    local)
      if ! command -v psql >/dev/null 2>&1; then
        echo "Error: DB_MODE=local but psql is not installed."
        exit 1
      fi
      RUN_MODE="local"
      export PGPASSWORD
      ;;
    docker)
      RUN_MODE="docker"
      ensure_docker_postgres_running
      wait_for_docker_postgres_ready
      ;;
    auto)
      if command -v psql >/dev/null 2>&1; then
        export PGPASSWORD
        if can_connect_local_postgres; then
          RUN_MODE="local"
        else
          echo "Local psql found, but PostgreSQL is not reachable on ${PGHOST}:${PGPORT}."
          echo "Falling back to docker compose service 'postgres'."
          RUN_MODE="docker"
          ensure_docker_postgres_running
          wait_for_docker_postgres_ready
        fi
      else
        RUN_MODE="docker"
        ensure_docker_postgres_running
        wait_for_docker_postgres_ready
      fi
      ;;
    *)
      echo "Error: invalid DB_MODE='${DB_MODE}'. Use: auto, local, or docker."
      exit 1
      ;;
  esac
}

run_psql() {
  local db_name="$1"
  shift

  if [[ "${RUN_MODE}" == "local" ]]; then
    psql \
      --host "${PGHOST}" \
      --port "${PGPORT}" \
      --username "${PGUSER}" \
      --dbname "${db_name}" \
      --set ON_ERROR_STOP=1 \
      "$@"
    return
  fi

  docker compose --file "${COMPOSE_FILE}" --project-directory "${PROJECT_ROOT}" exec -T postgres psql \
    --username "${PGUSER}" \
    --dbname "${db_name}" \
    --set ON_ERROR_STOP=1 \
    "$@"
}

apply_migration() {
  local migration_file="$1"

  if [[ "${RUN_MODE}" == "local" ]]; then
    run_psql "${PGDATABASE}" --file "${migration_file}"
    return
  fi

  docker compose --file "${COMPOSE_FILE}" --project-directory "${PROJECT_ROOT}" exec -T postgres psql \
    --username "${PGUSER}" \
    --dbname "${PGDATABASE}" \
    --set ON_ERROR_STOP=1 < "${migration_file}"
}

ensure_schema_migrations_table() {
  run_psql "${PGDATABASE}" \
    --command "CREATE TABLE IF NOT EXISTS schema_migrations (filename TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW());"
}

is_migration_applied() {
  local migration_name="$1"
  local escaped_name
  local query_result

  escaped_name="$(escape_sql_literal "${migration_name}")"
  query_result=$(run_psql "${PGDATABASE}" \
    --tuples-only \
    --no-align \
    --command "SELECT 1 FROM schema_migrations WHERE filename='${escaped_name}';" | tr -d '[:space:]')

  [[ "${query_result}" == "1" ]]
}

mark_migration_applied() {
  local migration_name="$1"
  local escaped_name

  escaped_name="$(escape_sql_literal "${migration_name}")"
  run_psql "${PGDATABASE}" \
    --command "INSERT INTO schema_migrations (filename) VALUES ('${escaped_name}') ON CONFLICT (filename) DO NOTHING;"
}

select_run_mode

echo "Using run mode: ${RUN_MODE}"

escaped_db_literal="$(escape_sql_literal "${PGDATABASE}")"
DB_EXISTS=$(run_psql postgres \
  --tuples-only \
  --no-align \
  --command "SELECT 1 FROM pg_database WHERE datname='${escaped_db_literal}';" | tr -d '[:space:]')

if [[ "${DB_EXISTS}" != "1" ]]; then
  echo "Creating database '${PGDATABASE}'..."
  escaped_db_identifier=${PGDATABASE//\"/\"\"}
  run_psql postgres \
    --command "CREATE DATABASE \"${escaped_db_identifier}\";"
else
  echo "Database '${PGDATABASE}' already exists."
fi

ensure_schema_migrations_table

shopt -s nullglob
migrations=("${PROJECT_ROOT}/db/migrations/"*.sql)

if [[ ${#migrations[@]} -eq 0 ]]; then
  echo "No migration files found in ${PROJECT_ROOT}/db/migrations"
  exit 0
fi

for migration in "${migrations[@]}"; do
  migration_name="$(basename "${migration}")"

  if is_migration_applied "${migration_name}"; then
    echo "Skipping ${migration_name} (already applied)."
    continue
  fi

  echo "Applying ${migration_name}..."
  apply_migration "${migration}"
  mark_migration_applied "${migration_name}"
  echo "Applied ${migration_name}."
done

echo "Database initialization complete."
