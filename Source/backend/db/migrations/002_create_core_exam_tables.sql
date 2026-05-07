CREATE TABLE IF NOT EXISTS students (
    id BIGSERIAL PRIMARY KEY,
    student_number VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    program_code VARCHAR(50) NOT NULL,
    phase VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    assignment_advanced TEXT,
    assignment_competent TEXT,
    assignment_herkansing TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS exams (
    id BIGSERIAL PRIMARY KEY,
    exam_date DATE NOT NULL,
    exam_type VARCHAR(100) NOT NULL,
    room VARCHAR(100) NOT NULL,
    exam_time TIME NOT NULL,
    flag_oproepbrief BOOLEAN NOT NULL DEFAULT FALSE,
    flag_verrassing BOOLEAN NOT NULL DEFAULT FALSE,
    flag_wakker BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS exam_students (
    id BIGSERIAL PRIMARY KEY,
    exam_id BIGINT NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    phase VARCHAR(100) NOT NULL,
    exam_name_op1 VARCHAR(255),
    op2_program_code VARCHAR(50),
    surprise_assignment TEXT,
    stars INTEGER,
    result VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT exam_students_stars_check CHECK (stars IS NULL OR stars >= 0),
    CONSTRAINT exam_students_exam_student_unique UNIQUE (exam_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_students_student_number
    ON students (student_number);

CREATE INDEX IF NOT EXISTS idx_students_program_code
    ON students (program_code);

CREATE INDEX IF NOT EXISTS idx_exams_exam_date
    ON exams (exam_date);

CREATE INDEX IF NOT EXISTS idx_exams_exam_type
    ON exams (exam_type);

CREATE INDEX IF NOT EXISTS idx_exam_students_exam_id
    ON exam_students (exam_id);

CREATE INDEX IF NOT EXISTS idx_exam_students_student_id
    ON exam_students (student_id);
