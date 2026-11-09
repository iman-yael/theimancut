# Data dictionary

> Generated 2026-11-09T00:58:13Z from the live schema (migrations: 001_init, 002_crew_credit, 003_counting_method_cm1, 004_controlled_tags).


## `account`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| platform | TEXT | yes |  |  |
| handle | TEXT |  |  |  |
| verified | INTEGER | yes | 0 |  |
| owner | TEXT |  |  |  |

## `annotation_set`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| asset_uuid | TEXT | yes |  | → asset.uuid |
| version | INTEGER | yes |  |  |
| status | TEXT | yes |  |  |
| counting_method | TEXT |  |  | → counting_method.version |

Constraints: CHECK status IN ('draft','active','superseded'); UNIQUE (asset_uuid, version)

## `appearance`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| character_uuid | TEXT | yes |  | → character.uuid |
| portrayal_uuid | TEXT |  |  | → portrayal.uuid |
| annotation_set_uuid | TEXT | yes |  | → annotation_set.uuid |
| scene_uuid | TEXT |  |  | → scene.uuid |
| shot_uuid | TEXT |  |  | → shot.uuid |
| start_ticks | INTEGER | yes |  |  |
| end_ticks | INTEGER | yes |  |  |
| mode | TEXT | yes |  |  |
| identity_status | TEXT | yes |  |  |
| review_status | TEXT | yes | 'proposed' |  |
| evidence | TEXT |  |  |  |

Constraints: CHECK mode IN ('visible','speaking_on_screen','voice_offscreen','archival','depiction','mention'); CHECK identity_status IN ('Confirmed','Probable','Unresolved'); CHECK review_status IN ('proposed','human_confirmed'); CHECK end_ticks > start_ticks

## `asset`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| original_filename | TEXT | yes |  |  |
| storage_uri | TEXT | yes |  |  |
| sha256 | TEXT | yes |  |  |
| size_bytes | INTEGER | yes |  |  |
| media_type | TEXT |  |  |  |
| duration_ticks | INTEGER |  |  |  |
| width | INTEGER |  |  |  |
| height | INTEGER |  |  |  |
| video_codec | TEXT |  |  |  |
| bitrate | INTEGER |  |  |  |
| fps_num | INTEGER |  |  |  |
| fps_den | INTEGER |  |  |  |
| is_vfr | INTEGER |  |  |  |
| color_primaries | TEXT |  |  |  |
| color_transfer | TEXT |  |  |  |
| color_matrix | TEXT |  |  |  |
| hdr | TEXT |  |  |  |
| audio_json | TEXT |  |  |  |
| subtitle_json | TEXT |  |  |  |
| language | TEXT |  |  |  |
| edition_uuid | TEXT |  |  | → edition.uuid |
| parent_asset_uuid | TEXT |  |  | → asset.uuid |
| transform_note | TEXT |  |  |  |
| asset_role | TEXT | yes | 'original' |  |

Constraints: CHECK asset_role IN ('original','intermediate','proxy','export','audio','still','test')

## `asset_edition_map`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| asset_uuid | TEXT | yes |  | PK → asset.uuid |
| edition_uuid | TEXT | yes |  | PK → edition.uuid |
| asset_start | INTEGER | yes |  | PK  |
| asset_end | INTEGER | yes |  |  |
| edition_start | INTEGER | yes |  |  |
| note | TEXT |  |  |  |

Constraints: CHECK asset_end > asset_start

## `audit_log`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| id | INTEGER | yes |  | PK  |
| at | TEXT | yes |  |  |
| actor | TEXT | yes |  |  |
| action | TEXT | yes |  |  |
| entity_uuid | TEXT |  |  |  |
| detail | TEXT |  |  |  |

## `character`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| work_uuid | TEXT | yes |  | → work.uuid |
| credited_name | TEXT | yes |  |  |
| norm_name | TEXT | yes |  |  |
| counterpart_status | TEXT | yes | 'unconfirmed' |  |
| relationship_to_subject | TEXT |  |  |  |
| profile_json | TEXT |  |  |  |
| notes | TEXT |  |  |  |

