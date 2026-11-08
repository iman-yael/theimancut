-- The Iman Cut catalog — migration 001. Title-agnostic schema.
-- Conventions: every record has an immutable uuid + readable display_id in `entity`.
-- Timing: integer ticks at the canonical time base 1/240000 s (see meta.timebase); intervals are [start, end).

CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
INSERT INTO meta VALUES ('timebase', '1/240000');

CREATE TABLE id_counter (prefix TEXT PRIMARY KEY, next_value INTEGER NOT NULL);

CREATE TABLE entity (
  uuid TEXT PRIMARY KEY,
  display_id TEXT NOT NULL UNIQUE,
  type TEXT NOT NULL,
  rev INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  retired_to TEXT REFERENCES entity(uuid),       -- merge redirect; record kept forever
  retired_reason TEXT
);

-- Full snapshot per revision. Never updated or deleted.
CREATE TABLE revision (
  entity_uuid TEXT NOT NULL REFERENCES entity(uuid),
  rev INTEGER NOT NULL,
  snapshot_json TEXT NOT NULL,
  changed_fields TEXT,
  ingestion_uuid TEXT REFERENCES entity(uuid),
  actor TEXT NOT NULL,
  note TEXT,
  at TEXT NOT NULL,
  PRIMARY KEY (entity_uuid, rev)
);

CREATE TABLE audit_log (id INTEGER PRIMARY KEY, at TEXT NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL, entity_uuid TEXT, detail TEXT);

-- ---------- Intake ----------
CREATE TABLE ingestion (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  kind TEXT NOT NULL,                 -- cast_list | research | asset | transcript | correction
  original_name TEXT NOT NULL,
  stored_path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  provenance TEXT NOT NULL,           -- who supplied it / where it came from
  received_at TEXT NOT NULL,
  report_json TEXT,
  UNIQUE (kind, sha256)
);
CREATE TABLE review_queue (
  id INTEGER PRIMARY KEY,
  ingestion_uuid TEXT REFERENCES entity(uuid),
  kind TEXT NOT NULL,                 -- ambiguous_match | conflict | unresolved_reference
  payload_json TEXT NOT NULL,
  candidates_json TEXT,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved','dismissed')),
  resolution TEXT,
  UNIQUE (kind, payload_json)
);
CREATE TABLE provenance (
  entity_uuid TEXT NOT NULL REFERENCES entity(uuid),
  field TEXT NOT NULL,
  value TEXT,
  ingestion_uuid TEXT REFERENCES entity(uuid),
  source_uuid TEXT REFERENCES entity(uuid),
  at TEXT NOT NULL
);

-- ---------- 1. Media catalog ----------
CREATE TABLE work (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  title TEXT NOT NULL,
  work_type TEXT NOT NULL CHECK (work_type IN ('series','limited_series','movie','documentary','documentary_series','special','short','other')),
  first_release TEXT, notes TEXT
);
CREATE TABLE work_title (work_uuid TEXT NOT NULL REFERENCES work(uuid), title TEXT NOT NULL, language TEXT, region TEXT, kind TEXT, PRIMARY KEY (work_uuid, title, language, region));
CREATE TABLE external_id (entity_uuid TEXT NOT NULL REFERENCES entity(uuid), provider TEXT NOT NULL, value TEXT NOT NULL, PRIMARY KEY (provider, value));
CREATE TABLE season (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), work_uuid TEXT NOT NULL REFERENCES work(uuid), label TEXT NOT NULL, ordinal INTEGER);
CREATE TABLE installment (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  work_uuid TEXT NOT NULL REFERENCES work(uuid),
  season_uuid TEXT REFERENCES season(uuid),          -- NULL for movies/specials
  kind TEXT NOT NULL CHECK (kind IN ('episode','feature','special','short','other')),
  title TEXT, synopsis TEXT, spoiler_level TEXT
);
CREATE TABLE installment_number (installment_uuid TEXT NOT NULL REFERENCES installment(uuid), scheme TEXT NOT NULL, label TEXT NOT NULL, ordinal INTEGER, PRIMARY KEY (installment_uuid, scheme));
CREATE TABLE release_date (entity_uuid TEXT NOT NULL REFERENCES entity(uuid), region TEXT NOT NULL, date TEXT NOT NULL, platform TEXT, PRIMARY KEY (entity_uuid, region, platform));
CREATE TABLE edition (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), installment_uuid TEXT NOT NULL REFERENCES installment(uuid), name TEXT NOT NULL, region TEXT, runtime_ticks INTEGER, notes TEXT);

