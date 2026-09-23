-- Offline Alembic SQL through revision 0010_unconditional_base_rates.
-- Not applied. No Postgres connection. POSTGRES_DSN was unset.
-- Rendered by alembic.command.upgrade(..., sql=True), which uses
-- packages/memory/src/mm_memory/migrations/env.py run_migrations_offline.
-- `lab migrate` on this branch has no --sql flag; this file is that
-- offline render stopped before 0011.
-- 0011 calls inspect(bind) and raises NoInspectionAvailable on Alembic's
-- MockConnection, so head (0012_heartbeat_if_not_exists) is not in this file.
-- 0011 and 0012 DDL is quoted from the revision files in
-- ops/reports/persistence/2026-09-23-neon-migrate-head-schema.md.
-- PR #105 (open, not merged) adds `lab migrate --sql-out` and rewrites
-- 0011/0012. That SQL is a different revision text and is not copied here.

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_phase1

CREATE TABLE source (
    id VARCHAR(26) NOT NULL, 
    name TEXT NOT NULL, 
    kind VARCHAR(32) NOT NULL, 
    base_url TEXT, 
    trust_tier INTEGER DEFAULT '3' NOT NULL, 
    tos_notes TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT source_kind_check CHECK (kind IN ('exchange','onchain','macro','news','internal')), 
    CONSTRAINT source_name_key UNIQUE (name)
);

CREATE TABLE raw_object (
    id VARCHAR(26) NOT NULL, 
    bucket TEXT NOT NULL, 
    object_key TEXT NOT NULL, 
    checksum_sha256 VARCHAR(64) NOT NULL, 
    content_type TEXT, 
    byte_size BIGINT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT raw_object_bucket_key_uidx UNIQUE (bucket, object_key)
);

CREATE TABLE observation (
    id VARCHAR(26) NOT NULL, 
    source_id VARCHAR(26) NOT NULL, 
    source_url_or_id TEXT, 
    published_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    ingested_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    market_time TIMESTAMP WITH TIME ZONE, 
    claim_text TEXT NOT NULL, 
    claim_hash VARCHAR(64) NOT NULL, 
    identity_hash VARCHAR(64) NOT NULL, 
    confidence NUMERIC(4, 3) NOT NULL, 
    evidence_type VARCHAR(32) NOT NULL, 
    data_quality VARCHAR(32) DEFAULT 'ok' NOT NULL, 
    payload_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    raw_object_key TEXT, 
    raw_object_checksum VARCHAR(64), 
    as_of_knowledge TIMESTAMP WITH TIME ZONE NOT NULL, 
    instrument TEXT NOT NULL, 
    metric TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT observation_evidence_type_check CHECK (evidence_type IN ('fact','quote','metric','commentary','derived')), 
    CONSTRAINT observation_data_quality_check CHECK (data_quality IN ('ok','stale','partial','contradicted','rejected')), 
    CONSTRAINT observation_confidence_check CHECK (confidence >= 0 AND confidence <= 1), 
    CONSTRAINT observation_claim_hash_uidx UNIQUE (claim_hash), 
    FOREIGN KEY(source_id) REFERENCES source (id)
);

CREATE INDEX observation_ingested_at_idx ON observation (ingested_at);

CREATE INDEX observation_market_time_idx ON observation (market_time);

CREATE INDEX observation_source_id_idx ON observation (source_id);

CREATE INDEX observation_identity_hash_idx ON observation (identity_hash);

CREATE INDEX observation_identity_idx ON observation (source_id, instrument, metric, market_time);

CREATE TABLE observation_link (
    id SERIAL NOT NULL, 
    observation_id VARCHAR(26) NOT NULL, 
    related_observation_id VARCHAR(26) NOT NULL, 
    relation VARCHAR(32) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT observation_link_relation_check CHECK (relation IN ('supports','contradicts','duplicate','updates')), 
    CONSTRAINT observation_link_no_self CHECK (observation_id <> related_observation_id), 
    CONSTRAINT observation_link_unique UNIQUE (observation_id, related_observation_id, relation), 
    FOREIGN KEY(observation_id) REFERENCES observation (id), 
    FOREIGN KEY(related_observation_id) REFERENCES observation (id)
);