Constraints: CHECK counterpart_status IN ('real_person','fictional','composite','disputed','unconfirmed')

## `character_name`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| character_uuid | TEXT | yes |  | PK → character.uuid |
| name | TEXT | yes |  |  |
| norm_name | TEXT | yes |  | PK  |
| kind | TEXT | yes |  | PK  |
| verification | TEXT | yes | 'supplied' |  |
| source | TEXT |  |  |  |

## `claim`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| text | TEXT | yes |  |  |
| subject_uuid | TEXT |  |  | → entity.uuid |
| domain | TEXT | yes |  |  |
| claim_class | TEXT | yes | 'fact' |  |
| status | TEXT | yes | 'unchecked' |  |
| notes | TEXT |  |  |  |
| checked_at | TEXT |  |  |  |

Constraints: CHECK domain IN ('series','production','actor','history','casting'); CHECK claim_class IN ('fact','quote','paraphrase','allegation','opinion','dramatization'); CHECK status IN ('unchecked','supported','supported_single_source','disputed','conflicting','refuted')

## `claim_evidence`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| claim_uuid | TEXT | yes |  | PK → claim.uuid |
| source_uuid | TEXT | yes |  | PK → source.uuid |
| stance | TEXT | yes |  | PK  |
| locator | TEXT |  |  |  |
| added_at | TEXT | yes |  |  |

Constraints: CHECK stance IN ('supports','conflicts','context')

## `concept`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| title | TEXT | yes |  |  |
| premise | TEXT |  |  |  |
| format | TEXT |  |  |  |
| hypothesis | TEXT |  |  |  |
| audience | TEXT |  |  |  |
| focus_json | TEXT |  |  |  |

## `counting_method`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| version | TEXT | yes |  | PK  |
| description | TEXT | yes |  |  |

## `coverage`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| annotation_set_uuid | TEXT | yes |  | → annotation_set.uuid |
| start_ticks | INTEGER | yes |  |  |
| end_ticks | INTEGER | yes |  |  |
| reviewed_by | TEXT | yes |  |  |
| at | TEXT | yes |  |  |

Constraints: CHECK end_ticks > start_ticks

## `crew_credit`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| work_uuid | TEXT | yes |  | PK → work.uuid |
| person_uuid | TEXT | yes |  | PK → person.uuid |
| department | TEXT | yes |  | PK  |
| role_verbatim | TEXT | yes |  | PK  |
| credited_episode_count | INTEGER |  |  |  |
| doubles_for_person | TEXT |  |  | → person.uuid |
| ingestion_uuid | TEXT |  |  | → entity.uuid |

## `dependency`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| upstream_uuid | TEXT | yes |  | PK → entity.uuid |
| downstream_uuid | TEXT | yes |  | PK → entity.uuid |
| kind | TEXT |  |  |  |

## `edition`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| installment_uuid | TEXT | yes |  | → installment.uuid |
| name | TEXT | yes |  |  |
| region | TEXT |  |  |  |
| runtime_ticks | INTEGER |  |  |  |
| notes | TEXT |  |  |  |

## `entity`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK  |
| display_id | TEXT | yes |  |  |
| type | TEXT | yes |  |  |
| rev | INTEGER | yes | 1 |  |
| created_at | TEXT | yes |  |  |
| updated_at | TEXT | yes |  |  |
| retired_to | TEXT |  |  | → entity.uuid |
| retired_reason | TEXT |  |  |  |

## `entity_tag`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| entity_uuid | TEXT | yes |  | PK → entity.uuid |
| tag | TEXT | yes |  | PK → tag.tag |