-- ---------- 2. People and story identities ----------
CREATE TABLE person (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), name TEXT NOT NULL, norm_name TEXT NOT NULL, born TEXT, died TEXT, bio_actor TEXT, bio_historical TEXT, notes TEXT);
CREATE TABLE person_name (person_uuid TEXT NOT NULL REFERENCES person(uuid), name TEXT NOT NULL, norm_name TEXT NOT NULL, kind TEXT NOT NULL, claim_uuid TEXT REFERENCES entity(uuid), PRIMARY KEY (person_uuid, norm_name, kind));
CREATE TABLE character (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  work_uuid TEXT NOT NULL REFERENCES work(uuid),
  credited_name TEXT NOT NULL, norm_name TEXT NOT NULL,
  counterpart_status TEXT NOT NULL DEFAULT 'unconfirmed' CHECK (counterpart_status IN ('real_person','fictional','composite','disputed','unconfirmed')),
  relationship_to_subject TEXT, profile_json TEXT, notes TEXT
);
CREATE TABLE character_name (character_uuid TEXT NOT NULL REFERENCES character(uuid), name TEXT NOT NULL, norm_name TEXT NOT NULL, kind TEXT NOT NULL, verification TEXT NOT NULL DEFAULT 'supplied', source TEXT, PRIMARY KEY (character_uuid, norm_name, kind));
CREATE TABLE portrayal (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  character_uuid TEXT NOT NULL REFERENCES character(uuid),
  person_uuid TEXT NOT NULL REFERENCES person(uuid),
  age_portrayal TEXT NOT NULL DEFAULT 'primary',       -- primary | young | older | voice | other
  voice_only INTEGER NOT NULL DEFAULT 0,
  credit_status TEXT NOT NULL DEFAULT 'credited' CHECK (credit_status IN ('credited','uncredited','unknown')),
  credit_verification TEXT NOT NULL DEFAULT 'supplied',  -- supplied | V1 | V2 | VC (on-screen credits)
  credited_episode_count INTEGER,                         -- as listed by a provider; NOT appearance data
  notes TEXT,
  UNIQUE (character_uuid, person_uuid, age_portrayal)
);
CREATE TABLE portrayal_credit_name (portrayal_uuid TEXT NOT NULL REFERENCES portrayal(uuid), credited_character_name TEXT NOT NULL, credited_actor_name TEXT NOT NULL, ingestion_uuid TEXT REFERENCES entity(uuid), PRIMARY KEY (portrayal_uuid, credited_character_name, credited_actor_name));
CREATE TABLE portrayal_installment (portrayal_uuid TEXT NOT NULL REFERENCES portrayal(uuid), installment_uuid TEXT NOT NULL REFERENCES installment(uuid), source TEXT, PRIMARY KEY (portrayal_uuid, installment_uuid));
CREATE TABLE historical_link (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  character_uuid TEXT NOT NULL REFERENCES character(uuid),
  person_uuid TEXT REFERENCES person(uuid),
  link_type TEXT NOT NULL CHECK (link_type IN ('depicts','composite_of','inspired_by','disputed','none_known')),
  claim_uuid TEXT REFERENCES entity(uuid),
  UNIQUE (character_uuid, person_uuid, link_type)
);
CREATE TABLE relationship (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  from_character TEXT NOT NULL REFERENCES character(uuid),
  to_character TEXT NOT NULL REFERENCES character(uuid),
  rel_type TEXT NOT NULL, description TEXT, scope_note TEXT, claim_uuid TEXT REFERENCES entity(uuid)
);