CREATE INDEX observation_link_observation_id_idx ON observation_link (observation_id);

CREATE INDEX observation_link_related_idx ON observation_link (related_observation_id);

INSERT INTO alembic_version (version_num) VALUES ('0001_phase1') RETURNING alembic_version.version_num;

-- Running upgrade 0001_phase1 -> 0002_phase2

CREATE TABLE thesis (
    id VARCHAR(26) NOT NULL, 
    slug TEXT NOT NULL, 
    status VARCHAR(32) NOT NULL, 
    author_role TEXT DEFAULT 'Research' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    artifact_git_path TEXT NOT NULL, 
    artifact_content_hash VARCHAR(64) NOT NULL, 
    instrument TEXT, 
    horizon TEXT, 
    invalidation_summary TEXT, 
    risk_budget_bps INTEGER, 
    PRIMARY KEY (id), 
    CONSTRAINT thesis_status_check CHECK (status IN ('draft','in_research','in_skeptic','paper','live','rejected','retired')), 
    CONSTRAINT thesis_slug_key UNIQUE (slug)
);

CREATE INDEX thesis_status_idx ON thesis (status);

CREATE TABLE thesis_evidence (
    id SERIAL NOT NULL, 
    thesis_id VARCHAR(26) NOT NULL, 
    observation_id VARCHAR(26) NOT NULL, 
    role VARCHAR(32) NOT NULL, 
    notes TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT thesis_evidence_role_check CHECK (role IN ('supports','opposes','context')), 
    CONSTRAINT thesis_evidence_unique UNIQUE (thesis_id, observation_id, role), 
    FOREIGN KEY(thesis_id) REFERENCES thesis (id), 
    FOREIGN KEY(observation_id) REFERENCES observation (id)
);

CREATE INDEX thesis_evidence_thesis_id_idx ON thesis_evidence (thesis_id);

CREATE INDEX thesis_evidence_observation_id_idx ON thesis_evidence (observation_id);

CREATE TABLE skeptic_review (
    id VARCHAR(26) NOT NULL, 
    thesis_id VARCHAR(26) NOT NULL, 
    reviewer_id_or_role TEXT NOT NULL, 
    verdict VARCHAR(32) NOT NULL, 
    findings_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    artifact_git_path TEXT NOT NULL, 
    content_hash VARCHAR(64) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT skeptic_review_verdict_check CHECK (verdict IN ('pass','revise','reject')), 
    FOREIGN KEY(thesis_id) REFERENCES thesis (id)
);

CREATE INDEX skeptic_review_thesis_id_idx ON skeptic_review (thesis_id);

UPDATE alembic_version SET version_num='0002_phase2' WHERE alembic_version.version_num = '0001_phase1';

-- Running upgrade 0002_phase2 -> 0003_phase3

CREATE TABLE brief (
    id VARCHAR(26) NOT NULL, 
    kind VARCHAR(32) NOT NULL, 
    session_date DATE NOT NULL, 
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    as_of_knowledge TIMESTAMP WITH TIME ZONE NOT NULL, 
    artifact_git_path TEXT NOT NULL, 
    content_hash VARCHAR(64) NOT NULL, 
    data_quality VARCHAR(32) NOT NULL, 
    payload_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT brief_kind_check CHECK (kind IN ('preopen','close','alert')), 
    CONSTRAINT brief_data_quality_check CHECK (data_quality IN ('ok','stale','partial','contradicted','rejected')), 
    CONSTRAINT brief_kind_session_hash_uidx UNIQUE (kind, session_date, content_hash)
);

CREATE INDEX brief_session_date_idx ON brief (session_date);

CREATE INDEX brief_kind_idx ON brief (kind);

UPDATE alembic_version SET version_num='0003_phase3' WHERE alembic_version.version_num = '0002_phase2';

-- Running upgrade 0003_phase3 -> 0004_phase4

