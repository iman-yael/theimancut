-- Migration 002: crew/stunt credits (identity-relevant: stunt doubles affect who is actually on screen).
CREATE TABLE crew_credit (
  work_uuid TEXT NOT NULL REFERENCES work(uuid),
  person_uuid TEXT NOT NULL REFERENCES person(uuid),
  department TEXT NOT NULL,
  role_verbatim TEXT NOT NULL,
  credited_episode_count INTEGER,
  doubles_for_person TEXT REFERENCES person(uuid),   -- set when role names a performer this person doubles
  ingestion_uuid TEXT REFERENCES entity(uuid),
  PRIMARY KEY (work_uuid, person_uuid, department, role_verbatim)
);
