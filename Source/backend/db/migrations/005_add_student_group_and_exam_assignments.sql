ALTER TABLE students
    ADD COLUMN IF NOT EXISTS placement_group VARCHAR(100);

CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    product_kind VARCHAR(50) NOT NULL,
    speciality_code VARCHAR(50) NOT NULL,
    speciality_name VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    stars INTEGER,
    document_link TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT products_kind_check CHECK (product_kind IN ('regular', 'surprise')),
    CONSTRAINT products_stars_check CHECK (stars IS NULL OR stars >= 0),
    CONSTRAINT products_document_link_kind_check
        CHECK (document_link IS NULL OR product_kind = 'surprise')
);

CREATE TABLE IF NOT EXISTS assessors (
    id BIGSERIAL PRIMARY KEY,
    assessor_type VARCHAR(30) NOT NULL,
    name VARCHAR(255) NOT NULL,
    organization VARCHAR(255),
    salutation VARCHAR(100),
    address TEXT,
    postal_city VARCHAR(255),
    phone VARCHAR(100),
    email VARCHAR(255),
    recruitment_status VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT assessors_type_check CHECK (assessor_type IN ('external', 'teacher'))
);

CREATE TABLE IF NOT EXISTS exam_assessors (
    id BIGSERIAL PRIMARY KEY,
    exam_planning_id BIGINT NOT NULL REFERENCES exam_planning(id) ON DELETE CASCADE,
    assessor_id BIGINT NOT NULL REFERENCES assessors(id) ON DELETE RESTRICT,
    assessor_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT exam_assessors_order_check CHECK (assessor_order IN (1, 2)),
    CONSTRAINT exam_assessors_unique_slot UNIQUE (exam_planning_id, assessor_order),
    CONSTRAINT exam_assessors_unique_assessor UNIQUE (exam_planning_id, assessor_id)
);

CREATE TABLE IF NOT EXISTS assignments (
    id BIGSERIAL PRIMARY KEY,
    exam_student_id BIGINT NOT NULL REFERENCES exam_students(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    regular_stars INTEGER NOT NULL DEFAULT 0,
    required_stars INTEGER NOT NULL DEFAULT 0,
    total_stars INTEGER NOT NULL DEFAULT 0,
    result VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT assignments_status_check
        CHECK (status IN ('draft', 'confirmed', 'completed', 'cancelled')),
    CONSTRAINT assignments_regular_stars_check CHECK (regular_stars >= 0),
    CONSTRAINT assignments_required_stars_check CHECK (required_stars >= 0),
    CONSTRAINT assignments_total_stars_check CHECK (total_stars >= 0),
    CONSTRAINT assignments_exam_student_unique UNIQUE (exam_student_id)
);

CREATE TABLE IF NOT EXISTS assignment_products (
    id BIGSERIAL PRIMARY KEY,
    assignment_id BIGINT NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    product_id BIGINT REFERENCES products(id) ON DELETE RESTRICT,
    product_role VARCHAR(50) NOT NULL,
    product_order INTEGER NOT NULL DEFAULT 1,
    product_text TEXT,
    stars INTEGER,
    result VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT assignment_products_role_check
        CHECK (product_role IN ('required', 'choice', 'surprise', 'bpv', 'practice_tool', 'custom')),
    CONSTRAINT assignment_products_order_check CHECK (product_order > 0),
    CONSTRAINT assignment_products_stars_check CHECK (stars IS NULL OR stars >= 0),
    CONSTRAINT assignment_products_has_product
        CHECK (product_id IS NOT NULL OR product_text IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_students_placement_group
    ON students (placement_group);

CREATE INDEX IF NOT EXISTS idx_products_speciality_kind
    ON products (speciality_code, product_kind);

CREATE INDEX IF NOT EXISTS idx_products_category
    ON products (category);

CREATE UNIQUE INDEX IF NOT EXISTS idx_products_import_identity
    ON products (product_kind, speciality_code, name);

CREATE INDEX IF NOT EXISTS idx_assessors_type
    ON assessors (assessor_type);

CREATE INDEX IF NOT EXISTS idx_assessors_name
    ON assessors (name);

CREATE UNIQUE INDEX IF NOT EXISTS idx_assessors_identity
    ON assessors (assessor_type, name, COALESCE(email, ''));

CREATE INDEX IF NOT EXISTS idx_exam_assessors_exam_planning_id
    ON exam_assessors (exam_planning_id);

CREATE INDEX IF NOT EXISTS idx_exam_assessors_assessor_id
    ON exam_assessors (assessor_id);

CREATE INDEX IF NOT EXISTS idx_assignments_exam_student_id
    ON assignments (exam_student_id);

CREATE INDEX IF NOT EXISTS idx_assignment_products_assignment_id
    ON assignment_products (assignment_id);

CREATE INDEX IF NOT EXISTS idx_assignment_products_product_id
    ON assignment_products (product_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_assignment_products_unique_slot
    ON assignment_products (assignment_id, product_role, product_order);

CREATE UNIQUE INDEX IF NOT EXISTS idx_assignment_products_unique_product
    ON assignment_products (assignment_id, product_id)
    WHERE product_id IS NOT NULL;

DO $$
BEGIN
    IF to_regclass('public.products') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_products_updated_at') THEN
        EXECUTE 'CREATE TRIGGER set_products_updated_at
                 BEFORE UPDATE ON products
                 FOR EACH ROW
                 EXECUTE FUNCTION set_updated_at()';
    END IF;

    IF to_regclass('public.assessors') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_assessors_updated_at') THEN
        EXECUTE 'CREATE TRIGGER set_assessors_updated_at
                 BEFORE UPDATE ON assessors
                 FOR EACH ROW
                 EXECUTE FUNCTION set_updated_at()';
    END IF;

    IF to_regclass('public.exam_assessors') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_exam_assessors_updated_at') THEN
        EXECUTE 'CREATE TRIGGER set_exam_assessors_updated_at
                 BEFORE UPDATE ON exam_assessors
                 FOR EACH ROW
                 EXECUTE FUNCTION set_updated_at()';
    END IF;

    IF to_regclass('public.assignments') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_assignments_updated_at') THEN
        EXECUTE 'CREATE TRIGGER set_assignments_updated_at
                 BEFORE UPDATE ON assignments
                 FOR EACH ROW
                 EXECUTE FUNCTION set_updated_at()';
    END IF;

    IF to_regclass('public.assignment_products') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_assignment_products_updated_at') THEN
        EXECUTE 'CREATE TRIGGER set_assignment_products_updated_at
                 BEFORE UPDATE ON assignment_products
                 FOR EACH ROW
                 EXECUTE FUNCTION set_updated_at()';
    END IF;
END
$$;