CREATE TABLE research_run (
    id VARCHAR(26) NOT NULL, 
    thesis_id VARCHAR(26), 
    kind VARCHAR(32) NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    finished_at TIMESTAMP WITH TIME ZONE, 
    params_hash VARCHAR(64) NOT NULL, 
    result_summary JSONB DEFAULT '{}'::jsonb NOT NULL, 
    artifact_paths JSONB DEFAULT '[]'::jsonb NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT research_run_kind_check CHECK (kind IN ('scan','backtest','manual')), 
    FOREIGN KEY(thesis_id) REFERENCES thesis (id)
);

CREATE INDEX research_run_thesis_id_idx ON research_run (thesis_id);

CREATE INDEX research_run_params_hash_idx ON research_run (params_hash);

CREATE INDEX research_run_kind_idx ON research_run (kind);

CREATE TABLE paper_trade (
    id VARCHAR(26) NOT NULL, 
    thesis_id VARCHAR(26) NOT NULL, 
    opened_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    closed_at TIMESTAMP WITH TIME ZONE, 
    status VARCHAR(32) DEFAULT 'open' NOT NULL, 
    instrument TEXT NOT NULL, 
    size TEXT NOT NULL, 
    invalidation TEXT NOT NULL, 
    max_loss TEXT NOT NULL, 
    max_loss_amount NUMERIC(20, 8) NOT NULL, 
    intent_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    fills_json JSONB DEFAULT '[]'::jsonb NOT NULL, 
    expected_path JSONB DEFAULT '[]'::jsonb NOT NULL, 
    realised_path JSONB DEFAULT '[]'::jsonb NOT NULL, 
    pnl NUMERIC(20, 8), 
    slippage_bps NUMERIC(12, 4), 
    exit_reason TEXT, 
    notes TEXT, 
    artifact_git_path TEXT NOT NULL, 
    entry_thesis_snapshot_hash VARCHAR(64) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT paper_trade_status_check CHECK (status IN ('open','closed')), 
    CONSTRAINT paper_trade_invalidation_check CHECK (length(btrim(invalidation)) > 0), 
    CONSTRAINT paper_trade_max_loss_check CHECK (length(btrim(max_loss)) > 0), 
    CONSTRAINT paper_trade_max_loss_amount_check CHECK (max_loss_amount > 0), 
    FOREIGN KEY(thesis_id) REFERENCES thesis (id)
);

CREATE INDEX paper_trade_thesis_id_idx ON paper_trade (thesis_id);

CREATE INDEX paper_trade_status_idx ON paper_trade (status);

UPDATE alembic_version SET version_num='0004_phase4' WHERE alembic_version.version_num = '0003_phase3';

-- Running upgrade 0004_phase4 -> 0005_knowledge_lockstep

ALTER TABLE observation ADD CONSTRAINT observation_as_of_knowledge_eq_ingested_at CHECK (as_of_knowledge = ingested_at);

CREATE INDEX observation_as_of_knowledge_idx ON observation (as_of_knowledge);

UPDATE alembic_version SET version_num='0005_knowledge_lockstep' WHERE alembic_version.version_num = '0004_phase4';

-- Running upgrade 0005_knowledge_lockstep -> 0006_phase5a_status_events

CREATE TABLE thesis_status_event (
    id VARCHAR(26) NOT NULL, 
    thesis_id VARCHAR(26) NOT NULL, 
    from_status VARCHAR(32) NOT NULL, 
    to_status VARCHAR(32) NOT NULL, 
    actor TEXT NOT NULL, 
    ts TIMESTAMP WITH TIME ZONE NOT NULL, 
    reason TEXT NOT NULL, 
    risk_decision VARCHAR(32) DEFAULT 'pending' NOT NULL, 
    principal_override BOOLEAN DEFAULT false NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT thesis_status_event_from_status_check CHECK (from_status IN ('draft','in_research','in_skeptic','paper','live','rejected','retired')), 
    CONSTRAINT thesis_status_event_to_status_check CHECK (to_status IN ('draft','in_research','in_skeptic','paper','live','rejected','retired')), 
    CONSTRAINT thesis_status_event_risk_decision_check CHECK (risk_decision IN ('pending','allow','block')), 
    FOREIGN KEY(thesis_id) REFERENCES thesis (id)
);

CREATE INDEX thesis_status_event_thesis_id_idx ON thesis_status_event (thesis_id);

