#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${PROJECT_ROOT}/../.." && pwd)"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
REQUESTED_DB_MODE="${DB_MODE:-}"

if [[ -f "${PROJECT_ROOT}/.env" ]]; then
  # shellcheck disable=SC1091
  source "${PROJECT_ROOT}/.env"
fi

PGHOST="${PGHOST:-localhost}"
PGPORT="${PGPORT:-5433}"
PGUSER="${PGUSER:-exam_admin}"
PGPASSWORD="${PGPASSWORD:-exam_admin}"
PGDATABASE="${PGDATABASE:-exam_tool}"
DB_MODE="${REQUESTED_DB_MODE:-${DB_MODE:-auto}}"
STATIC_DATA_DIR="${STATIC_DATA_DIR:-${REPO_ROOT}/localfiles/output}"

DB_MODE="$(printf '%s' "${DB_MODE}" | tr '[:upper:]' '[:lower:]')"

students_file="${STATIC_DATA_DIR}/students_import_normalized_v2.csv"
regular_products_file="${STATIC_DATA_DIR}/products_regular_import_normalized.csv"
surprise_products_file="${STATIC_DATA_DIR}/products_surprise_import_normalized_v2.csv"
assessors_file="${STATIC_DATA_DIR}/assessors_import_normalized_v2.csv"

required_files=(
  "${students_file}"
  "${regular_products_file}"
  "${surprise_products_file}"
  "${assessors_file}"
)

for file in "${required_files[@]}"; do
  if [[ ! -f "${file}" ]]; then
    echo "Error: static import file not found: ${file}"
    exit 1
  fi
done

can_connect_local_postgres() {
  PGPASSWORD="${PGPASSWORD}" psql \
    --host "${PGHOST}" \
    --port "${PGPORT}" \
    --username "${PGUSER}" \
    --dbname "${PGDATABASE}" \
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
      ;;
    auto)
      if command -v psql >/dev/null 2>&1; then
        export PGPASSWORD
        if can_connect_local_postgres; then
          RUN_MODE="local"
        else
          RUN_MODE="docker"
        fi
      else
        RUN_MODE="docker"
      fi
      ;;
    *)
      echo "Error: invalid DB_MODE='${DB_MODE}'. Use: auto, local, or docker."
      exit 1
      ;;
  esac
}

run_psql_command() {
  if [[ "${RUN_MODE}" == "local" ]]; then
    psql \
      --host "${PGHOST}" \
      --port "${PGPORT}" \
      --username "${PGUSER}" \
      --dbname "${PGDATABASE}" \
      --set ON_ERROR_STOP=1 \
      --command "$1"
    return
  fi

  docker compose --file "${COMPOSE_FILE}" --project-directory "${PROJECT_ROOT}" exec -T postgres psql \
    --username "${PGUSER}" \
    --dbname "${PGDATABASE}" \
    --set ON_ERROR_STOP=1 \
    --command "$1"
}

copy_csv() {
  local table_name="$1"
  local columns="$2"
  local csv_file="$3"

  if [[ "${RUN_MODE}" == "local" ]]; then
    psql \
      --host "${PGHOST}" \
      --port "${PGPORT}" \
      --username "${PGUSER}" \
      --dbname "${PGDATABASE}" \
      --set ON_ERROR_STOP=1 \
      --command "\\copy ${table_name} (${columns}) FROM STDIN WITH (FORMAT csv, HEADER true)" < "${csv_file}"
    return
  fi

  docker compose --file "${COMPOSE_FILE}" --project-directory "${PROJECT_ROOT}" exec -T postgres psql \
    --username "${PGUSER}" \
    --dbname "${PGDATABASE}" \
    --set ON_ERROR_STOP=1 \
    --command "\\copy ${table_name} (${columns}) FROM STDIN WITH (FORMAT csv, HEADER true)" < "${csv_file}"
}

select_run_mode

echo "Importing static data using run mode: ${RUN_MODE}"
echo "Static data directory: ${STATIC_DATA_DIR}"

run_psql_command "DROP TABLE IF EXISTS static_import_students;
CREATE TABLE static_import_students (
  student_number TEXT,
  name TEXT,
  program_code TEXT,
  phase TEXT,
  email TEXT,
  placement_group TEXT
);"
copy_csv "static_import_students" "student_number, name, program_code, phase, email, placement_group" "${students_file}"
run_psql_command "INSERT INTO students (student_number, name, program_code, phase, email, placement_group)
SELECT student_number, name, program_code, phase, NULLIF(email, ''), NULLIF(placement_group, '')
FROM static_import_students
ON CONFLICT (student_number) DO UPDATE SET
  name = EXCLUDED.name,
  program_code = EXCLUDED.program_code,
  phase = EXCLUDED.phase,
  email = EXCLUDED.email,
  placement_group = EXCLUDED.placement_group,
  updated_at = NOW();"

