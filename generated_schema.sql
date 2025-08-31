-- Generated DDL from SQLAlchemy Models
-- Use this file to visualize ERD in PyCharm or other IDEs


CREATE TABLE cm_codeset (
	codeset_id VARCHAR(36) NOT NULL, 
	codeset_code VARCHAR(100) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (codeset_id), 
	UNIQUE (codeset_code)
)




CREATE TABLE custom_meta_group (
	group_id VARCHAR(36) NOT NULL, 
	group_code VARCHAR(100) NOT NULL, 
	display_name VARCHAR(200) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (group_id), 
	UNIQUE (group_code)
)




CREATE TABLE tx_taxonomy (
	taxonomy_id VARCHAR(36) NOT NULL, 
	taxonomy_code VARCHAR(100) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	description TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (taxonomy_id), 
	UNIQUE (taxonomy_code)
)




CREATE TABLE cm_code (
	code_id VARCHAR(36) NOT NULL, 
	codeset_id VARCHAR(36) NOT NULL, 
	code_key VARCHAR(150) NOT NULL, 
	current_version_id VARCHAR(36), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (code_id), 
	CONSTRAINT uq_code_key_per_set UNIQUE (codeset_id, code_key), 
	FOREIGN KEY(codeset_id) REFERENCES cm_codeset (codeset_id)
)




CREATE TABLE custom_meta_item (
	item_id VARCHAR(36) NOT NULL, 
	item_code VARCHAR(150) NOT NULL, 
	display_name VARCHAR(200) NOT NULL, 
	group_id VARCHAR(36) NOT NULL, 
	type_kind VARCHAR(30) NOT NULL, 
	is_required BOOLEAN NOT NULL, 
	default_json TEXT, 
	selection_mode VARCHAR(10) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (item_id), 
	UNIQUE (item_code), 
	FOREIGN KEY(group_id) REFERENCES custom_meta_group (group_id)
)




CREATE TABLE tx_term (
	term_id VARCHAR(36) NOT NULL, 
	taxonomy_id VARCHAR(36) NOT NULL, 
	term_key VARCHAR(150) NOT NULL, 
	display_name VARCHAR(200) NOT NULL, 
	parent_term_id VARCHAR(36), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (term_id), 
	CONSTRAINT uq_term_key_per_taxonomy UNIQUE (taxonomy_id, term_key), 
	FOREIGN KEY(taxonomy_id) REFERENCES tx_taxonomy (taxonomy_id), 
	FOREIGN KEY(parent_term_id) REFERENCES tx_term (term_id)
)




CREATE TABLE cm_code_version (
	code_version_id VARCHAR(36) NOT NULL, 
	code_id VARCHAR(36) NOT NULL, 
	version_no INTEGER NOT NULL, 
	label_default VARCHAR(200) NOT NULL, 
	sort_order INTEGER NOT NULL, 
	parent_code_id VARCHAR(36), 
	valid_from DATETIME NOT NULL, 
	valid_to DATETIME, 
	tx_time DATETIME NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	extra_json TEXT, 
	PRIMARY KEY (code_version_id), 
	CONSTRAINT uq_code_version_no UNIQUE (code_id, version_no), 
	FOREIGN KEY(code_id) REFERENCES cm_code (code_id), 
	FOREIGN KEY(parent_code_id) REFERENCES cm_code (code_id)
)




CREATE TABLE custom_meta_value (
	value_id VARCHAR(36) NOT NULL, 
	target_type VARCHAR(50) NOT NULL, 
	target_id VARCHAR(200) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	current_version_id VARCHAR(36), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (value_id), 
	CONSTRAINT uq_value_target_item UNIQUE (target_type, target_id, item_id), 
	FOREIGN KEY(item_id) REFERENCES custom_meta_item (item_id)
)




CREATE TABLE tx_term_content (
	content_id VARCHAR(36) NOT NULL, 
	term_id VARCHAR(36) NOT NULL, 
	current_version_id VARCHAR(36), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (content_id), 
	UNIQUE (term_id), 
	FOREIGN KEY(term_id) REFERENCES tx_term (term_id)
)




CREATE TABLE custom_meta_value_version (
	version_id VARCHAR(36) NOT NULL, 
	value_id VARCHAR(36) NOT NULL, 
	version_no INTEGER NOT NULL, 
	value_json TEXT, 
	code_id VARCHAR(36), 
	taxonomy_term_id VARCHAR(36), 
	valid_from DATETIME NOT NULL, 
	valid_to DATETIME, 
	tx_time DATETIME NOT NULL, 
	author VARCHAR(200), 
	reason VARCHAR(1000), 
	PRIMARY KEY (version_id), 
	CONSTRAINT uq_value_version_no UNIQUE (value_id, version_no), 
	FOREIGN KEY(value_id) REFERENCES custom_meta_value (value_id), 
	FOREIGN KEY(code_id) REFERENCES cm_code (code_id), 
	FOREIGN KEY(taxonomy_term_id) REFERENCES tx_term (term_id)
)




CREATE TABLE tx_term_content_version (
	content_version_id VARCHAR(36) NOT NULL, 
	content_id VARCHAR(36) NOT NULL, 
	version_no INTEGER NOT NULL, 
	body_json TEXT, 
	body_markdown TEXT, 
	tx_time DATETIME NOT NULL, 
	valid_from DATETIME NOT NULL, 
	valid_to DATETIME, 
	author VARCHAR(200), 
	change_reason VARCHAR(1000), 
	PRIMARY KEY (content_version_id), 
	CONSTRAINT uq_term_content_version_no UNIQUE (content_id, version_no), 
	FOREIGN KEY(content_id) REFERENCES tx_term_content (content_id)
)




CREATE TABLE custom_meta_value_version_term (
	version_id VARCHAR(36) NOT NULL, 
	term_id VARCHAR(36) NOT NULL, 
	PRIMARY KEY (version_id, term_id), 
	FOREIGN KEY(version_id) REFERENCES custom_meta_value_version (version_id), 
	FOREIGN KEY(term_id) REFERENCES tx_term (term_id)
)