-- ---------- 3. Evidence and footage ----------
CREATE TABLE asset (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  original_filename TEXT NOT NULL, storage_uri TEXT NOT NULL,
  sha256 TEXT NOT NULL UNIQUE, size_bytes INTEGER NOT NULL, media_type TEXT,
  duration_ticks INTEGER, width INTEGER, height INTEGER, video_codec TEXT, bitrate INTEGER,
  fps_num INTEGER, fps_den INTEGER, is_vfr INTEGER,
  color_primaries TEXT, color_transfer TEXT, color_matrix TEXT, hdr TEXT,
  audio_json TEXT, subtitle_json TEXT, language TEXT,
  edition_uuid TEXT REFERENCES edition(uuid),
  parent_asset_uuid TEXT REFERENCES asset(uuid), transform_note TEXT,
  asset_role TEXT NOT NULL DEFAULT 'original' CHECK (asset_role IN ('original','intermediate','proxy','export','audio','still','test'))
);
-- Piecewise asset-time → edition-time mapping (handles intros, ad breaks, missing sections).
CREATE TABLE asset_edition_map (asset_uuid TEXT NOT NULL REFERENCES asset(uuid), edition_uuid TEXT NOT NULL REFERENCES edition(uuid), asset_start INTEGER NOT NULL, asset_end INTEGER NOT NULL, edition_start INTEGER NOT NULL, note TEXT, CHECK (asset_end > asset_start), PRIMARY KEY (asset_uuid, edition_uuid, asset_start));
CREATE TABLE counting_method (version TEXT PRIMARY KEY, description TEXT NOT NULL);
CREATE TABLE annotation_set (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), asset_uuid TEXT NOT NULL REFERENCES asset(uuid), version INTEGER NOT NULL, status TEXT NOT NULL CHECK (status IN ('draft','active','superseded')), counting_method TEXT REFERENCES counting_method(version), UNIQUE (asset_uuid, version));
CREATE TABLE coverage (annotation_set_uuid TEXT NOT NULL REFERENCES annotation_set(uuid), start_ticks INTEGER NOT NULL, end_ticks INTEGER NOT NULL, reviewed_by TEXT NOT NULL, at TEXT NOT NULL, CHECK (end_ticks > start_ticks));
CREATE TABLE transcript (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), asset_uuid TEXT NOT NULL REFERENCES asset(uuid), language TEXT NOT NULL, kind TEXT NOT NULL CHECK (kind IN ('machine','subtitle_track','human')), version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE segment (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), transcript_uuid TEXT NOT NULL REFERENCES transcript(uuid), start_ticks INTEGER NOT NULL, end_ticks INTEGER NOT NULL, text TEXT NOT NULL, speaker_label TEXT, speaker_character TEXT REFERENCES character(uuid), confidence REAL, review_status TEXT NOT NULL DEFAULT 'machine' CHECK (review_status IN ('machine','human_confirmed','human_corrected')), CHECK (end_ticks > start_ticks));
CREATE TABLE scene (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), annotation_set_uuid TEXT NOT NULL REFERENCES annotation_set(uuid), start_ticks INTEGER NOT NULL, end_ticks INTEGER NOT NULL, location TEXT, story_time TEXT, synopsis TEXT, spoiler_level TEXT, sensitive_json TEXT, confidence TEXT, review_status TEXT NOT NULL DEFAULT 'proposed' CHECK (review_status IN ('proposed','human_confirmed')), CHECK (end_ticks > start_ticks));
CREATE TABLE shot (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), scene_uuid TEXT NOT NULL REFERENCES scene(uuid), start_ticks INTEGER NOT NULL, end_ticks INTEGER NOT NULL, review_status TEXT NOT NULL DEFAULT 'proposed' CHECK (review_status IN ('proposed','human_confirmed')), CHECK (end_ticks > start_ticks));
CREATE TABLE appearance (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  character_uuid TEXT NOT NULL REFERENCES character(uuid),
  portrayal_uuid TEXT REFERENCES portrayal(uuid),
  annotation_set_uuid TEXT NOT NULL REFERENCES annotation_set(uuid),
  scene_uuid TEXT REFERENCES scene(uuid), shot_uuid TEXT REFERENCES shot(uuid),
  start_ticks INTEGER NOT NULL, end_ticks INTEGER NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('visible','speaking_on_screen','voice_offscreen','archival','depiction','mention')),
  identity_status TEXT NOT NULL CHECK (identity_status IN ('Confirmed','Probable','Unresolved')),
  review_status TEXT NOT NULL DEFAULT 'proposed' CHECK (review_status IN ('proposed','human_confirmed')),
  evidence TEXT, CHECK (end_ticks > start_ticks)
);
CREATE TABLE reference_image (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), subject_uuid TEXT NOT NULL REFERENCES entity(uuid), kind TEXT NOT NULL CHECK (kind IN ('actor_headshot','in_character_frame','archival_photo')), asset_uuid TEXT REFERENCES asset(uuid), frame_ticks INTEGER, source_url TEXT, permission_status TEXT NOT NULL DEFAULT 'Unknown', internal_only INTEGER NOT NULL DEFAULT 1, notes TEXT);
CREATE TABLE source (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), title TEXT NOT NULL, author TEXT, url TEXT, file_ref TEXT, pub_date TEXT, access_date TEXT, source_type TEXT NOT NULL, archive_url TEXT, reliability_note TEXT);
CREATE TABLE claim (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  text TEXT NOT NULL, subject_uuid TEXT REFERENCES entity(uuid),
  domain TEXT NOT NULL CHECK (domain IN ('series','production','actor','history','casting')),
  claim_class TEXT NOT NULL DEFAULT 'fact' CHECK (claim_class IN ('fact','quote','paraphrase','allegation','opinion','dramatization')),
  status TEXT NOT NULL DEFAULT 'unchecked' CHECK (status IN ('unchecked','supported','supported_single_source','disputed','conflicting','refuted')),
  notes TEXT, checked_at TEXT
);
CREATE TABLE claim_evidence (claim_uuid TEXT NOT NULL REFERENCES claim(uuid), source_uuid TEXT NOT NULL REFERENCES source(uuid), stance TEXT NOT NULL CHECK (stance IN ('supports','conflicts','context')), locator TEXT, added_at TEXT NOT NULL, PRIMARY KEY (claim_uuid, source_uuid, stance));
CREATE TABLE rights (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid),
  covers_uuid TEXT REFERENCES entity(uuid), asset_description TEXT NOT NULL,
  asset_class TEXT NOT NULL CHECK (asset_class IN ('footage','photo','music','voice','likeness','font','other')),
  holder TEXT, evidence TEXT, platforms_json TEXT, territories TEXT, starts TEXT, expires TEXT,
  monetization TEXT, derivative_terms TEXT, attribution TEXT,
  status TEXT NOT NULL DEFAULT 'Unknown' CHECK (status IN ('Unknown','Under review','Documented permission','Documented restriction')),
  conditions TEXT
);