run_psql_command "DROP TABLE IF EXISTS static_import_products;
CREATE TABLE static_import_products (
  product_kind TEXT,
  speciality_code TEXT,
  speciality_name TEXT,
  name TEXT,
  category TEXT,
  stars TEXT,
  document_link TEXT
);"
copy_csv "static_import_products" "product_kind, speciality_code, speciality_name, name, category, stars, document_link" "${regular_products_file}"
copy_csv "static_import_products" "product_kind, speciality_code, speciality_name, name, category, stars, document_link" "${surprise_products_file}"
run_psql_command "INSERT INTO products (product_kind, speciality_code, speciality_name, name, category, stars, document_link)
SELECT
  product_kind,
  speciality_code,
  NULLIF(speciality_name, ''),
  name,
  NULLIF(category, ''),
  NULLIF(stars, '')::INTEGER,
  NULLIF(document_link, '')
FROM static_import_products
ON CONFLICT (product_kind, speciality_code, name) DO UPDATE SET
  speciality_name = EXCLUDED.speciality_name,
  category = EXCLUDED.category,
  stars = EXCLUDED.stars,
  document_link = EXCLUDED.document_link,
  updated_at = NOW();"

run_psql_command "DROP TABLE IF EXISTS static_import_assessors;
CREATE TABLE static_import_assessors (
  assessor_type TEXT,
  name TEXT,
  organization TEXT,
  salutation TEXT,
  address TEXT,
  postal_city TEXT,
  phone TEXT,
  email TEXT,
  recruitment_status TEXT
);"
copy_csv "static_import_assessors" "assessor_type, name, organization, salutation, address, postal_city, phone, email, recruitment_status" "${assessors_file}"
run_psql_command "WITH source AS (
  SELECT
    assessor_type,
    name,
    NULLIF(organization, '') AS organization,
    NULLIF(salutation, '') AS salutation,
    NULLIF(address, '') AS address,
    NULLIF(postal_city, '') AS postal_city,
    NULLIF(phone, '') AS phone,
    NULLIF(email, '') AS email,
    NULLIF(recruitment_status, '') AS recruitment_status
  FROM static_import_assessors
)
UPDATE assessors AS target
SET
  organization = source.organization,
  salutation = source.salutation,
  address = source.address,
  postal_city = source.postal_city,
  phone = source.phone,
  recruitment_status = source.recruitment_status,
  updated_at = NOW()
FROM source
WHERE target.assessor_type = source.assessor_type
  AND target.name = source.name
  AND COALESCE(target.email, '') = COALESCE(source.email, '');

WITH source AS (
  SELECT
    assessor_type,
    name,
    NULLIF(organization, '') AS organization,
    NULLIF(salutation, '') AS salutation,
    NULLIF(address, '') AS address,
    NULLIF(postal_city, '') AS postal_city,
    NULLIF(phone, '') AS phone,
    NULLIF(email, '') AS email,
    NULLIF(recruitment_status, '') AS recruitment_status
  FROM static_import_assessors
)
INSERT INTO assessors (
  assessor_type,
  name,
  organization,
  salutation,
  address,
  postal_city,
  phone,
  email,
  recruitment_status
)
SELECT
  source.assessor_type,
  source.name,
  source.organization,
  source.salutation,
  source.address,
  source.postal_city,
  source.phone,
  source.email,
  source.recruitment_status
FROM source
WHERE NOT EXISTS (
  SELECT 1
  FROM assessors AS target
  WHERE target.assessor_type = source.assessor_type
    AND target.name = source.name
    AND COALESCE(target.email, '') = COALESCE(source.email, '')
);"

run_psql_command "SELECT
  (SELECT COUNT(*) FROM students) AS students,
  (SELECT COUNT(*) FROM products WHERE product_kind = 'regular') AS regular_products,
  (SELECT COUNT(*) FROM products WHERE product_kind = 'surprise') AS surprise_products,
  (SELECT COUNT(*) FROM assessors) AS assessors;"

run_psql_command "DROP TABLE IF EXISTS static_import_students;
DROP TABLE IF EXISTS static_import_products;
DROP TABLE IF EXISTS static_import_assessors;"

echo "Static data import complete."