CREATE INDEX thesis_status_event_ts_idx ON thesis_status_event (ts);

UPDATE alembic_version SET version_num='0006_phase5a_status_events' WHERE alembic_version.version_num = '0005_knowledge_lockstep';

-- Running upgrade 0006_phase5a_status_events -> 0007_phase6a_desk_mesh

CREATE TABLE desk_envelope (
    id VARCHAR(26) NOT NULL, 
    desk VARCHAR(32) NOT NULL, 
    channel TEXT NOT NULL, 
    as_of_knowledge TIMESTAMP WITH TIME ZONE NOT NULL, 
    as_of_sydney TEXT NOT NULL, 
    status VARCHAR(16) NOT NULL, 
    n INTEGER NOT NULL, 
    completeness_pct NUMERIC(5, 2) NOT NULL, 
    regime TEXT DEFAULT 'unset' NOT NULL, 
    op VARCHAR(32) NOT NULL, 
    universe TEXT NOT NULL, 
    sources JSONB DEFAULT '[]'::jsonb NOT NULL, 
    missing JSONB DEFAULT '[]'::jsonb NOT NULL, 
    cadence VARCHAR(32) NOT NULL, 
    content_hash VARCHAR(64) NOT NULL, 
    error_class TEXT, 
    body_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    alert_channel TEXT, 
    dq_channel TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT desk_envelope_status_check CHECK (status IN ('OK','DEGRADED','FAILED')), 
    CONSTRAINT desk_envelope_op_check CHECK (op IN ('paper','observation')), 
    CONSTRAINT desk_envelope_error_class_check CHECK (error_class IS NULL OR error_class IN ('desk_missing','desk_killed','desk_error','desk_timeout')), 
    CONSTRAINT desk_envelope_completeness_check CHECK (completeness_pct >= 0 AND completeness_pct <= 100), 
    CONSTRAINT desk_envelope_desk_as_of_hash_uidx UNIQUE (desk, as_of_knowledge, content_hash)
);

CREATE INDEX desk_envelope_desk_as_of_idx ON desk_envelope (desk, as_of_knowledge);

CREATE INDEX desk_envelope_channel_idx ON desk_envelope (channel);

CREATE INDEX desk_envelope_as_of_idx ON desk_envelope (as_of_knowledge);

CREATE TABLE desk_health (
    desk VARCHAR(32) NOT NULL, 
    status VARCHAR(16) NOT NULL, 
    last_as_of TIMESTAMP WITH TIME ZONE, 
    last_envelope_id VARCHAR(26), 
    last_content_hash VARCHAR(64), 
    error_class TEXT, 
    n INTEGER DEFAULT '0' NOT NULL, 
    completeness_pct NUMERIC(5, 2) DEFAULT '0' NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (desk)
);

UPDATE alembic_version SET version_num='0007_phase6a_desk_mesh' WHERE alembic_version.version_num = '0006_phase5a_status_events';

-- Running upgrade 0007_phase6a_desk_mesh -> 0008_phase6c_delivery

CREATE TABLE delivery_event (
    id VARCHAR(26) NOT NULL, 
    desk VARCHAR(64) NOT NULL, 
    as_of_knowledge TIMESTAMP WITH TIME ZONE NOT NULL, 
    content_hash VARCHAR(64) NOT NULL, 
    status VARCHAR(16) NOT NULL, 
    reason TEXT NOT NULL, 
    notes_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT delivery_event_status_check CHECK (status IN ('DRY_RUN','SENT','FAILED','DEDUPE'))
);

CREATE INDEX delivery_event_desk_as_of_idx ON delivery_event (desk, as_of_knowledge);

CREATE INDEX delivery_event_content_hash_idx ON delivery_event (content_hash);