## `export`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| project_uuid | TEXT | yes |  | → project.uuid |
| timeline_uuid | TEXT |  |  | → timeline.uuid |
| timeline_rev | INTEGER |  |  |  |
| take_uuid | TEXT |  |  | → take.uuid |
| platform | TEXT | yes |  |  |
| width | INTEGER | yes |  |  |
| height | INTEGER | yes |  |  |
| variant | TEXT | yes |  |  |
| language | TEXT | yes |  |  |
| subtitle_ref | TEXT |  |  |  |
| settings_json | TEXT |  |  |  |
| file_uri | TEXT | yes |  |  |
| sha256 | TEXT | yes |  |  |

Constraints: CHECK variant IN ('captioned','clean','master_srcfps')

## `external_id`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| entity_uuid | TEXT | yes |  | → entity.uuid |
| provider | TEXT | yes |  | PK  |
| value | TEXT | yes |  | PK  |

## `historical_link`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| character_uuid | TEXT | yes |  | → character.uuid |
| person_uuid | TEXT |  |  | → person.uuid |
| link_type | TEXT | yes |  |  |
| claim_uuid | TEXT |  |  | → entity.uuid |

Constraints: CHECK link_type IN ('depicts','composite_of','inspired_by','disputed','none_known'); UNIQUE (character_uuid, person_uuid, link_type)

## `id_counter`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| prefix | TEXT | yes |  | PK  |
| next_value | INTEGER | yes |  |  |

## `ingestion`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| kind | TEXT | yes |  |  |
| original_name | TEXT | yes |  |  |
| stored_path | TEXT | yes |  |  |
| sha256 | TEXT | yes |  |  |
| provenance | TEXT | yes |  |  |
| received_at | TEXT | yes |  |  |
| report_json | TEXT |  |  |  |

Constraints: UNIQUE (kind, sha256)

## `installment`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| work_uuid | TEXT | yes |  | → work.uuid |
| season_uuid | TEXT |  |  | → season.uuid |
| kind | TEXT | yes |  |  |
| title | TEXT |  |  |  |
| synopsis | TEXT |  |  |  |
| spoiler_level | TEXT |  |  |  |

Constraints: CHECK kind IN ('episode','feature','special','short','other')

## `installment_number`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| installment_uuid | TEXT | yes |  | PK → installment.uuid |
| scheme | TEXT | yes |  | PK  |
| label | TEXT | yes |  |  |
| ordinal | INTEGER |  |  |  |

## `meta`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| key | TEXT | yes |  | PK  |
| value | TEXT | yes |  |  |

## `metric`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| post_uuid | TEXT | yes |  | → post.uuid |
| observed_at | TEXT | yes |  |  |
| name | TEXT | yes |  |  |
| value | REAL |  |  |  |
| kind | TEXT | yes |  |  |
| source | TEXT |  |  |  |

Constraints: CHECK kind IN ('observed','derived','predicted')

## `packaging`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| project_uuid | TEXT | yes |  | → project.uuid |
| export_uuid | TEXT |  |  | → export.uuid |
| export_rev | INTEGER |  |  |  |
| platform | TEXT | yes |  |  |
| language | TEXT | yes |  |  |
| primary_phrase | TEXT |  |  |  |
| related_json | TEXT |  |  |  |
| intent | TEXT |  |  |  |
| hooks_json | TEXT |  |  |  |
| recommended_hook | TEXT |  |  |  |
| cover_headline | TEXT |  |  |  |
| title | TEXT |  |  |  |
| caption | TEXT |  |  |  |
| hashtags_json | TEXT |  |  |  |
| mentions_json | TEXT |  |  |  |
| pinned_comment | TEXT |  |  |  |
| sources_json | TEXT |  |  |  |
| hypothesis | TEXT |  |  |  |
| provisional | INTEGER | yes | 1 |  |

## `person`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| name | TEXT | yes |  |  |
| norm_name | TEXT | yes |  |  |
| born | TEXT |  |  |  |
| died | TEXT |  |  |  |
| bio_actor | TEXT |  |  |  |
| bio_historical | TEXT |  |  |  |
| notes | TEXT |  |  |  |

## `person_name`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| person_uuid | TEXT | yes |  | PK → person.uuid |
| name | TEXT | yes |  |  |
| norm_name | TEXT | yes |  | PK  |
| kind | TEXT | yes |  | PK  |
| claim_uuid | TEXT |  |  | → entity.uuid |

