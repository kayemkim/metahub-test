-- Database Schema for MetaHub Test Application
-- This file contains the complete database schema that can be used to visualize ERD in PyCharm

-- Taxonomy Domain Tables
CREATE TABLE tx_taxonomy (
    taxonomy_id VARCHAR(36) PRIMARY KEY,
    taxonomy_code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tx_term (
    term_id VARCHAR(36) PRIMARY KEY,
    taxonomy_id VARCHAR(36) NOT NULL,
    term_key VARCHAR(150) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    parent_term_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_term_taxonomy FOREIGN KEY (taxonomy_id) REFERENCES tx_taxonomy(taxonomy_id),
    CONSTRAINT fk_term_parent FOREIGN KEY (parent_term_id) REFERENCES tx_term(term_id),
    CONSTRAINT uq_term_key_per_taxonomy UNIQUE (taxonomy_id, term_key)
);

CREATE TABLE tx_term_content (
    content_id VARCHAR(36) PRIMARY KEY,
    term_id VARCHAR(36) UNIQUE NOT NULL,
    current_version_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_term_content_term FOREIGN KEY (term_id) REFERENCES tx_term(term_id)
);

CREATE TABLE tx_term_content_version (
    content_version_id VARCHAR(36) PRIMARY KEY,
    content_id VARCHAR(36) NOT NULL,
    version_no INTEGER NOT NULL,
    body_json TEXT,
    body_markdown TEXT,
    tx_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP WITH TIME ZONE,
    author VARCHAR(200),
    change_reason VARCHAR(1000),
    
    CONSTRAINT fk_term_content_version_content FOREIGN KEY (content_id) REFERENCES tx_term_content(content_id),
    CONSTRAINT uq_term_content_version_no UNIQUE (content_id, version_no)
);

-- CodeSet Domain Tables
CREATE TABLE cm_codeset (
    codeset_id VARCHAR(36) PRIMARY KEY,
    codeset_code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cm_code (
    code_id VARCHAR(36) PRIMARY KEY,
    codeset_id VARCHAR(36) NOT NULL,
    code_key VARCHAR(150) NOT NULL,
    current_version_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_code_codeset FOREIGN KEY (codeset_id) REFERENCES cm_codeset(codeset_id),
    CONSTRAINT uq_code_key_per_set UNIQUE (codeset_id, code_key)
);

CREATE TABLE cm_code_version (
    code_version_id VARCHAR(36) PRIMARY KEY,
    code_id VARCHAR(36) NOT NULL,
    version_no INTEGER NOT NULL,
    label_default VARCHAR(200) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    parent_code_id VARCHAR(36),
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP WITH TIME ZONE,
    tx_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    extra_json TEXT,
    
    CONSTRAINT fk_code_version_code FOREIGN KEY (code_id) REFERENCES cm_code(code_id),
    CONSTRAINT fk_code_version_parent FOREIGN KEY (parent_code_id) REFERENCES cm_code(code_id),
    CONSTRAINT uq_code_version_no UNIQUE (code_id, version_no)
);

-- Custom Meta Type System
CREATE TABLE custom_meta_type (
    type_id VARCHAR(36) PRIMARY KEY,
    type_code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    type_kind VARCHAR(30) DEFAULT 'PRIMITIVE', -- PRIMITIVE|CODESET|TAXONOMY
    schema_json TEXT, -- validation rules for PRIMITIVE
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE custom_meta_group (
    group_id VARCHAR(36) PRIMARY KEY,
    group_code VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE custom_meta_item (
    item_id VARCHAR(36) PRIMARY KEY,
    item_code VARCHAR(150) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    group_id VARCHAR(36) NOT NULL,
    type_id VARCHAR(36) NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,
    default_json TEXT,
    selection_mode VARCHAR(10) DEFAULT 'SINGLE', -- SINGLE|MULTI (TAXONOMY only)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_meta_item_group FOREIGN KEY (group_id) REFERENCES custom_meta_group(group_id),
    CONSTRAINT fk_meta_item_type FOREIGN KEY (type_id) REFERENCES custom_meta_type(type_id)
);

-- Meta Type Link Tables
CREATE TABLE custom_meta_type_codeset (
    type_id VARCHAR(36) PRIMARY KEY,
    codeset_id VARCHAR(36) NOT NULL,
    
    CONSTRAINT fk_meta_type_codeset_type FOREIGN KEY (type_id) REFERENCES custom_meta_type(type_id),
    CONSTRAINT fk_meta_type_codeset_codeset FOREIGN KEY (codeset_id) REFERENCES cm_codeset(codeset_id)
);

CREATE TABLE custom_meta_type_taxonomy (
    type_id VARCHAR(36) PRIMARY KEY,
    taxonomy_id VARCHAR(36) NOT NULL,
    
    CONSTRAINT fk_meta_type_taxonomy_type FOREIGN KEY (type_id) REFERENCES custom_meta_type(type_id),
    CONSTRAINT fk_meta_type_taxonomy_taxonomy FOREIGN KEY (taxonomy_id) REFERENCES tx_taxonomy(taxonomy_id)
);

-- Meta Value Storage
CREATE TABLE custom_meta_value (
    value_id VARCHAR(36) PRIMARY KEY,
    target_type VARCHAR(50) NOT NULL, -- 'table','column','job', etc.
    target_id VARCHAR(200) NOT NULL,
    item_id VARCHAR(36) NOT NULL,
    current_version_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_meta_value_item FOREIGN KEY (item_id) REFERENCES custom_meta_item(item_id),
    CONSTRAINT uq_value_target_item UNIQUE (target_type, target_id, item_id)
);

CREATE TABLE custom_meta_value_version (
    version_id VARCHAR(36) PRIMARY KEY,
    value_id VARCHAR(36) NOT NULL,
    version_no INTEGER NOT NULL,
    
    -- PRIMITIVE payload
    value_json TEXT,
    
    -- CODESET payload (single)
    code_id VARCHAR(36),
    
    -- TAXONOMY payload (single)
    taxonomy_term_id VARCHAR(36),
    
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    valid_to TIMESTAMP WITH TIME ZONE,
    tx_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    author VARCHAR(200),
    reason VARCHAR(1000),
    
    CONSTRAINT fk_meta_value_version_value FOREIGN KEY (value_id) REFERENCES custom_meta_value(value_id),
    CONSTRAINT fk_meta_value_version_code FOREIGN KEY (code_id) REFERENCES cm_code(code_id),
    CONSTRAINT fk_meta_value_version_term FOREIGN KEY (taxonomy_term_id) REFERENCES tx_term(term_id),
    CONSTRAINT uq_value_version_no UNIQUE (value_id, version_no)
);

-- Multi-term taxonomy values (for MULTI selection mode)
CREATE TABLE custom_meta_value_version_term (
    version_id VARCHAR(36),
    term_id VARCHAR(36),
    
    PRIMARY KEY (version_id, term_id),
    CONSTRAINT fk_meta_value_version_term_version FOREIGN KEY (version_id) REFERENCES custom_meta_value_version(version_id),
    CONSTRAINT fk_meta_value_version_term_term FOREIGN KEY (term_id) REFERENCES tx_term(term_id)
);

-- Indexes for better performance
CREATE INDEX ix_term_taxonomy_id ON tx_term(taxonomy_id);
CREATE INDEX ix_term_parent_term_id ON tx_term(parent_term_id);
CREATE INDEX ix_term_content_version_content_id ON tx_term_content_version(content_id);

CREATE INDEX ix_code_codeset_id ON cm_code(codeset_id);
CREATE INDEX ix_code_version_code_id ON cm_code_version(code_id);

CREATE INDEX ix_meta_value_target ON custom_meta_value(target_type, target_id);
CREATE INDEX ix_meta_value_version_value_id ON custom_meta_value_version(value_id);

-- Comments for better understanding
COMMENT ON TABLE tx_taxonomy IS 'Taxonomy definitions - hierarchical classification systems';
COMMENT ON TABLE tx_term IS 'Terms within taxonomies - supports parent-child relationships';
COMMENT ON TABLE tx_term_content IS 'Content management for terms';
COMMENT ON TABLE tx_term_content_version IS 'Version history for term content';

COMMENT ON TABLE cm_codeset IS 'Code set definitions - controlled vocabularies';
COMMENT ON TABLE cm_code IS 'Codes within code sets - supports hierarchical structure';
COMMENT ON TABLE cm_code_version IS 'Version history for codes with labels and metadata';

COMMENT ON TABLE custom_meta_type IS 'Meta type definitions - PRIMITIVE, CODESET, or TAXONOMY types';
COMMENT ON TABLE custom_meta_group IS 'Logical grouping for meta items';
COMMENT ON TABLE custom_meta_item IS 'Meta item definitions - actual metadata fields';
COMMENT ON TABLE custom_meta_value IS 'Meta value instances - applied to target entities';
COMMENT ON TABLE custom_meta_value_version IS 'Version history for meta values';

-- Sample data for testing ERD visualization
INSERT INTO tx_taxonomy (taxonomy_id, taxonomy_code, name, description) VALUES
('tax1', 'DATA_DOMAIN', 'Data Domain', 'Business data domains'),
('tax2', 'SYSTEM_TYPE', 'System Type', 'Types of systems');

INSERT INTO cm_codeset (codeset_id, codeset_code, name, description) VALUES
('cs1', 'PII_LEVEL', 'PII Level', 'Personal Information Sensitivity Levels'),
('cs2', 'DATA_CLASS', 'Data Classification', 'Data classification levels');

INSERT INTO custom_meta_group (group_id, group_code, display_name) VALUES
('grp1', 'BUSINESS', 'Business Information'),
('grp2', 'TECHNICAL', 'Technical Information');

INSERT INTO custom_meta_type (type_id, type_code, name, type_kind) VALUES
('type1', 'TEXT_TYPE', 'Text Field', 'PRIMITIVE'),
('type2', 'PII_TYPE', 'PII Classification', 'CODESET'),
('type3', 'DOMAIN_TYPE', 'Domain Classification', 'TAXONOMY');