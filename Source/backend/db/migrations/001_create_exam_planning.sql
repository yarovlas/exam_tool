CREATE TABLE IF NOT EXISTS exam_planning (
    id BIGSERIAL PRIMARY KEY,
    exam_date DATE NOT NULL,
    exam_type VARCHAR(100) NOT NULL,
    room VARCHAR(100) NOT NULL,
    exam_time TIME NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'planned',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT exam_planning_status_check
        CHECK (status IN ('planned', 'confirmed', 'completed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_exam_planning_exam_date
    ON exam_planning (exam_date);

CREATE INDEX IF NOT EXISTS idx_exam_planning_status
    ON exam_planning (status);
