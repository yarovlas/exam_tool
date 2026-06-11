-- Migration 007: make exam_students.phase nullable (leeg = gebruik student.phase als fallback)
-- Reden: phase wordt soms niet ingesteld bij het koppelen van een student aan een examen;
--        de ophaal-logica valt dan terug op student.phase.

ALTER TABLE exam_students
    ALTER COLUMN phase DROP NOT NULL;

ALTER TABLE exam_students
    ALTER COLUMN phase SET DEFAULT NULL;

-- Zet lege strings (legacy) om naar NULL zodat de OR-fallback in Python correct werkt
UPDATE exam_students
    SET phase = NULL
    WHERE phase = '';
