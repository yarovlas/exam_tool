CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DO $$
BEGIN
    IF to_regclass('public.exam_planning') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_exam_planning_updated_at') THEN
        EXECUTE 'CREATE TRIGGER set_exam_planning_updated_at
                 BEFORE UPDATE ON exam_planning
                 FOR EACH ROW
                 EXECUTE FUNCTION set_updated_at()';
    END IF;

    IF to_regclass('public.students') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_students_updated_at') THEN
        EXECUTE 'CREATE TRIGGER set_students_updated_at
                 BEFORE UPDATE ON students
                 FOR EACH ROW
                 EXECUTE FUNCTION set_updated_at()';
    END IF;

    IF to_regclass('public.exam_students') IS NOT NULL
       AND NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'set_exam_students_updated_at') THEN
        EXECUTE 'CREATE TRIGGER set_exam_students_updated_at
                 BEFORE UPDATE ON exam_students
                 FOR EACH ROW
                 EXECUTE FUNCTION set_updated_at()';
    END IF;
END
$$;