-- ---------- 4. Editorial production ----------
CREATE TABLE concept (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), title TEXT NOT NULL, premise TEXT, format TEXT, hypothesis TEXT, audience TEXT, focus_json TEXT);
CREATE TABLE project (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), concept_uuid TEXT REFERENCES concept(uuid), title TEXT NOT NULL, slug TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'Researching' CHECK (status IN ('Researching','Indexed','Proposed','Approved for edit','Rendered','Checked','Approved for publication')),
  cost_estimate TEXT, cost_actual TEXT);
CREATE TABLE timeline (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), project_uuid TEXT NOT NULL REFERENCES project(uuid), approach TEXT NOT NULL CHECK (approach IN ('performance_led','narrated')), status TEXT NOT NULL DEFAULT 'draft');
CREATE TABLE timeline_item (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid), timeline_uuid TEXT NOT NULL REFERENCES timeline(uuid),
  seq INTEGER NOT NULL, track TEXT NOT NULL, kind TEXT NOT NULL CHECK (kind IN ('source','narration','text','music','graphic','label','watermark')),
  source_uuid TEXT REFERENCES entity(uuid), src_start INTEGER, src_end INTEGER,
  tl_start INTEGER NOT NULL, tl_end INTEGER NOT NULL, chrono_order INTEGER,
  layout TEXT, audio_note TEXT, caption_ref TEXT, content TEXT, line_type TEXT CHECK (line_type IN ('original_dialogue','editorial_interpretation','verified_history',NULL)),
  CHECK (tl_end > tl_start), CHECK (src_start IS NULL OR src_end > src_start)
);
CREATE TABLE script (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), project_uuid TEXT NOT NULL REFERENCES project(uuid), approach TEXT NOT NULL, body_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'draft');
CREATE TABLE voice (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), owner TEXT NOT NULL, kind TEXT NOT NULL CHECK (kind IN ('recorded','digital')), service TEXT, consent_ref TEXT, status TEXT NOT NULL DEFAULT 'not_supplied');
CREATE TABLE take (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), script_uuid TEXT NOT NULL REFERENCES script(uuid), script_rev INTEGER NOT NULL, voice_uuid TEXT NOT NULL REFERENCES voice(uuid), origin TEXT NOT NULL, settings_json TEXT, audio_asset_uuid TEXT REFERENCES asset(uuid), duration_ticks INTEGER);
CREATE TABLE export (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid), project_uuid TEXT NOT NULL REFERENCES project(uuid),
  timeline_uuid TEXT REFERENCES timeline(uuid), timeline_rev INTEGER, take_uuid TEXT REFERENCES take(uuid),
  platform TEXT NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL, variant TEXT NOT NULL CHECK (variant IN ('captioned','clean','master_srcfps')),
  language TEXT NOT NULL, subtitle_ref TEXT, settings_json TEXT, file_uri TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE
);
-- Approvals are bound to an exact revision. Separate review kinds; no single "approved" flag.
CREATE TABLE review (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid), target_uuid TEXT NOT NULL REFERENCES entity(uuid), target_rev INTEGER NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('identity','history','rights','sensitivity','editorial','technical_qc','publication')),
  decision TEXT NOT NULL CHECK (decision IN ('approved','rejected','needs_changes')),
  reviewer TEXT NOT NULL, notes TEXT, at TEXT NOT NULL,
  valid INTEGER NOT NULL DEFAULT 1, invalidated_reason TEXT
);
CREATE TABLE dependency (upstream_uuid TEXT NOT NULL REFERENCES entity(uuid), downstream_uuid TEXT NOT NULL REFERENCES entity(uuid), kind TEXT, PRIMARY KEY (upstream_uuid, downstream_uuid));
CREATE TABLE stale_flag (id INTEGER PRIMARY KEY, downstream_uuid TEXT NOT NULL REFERENCES entity(uuid), upstream_uuid TEXT NOT NULL REFERENCES entity(uuid), upstream_rev INTEGER NOT NULL, change TEXT NOT NULL, at TEXT NOT NULL, resolved INTEGER NOT NULL DEFAULT 0);

