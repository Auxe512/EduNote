-- EduNote schema extension

DEFINE TABLE exam_paper SCHEMAFULL;
DEFINE FIELD notebook_id ON TABLE exam_paper TYPE record<notebook>;
DEFINE FIELD file_name   ON TABLE exam_paper TYPE string;
DEFINE FIELD created_at  ON TABLE exam_paper TYPE datetime DEFAULT time::now();

DEFINE TABLE exam_topic SCHEMAFULL;
DEFINE FIELD exam_paper_id  ON TABLE exam_topic TYPE record<exam_paper>;
DEFINE FIELD notebook_id    ON TABLE exam_topic TYPE record<notebook>;
DEFINE FIELD topic          ON TABLE exam_topic TYPE string;
DEFINE FIELD count          ON TABLE exam_topic TYPE int;
DEFINE FIELD description    ON TABLE exam_topic TYPE string;

DEFINE TABLE question SCHEMAFULL;
DEFINE FIELD notebook_id  ON TABLE question TYPE record<notebook>;
DEFINE FIELD question     ON TABLE question TYPE string;
DEFINE FIELD options      ON TABLE question TYPE array<string>;
DEFINE FIELD correct      ON TABLE question TYPE string;
DEFINE FIELD topic        ON TABLE question TYPE string;
DEFINE FIELD explanation  ON TABLE question TYPE string;
DEFINE FIELD created_at   ON TABLE question TYPE datetime DEFAULT time::now();

DEFINE TABLE quiz_attempt SCHEMAFULL;
DEFINE FIELD notebook_id    ON TABLE quiz_attempt TYPE record<notebook>;
DEFINE FIELD user_id        ON TABLE quiz_attempt TYPE record<user>;
DEFINE FIELD question_ids   ON TABLE quiz_attempt TYPE array<record<question>>;
DEFINE FIELD score          ON TABLE quiz_attempt TYPE option<float>;
DEFINE FIELD completed      ON TABLE quiz_attempt TYPE bool DEFAULT false;
DEFINE FIELD created_at     ON TABLE quiz_attempt TYPE datetime DEFAULT time::now();

DEFINE TABLE answer_record SCHEMAFULL;
DEFINE FIELD attempt_id   ON TABLE answer_record TYPE record<quiz_attempt>;
DEFINE FIELD question_id  ON TABLE answer_record TYPE record<question>;
DEFINE FIELD chosen       ON TABLE answer_record TYPE string;
DEFINE FIELD is_correct   ON TABLE answer_record TYPE bool;
DEFINE FIELD topic        ON TABLE answer_record TYPE string;

DEFINE TABLE flashcard SCHEMAFULL;
DEFINE FIELD notebook_id  ON TABLE flashcard TYPE record<notebook>;
DEFINE FIELD front        ON TABLE flashcard TYPE string;
DEFINE FIELD back         ON TABLE flashcard TYPE string;
DEFINE FIELD topic        ON TABLE flashcard TYPE string;
DEFINE FIELD created_at   ON TABLE flashcard TYPE datetime DEFAULT time::now();

DEFINE TABLE flashcard_review SCHEMAFULL;
DEFINE FIELD flashcard_id  ON TABLE flashcard_review TYPE record<flashcard>;
DEFINE FIELD user_id       ON TABLE flashcard_review TYPE record<user>;
DEFINE FIELD is_correct    ON TABLE flashcard_review TYPE bool;
DEFINE FIELD reviewed_at   ON TABLE flashcard_review TYPE datetime DEFAULT time::now();

DEFINE TABLE study_session SCHEMAFULL;
DEFINE FIELD user_id       ON TABLE study_session TYPE record<user>;
DEFINE FIELD notebook_id   ON TABLE study_session TYPE record<notebook>;
DEFINE FIELD note_id       ON TABLE study_session TYPE option<record<note>>;
DEFINE FIELD activity_type ON TABLE study_session TYPE string;
DEFINE FIELD started_at    ON TABLE study_session TYPE datetime DEFAULT time::now();
