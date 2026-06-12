CREATE TABLE IF NOT EXISTS students (
    id BIGSERIAL PRIMARY KEY,
    student_number VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    program_code VARCHAR(50) NOT NULL,
    phase VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS exam_students (
    id BIGSERIAL PRIMARY KEY,
    exam_planning_id BIGINT NOT NULL REFERENCES exam_planning(id) ON DELETE CASCADE,
    student_id BIGINT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    phase VARCHAR(100) NOT NULL,
    result VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT exam_students_exam_student_unique UNIQUE (exam_planning_id, student_id)
);

CREATE INDEX IF NOT EXISTS idx_students_student_number
    ON students (student_number);

CREATE INDEX IF NOT EXISTS idx_students_program_code
    ON students (program_code);

CREATE INDEX IF NOT EXISTS idx_exam_students_exam_planning_id
    ON exam_students (exam_planning_id);

CREATE INDEX IF NOT EXISTS idx_exam_students_student_id
    ON exam_students (student_id);