-- ---------- 5. Distribution and results ----------
CREATE TABLE packaging (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid), project_uuid TEXT NOT NULL REFERENCES project(uuid),
  export_uuid TEXT REFERENCES export(uuid), export_rev INTEGER, platform TEXT NOT NULL, language TEXT NOT NULL,
  primary_phrase TEXT, related_json TEXT, intent TEXT, hooks_json TEXT, recommended_hook TEXT, cover_headline TEXT,
  title TEXT, caption TEXT, hashtags_json TEXT, mentions_json TEXT, pinned_comment TEXT, sources_json TEXT, hypothesis TEXT,
  provisional INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE account (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), platform TEXT NOT NULL, handle TEXT, verified INTEGER NOT NULL DEFAULT 0, owner TEXT);
CREATE TABLE post (
  uuid TEXT PRIMARY KEY REFERENCES entity(uuid), account_uuid TEXT NOT NULL REFERENCES account(uuid), export_uuid TEXT NOT NULL REFERENCES export(uuid),
  packaging_uuid TEXT REFERENCES packaging(uuid), platform_post_id TEXT, url TEXT,
  published_title TEXT, published_caption TEXT, published_hashtags TEXT, published_at TEXT, timezone TEXT,
  approval_review_uuid TEXT NOT NULL REFERENCES review(uuid)
);
CREATE TABLE metric (uuid TEXT PRIMARY KEY REFERENCES entity(uuid), post_uuid TEXT NOT NULL REFERENCES post(uuid), observed_at TEXT NOT NULL, name TEXT NOT NULL, value REAL, kind TEXT NOT NULL CHECK (kind IN ('observed','derived','predicted')), source TEXT);

-- ---------- Controlled tags ----------
CREATE TABLE tag (tag TEXT PRIMARY KEY, meaning TEXT NOT NULL);
CREATE TABLE entity_tag (entity_uuid TEXT NOT NULL REFERENCES entity(uuid), tag TEXT NOT NULL REFERENCES tag(tag), PRIMARY KEY (entity_uuid, tag));

CREATE INDEX ix_app_char ON appearance(character_uuid);
CREATE INDEX ix_dep_up ON dependency(upstream_uuid);
CREATE INDEX ix_review_target ON review(target_uuid);