## `portrayal`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| character_uuid | TEXT | yes |  | → character.uuid |
| person_uuid | TEXT | yes |  | → person.uuid |
| age_portrayal | TEXT | yes | 'primary' |  |
| voice_only | INTEGER | yes | 0 |  |
| credit_status | TEXT | yes | 'credited' |  |
| credit_verification | TEXT | yes | 'supplied' |  |
| credited_episode_count | INTEGER |  |  |  |
| notes | TEXT |  |  |  |

Constraints: CHECK credit_status IN ('credited','uncredited','unknown'); UNIQUE (character_uuid, person_uuid, age_portrayal)

## `portrayal_credit_name`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| portrayal_uuid | TEXT | yes |  | PK → portrayal.uuid |
| credited_character_name | TEXT | yes |  | PK  |
| credited_actor_name | TEXT | yes |  | PK  |
| ingestion_uuid | TEXT |  |  | → entity.uuid |

## `portrayal_installment`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| portrayal_uuid | TEXT | yes |  | PK → portrayal.uuid |
| installment_uuid | TEXT | yes |  | PK → installment.uuid |
| source | TEXT |  |  |  |

## `post`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| account_uuid | TEXT | yes |  | → account.uuid |
| export_uuid | TEXT | yes |  | → export.uuid |
| packaging_uuid | TEXT |  |  | → packaging.uuid |
| platform_post_id | TEXT |  |  |  |
| url | TEXT |  |  |  |
| published_title | TEXT |  |  |  |
| published_caption | TEXT |  |  |  |
| published_hashtags | TEXT |  |  |  |
| published_at | TEXT |  |  |  |
| timezone | TEXT |  |  |  |
| approval_review_uuid | TEXT | yes |  | → review.uuid |

## `project`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| concept_uuid | TEXT |  |  | → concept.uuid |
| title | TEXT | yes |  |  |
| slug | TEXT | yes |  |  |
| status | TEXT | yes | 'Researching' |  |
| cost_estimate | TEXT |  |  |  |
| cost_actual | TEXT |  |  |  |

Constraints: CHECK status IN ('Researching','Indexed','Proposed','Approved for edit','Rendered','Checked','Approved for publication')

## `provenance`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| entity_uuid | TEXT | yes |  | → entity.uuid |
| field | TEXT | yes |  |  |
| value | TEXT |  |  |  |
| ingestion_uuid | TEXT |  |  | → entity.uuid |
| source_uuid | TEXT |  |  | → entity.uuid |
| at | TEXT | yes |  |  |

## `reference_image`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| subject_uuid | TEXT | yes |  | → entity.uuid |
| kind | TEXT | yes |  |  |
| asset_uuid | TEXT |  |  | → asset.uuid |
| frame_ticks | INTEGER |  |  |  |
| source_url | TEXT |  |  |  |
| permission_status | TEXT | yes | 'Unknown' |  |
| internal_only | INTEGER | yes | 1 |  |
| notes | TEXT |  |  |  |

Constraints: CHECK kind IN ('actor_headshot','in_character_frame','archival_photo')

## `relationship`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| from_character | TEXT | yes |  | → character.uuid |
| to_character | TEXT | yes |  | → character.uuid |
| rel_type | TEXT | yes |  |  |
| description | TEXT |  |  |  |
| scope_note | TEXT |  |  |  |
| claim_uuid | TEXT |  |  | → entity.uuid |

## `release_date`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| entity_uuid | TEXT | yes |  | PK → entity.uuid |
| region | TEXT | yes |  | PK  |
| date | TEXT | yes |  |  |
| platform | TEXT | yes |  | PK  |

## `review`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| target_uuid | TEXT | yes |  | → entity.uuid |
| target_rev | INTEGER | yes |  |  |
| kind | TEXT | yes |  |  |
| decision | TEXT | yes |  |  |
| reviewer | TEXT | yes |  |  |
| notes | TEXT |  |  |  |
| at | TEXT | yes |  |  |
| valid | INTEGER | yes | 1 |  |
| invalidated_reason | TEXT |  |  |  |