CREATE TABLE inbound_audit (
    id VARCHAR(26) NOT NULL, 
    uid TEXT NOT NULL, 
    command TEXT NOT NULL, 
    action VARCHAR(32) NOT NULL, 
    reason TEXT DEFAULT '' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX inbound_audit_uid_idx ON inbound_audit (uid);

CREATE TABLE llm_call (
    id VARCHAR(26) NOT NULL, 
    run_id VARCHAR(64) NOT NULL, 
    desk_slug VARCHAR(32) NOT NULL, 
    artifact_type VARCHAR(32) NOT NULL, 
    prompt_file TEXT NOT NULL, 
    prompt_hash VARCHAR(64) NOT NULL, 
    model TEXT NOT NULL, 
    model_version TEXT NOT NULL, 
    temperature NUMERIC(4, 3) NOT NULL, 
    input_tokens INTEGER NOT NULL, 
    output_tokens INTEGER NOT NULL, 
    cached_tokens INTEGER DEFAULT '0' NOT NULL, 
    latency_ms NUMERIC(12, 3) DEFAULT '0' NOT NULL, 
    cost NUMERIC(12, 6) DEFAULT '0' NOT NULL, 
    schema_valid BOOLEAN NOT NULL, 
    retry_count INTEGER DEFAULT '0' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX llm_call_run_id_idx ON llm_call (run_id);

CREATE INDEX llm_call_desk_idx ON llm_call (desk_slug);

UPDATE alembic_version SET version_num='0008_phase6c_delivery' WHERE alembic_version.version_num = '0007_phase6a_desk_mesh';

-- Running upgrade 0008_phase6c_delivery -> 0009_phase6d_listings

CREATE TABLE listing_outcome (
    id VARCHAR(26) NOT NULL, 
    instrument TEXT NOT NULL, 
    listing_date VARCHAR(10) NOT NULL, 
    as_of_knowledge TIMESTAMP WITH TIME ZONE NOT NULL, 
    ingested_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    offer_price NUMERIC(20, 8), 
    ret_30d NUMERIC(16, 8), 
    ret_90d NUMERIC(16, 8), 
    reclaimed_offer BOOLEAN, 
    reclaimed_day1_vwap BOOLEAN, 
    observation_id TEXT, 
    payload_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT listing_outcome_as_of_knowledge_eq_ingested_at CHECK (as_of_knowledge = ingested_at)
);

CREATE INDEX listing_outcome_as_of_idx ON listing_outcome (as_of_knowledge);

CREATE INDEX listing_outcome_instrument_idx ON listing_outcome (instrument);

UPDATE alembic_version SET version_num='0009_phase6d_listings' WHERE alembic_version.version_num = '0008_phase6c_delivery';

-- Running upgrade 0009_phase6d_listings -> 0010_unconditional_base_rates

CREATE TABLE event_base_rate (
    id VARCHAR(26) NOT NULL, 
    event_class VARCHAR(32) NOT NULL, 
    as_of_knowledge TIMESTAMP WITH TIME ZONE NOT NULL, 
    ingested_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    params_hash VARCHAR(64) NOT NULL, 
    content_hash VARCHAR(64) NOT NULL, 
    instrument_set JSONB DEFAULT '[]'::jsonb NOT NULL, 
    window_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    cost_model_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    n INTEGER NOT NULL, 
    n_min INTEGER NOT NULL, 
    claimed BOOLEAN DEFAULT false NOT NULL, 
    hit_rate NUMERIC(16, 8), 
    median_fwd_return NUMERIC(16, 8), 
    mean_r_after_cost NUMERIC(16, 8), 
    reason TEXT NOT NULL, 
    cites_candidate VARCHAR(16) NOT NULL, 
    survivorship_tag TEXT NOT NULL, 
    fixture_id TEXT, 
    payload_json JSONB DEFAULT '{}'::jsonb NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT event_base_rate_as_of_knowledge_eq_ingested_at CHECK (as_of_knowledge = ingested_at), 
    CONSTRAINT event_base_rate_event_class_check CHECK (event_class IN ('dip_touch','zone_boundary_touch','pullback_ema_touch')), 
    CONSTRAINT event_base_rate_class_params_as_of_uidx UNIQUE (event_class, params_hash, as_of_knowledge)
);

CREATE INDEX event_base_rate_as_of_idx ON event_base_rate (as_of_knowledge);

CREATE INDEX event_base_rate_params_idx ON event_base_rate (params_hash);

UPDATE alembic_version SET version_num='0010_unconditional_base_rates' WHERE alembic_version.version_num = '0009_phase6d_listings';

COMMIT;