Constraints: CHECK kind IN ('identity','history','rights','sensitivity','editorial','technical_qc','publication'); CHECK decision IN ('approved','rejected','needs_changes')

## `review_queue`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| id | INTEGER | yes |  | PK  |
| ingestion_uuid | TEXT |  |  | → entity.uuid |
| kind | TEXT | yes |  |  |
| payload_json | TEXT | yes |  |  |
| candidates_json | TEXT |  |  |  |
| status | TEXT | yes | 'open' |  |
| resolution | TEXT |  |  |  |

Constraints: CHECK status IN ('open','resolved','dismissed'); UNIQUE (kind, payload_json)

## `revision`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| entity_uuid | TEXT | yes |  | PK → entity.uuid |
| rev | INTEGER | yes |  | PK  |
| snapshot_json | TEXT | yes |  |  |
| changed_fields | TEXT |  |  |  |
| ingestion_uuid | TEXT |  |  | → entity.uuid |
| actor | TEXT | yes |  |  |
| note | TEXT |  |  |  |
| at | TEXT | yes |  |  |

## `rights`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| covers_uuid | TEXT |  |  | → entity.uuid |
| asset_description | TEXT | yes |  |  |
| asset_class | TEXT | yes |  |  |
| holder | TEXT |  |  |  |
| evidence | TEXT |  |  |  |
| platforms_json | TEXT |  |  |  |
| territories | TEXT |  |  |  |
| starts | TEXT |  |  |  |
| expires | TEXT |  |  |  |
| monetization | TEXT |  |  |  |
| derivative_terms | TEXT |  |  |  |
| attribution | TEXT |  |  |  |
| status | TEXT | yes | 'Unknown' |  |
| conditions | TEXT |  |  |  |

Constraints: CHECK asset_class IN ('footage','photo','music','voice','likeness','font','other'); CHECK status IN ('Unknown','Under review','Documented permission','Documented restriction')

## `scene`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| annotation_set_uuid | TEXT | yes |  | → annotation_set.uuid |
| start_ticks | INTEGER | yes |  |  |
| end_ticks | INTEGER | yes |  |  |
| location | TEXT |  |  |  |
| story_time | TEXT |  |  |  |
| synopsis | TEXT |  |  |  |
| spoiler_level | TEXT |  |  |  |
| sensitive_json | TEXT |  |  |  |
| confidence | TEXT |  |  |  |
| review_status | TEXT | yes | 'proposed' |  |

Constraints: CHECK review_status IN ('proposed','human_confirmed'); CHECK end_ticks > start_ticks

## `schema_migration`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| version | TEXT | yes |  | PK  |
| applied_at | TEXT | yes |  |  |

## `script`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| project_uuid | TEXT | yes |  | → project.uuid |
| approach | TEXT | yes |  |  |
| body_json | TEXT | yes |  |  |
| status | TEXT | yes | 'draft' |  |

## `season`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| work_uuid | TEXT | yes |  | → work.uuid |
| label | TEXT | yes |  |  |
| ordinal | INTEGER |  |  |  |

## `segment`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| transcript_uuid | TEXT | yes |  | → transcript.uuid |
| start_ticks | INTEGER | yes |  |  |
| end_ticks | INTEGER | yes |  |  |
| text | TEXT | yes |  |  |
| speaker_label | TEXT |  |  |  |
| speaker_character | TEXT |  |  | → character.uuid |
| confidence | REAL |  |  |  |
| review_status | TEXT | yes | 'machine' |  |

Constraints: CHECK review_status IN ('machine','human_confirmed','human_corrected'); CHECK end_ticks > start_ticks

## `shot`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| scene_uuid | TEXT | yes |  | → scene.uuid |
| start_ticks | INTEGER | yes |  |  |
| end_ticks | INTEGER | yes |  |  |
| review_status | TEXT | yes | 'proposed' |  |

Constraints: CHECK review_status IN ('proposed','human_confirmed'); CHECK end_ticks > start_ticks

## `source`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| title | TEXT | yes |  |  |
| author | TEXT |  |  |  |
| url | TEXT |  |  |  |
| file_ref | TEXT |  |  |  |
| pub_date | TEXT |  |  |  |
| access_date | TEXT |  |  |  |
| source_type | TEXT | yes |  |  |
| archive_url | TEXT |  |  |  |
| reliability_note | TEXT |  |  |  |

## `stale_flag`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| id | INTEGER | yes |  | PK  |
| downstream_uuid | TEXT | yes |  | → entity.uuid |
| upstream_uuid | TEXT | yes |  | → entity.uuid |
| upstream_rev | INTEGER | yes |  |  |
| change | TEXT | yes |  |  |
| at | TEXT | yes |  |  |
| resolved | INTEGER | yes | 0 |  |

## `tag`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| tag | TEXT | yes |  | PK  |
| meaning | TEXT | yes |  |  |

## `take`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| script_uuid | TEXT | yes |  | → script.uuid |
| script_rev | INTEGER | yes |  |  |
| voice_uuid | TEXT | yes |  | → voice.uuid |
| origin | TEXT | yes |  |  |
| settings_json | TEXT |  |  |  |
| audio_asset_uuid | TEXT |  |  | → asset.uuid |
| duration_ticks | INTEGER |  |  |  |

## `timeline`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| project_uuid | TEXT | yes |  | → project.uuid |
| approach | TEXT | yes |  |  |
| status | TEXT | yes | 'draft' |  |

Constraints: CHECK approach IN ('performance_led','narrated')

## `timeline_item`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| timeline_uuid | TEXT | yes |  | → timeline.uuid |
| seq | INTEGER | yes |  |  |
| track | TEXT | yes |  |  |
| kind | TEXT | yes |  |  |
| source_uuid | TEXT |  |  | → entity.uuid |
| src_start | INTEGER |  |  |  |
| src_end | INTEGER |  |  |  |
| tl_start | INTEGER | yes |  |  |
| tl_end | INTEGER | yes |  |  |
| chrono_order | INTEGER |  |  |  |
| layout | TEXT |  |  |  |
| audio_note | TEXT |  |  |  |
| caption_ref | TEXT |  |  |  |
| content | TEXT |  |  |  |
| line_type | TEXT |  |  |  |

Constraints: CHECK kind IN ('source','narration','text','music','graphic','label','watermark'); CHECK line_type IN ('original_dialogue','editorial_interpretation','verified_history',NULL); CHECK tl_end > tl_start; CHECK src_start IS NULL OR src_end > src_start

## `transcript`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| asset_uuid | TEXT | yes |  | → asset.uuid |
| language | TEXT | yes |  |  |
| kind | TEXT | yes |  |  |
| version | INTEGER | yes | 1 |  |

Constraints: CHECK kind IN ('machine','subtitle_track','human')

## `voice`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| owner | TEXT | yes |  |  |
| kind | TEXT | yes |  |  |
| service | TEXT |  |  |  |
| consent_ref | TEXT |  |  |  |
| status | TEXT | yes | 'not_supplied' |  |

Constraints: CHECK kind IN ('recorded','digital')

## `work`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| uuid | TEXT | yes |  | PK → entity.uuid |
| title | TEXT | yes |  |  |
| work_type | TEXT | yes |  |  |
| first_release | TEXT |  |  |  |
| notes | TEXT |  |  |  |

Constraints: CHECK work_type IN ('series','limited_series','movie','documentary','documentary_series','special','short','other')

## `work_title`
| Column | Type | Required | Default | Key / reference |
|---|---|---|---|---|
| work_uuid | TEXT | yes |  | PK → work.uuid |
| title | TEXT | yes |  | PK  |
| language | TEXT | yes |  | PK  |
| region | TEXT | yes |  | PK  |
| kind | TEXT |  |  |  |
