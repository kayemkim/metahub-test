#!/usr/bin/env python3
"""
ERD Generation Script for MetaHub Database
This script generates database schema files and diagrams for visualization in IDEs
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable
import app.models  # Import all models to register them

def generate_sqlite_db():
    """Generate SQLite database file with actual schema"""
    from app.db.base import Base
    from app.db.session import engine
    import asyncio
    
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    # Create the database with tables
    asyncio.run(create_tables())
    print("✅ SQLite database created: test.db")

def generate_ddl_script():
    """Generate DDL script from SQLAlchemy models"""
    from app.db.base import Base
    
    # Create in-memory SQLite engine for DDL generation
    engine = create_engine("sqlite:///:memory:")
    
    # Generate DDL statements
    ddl_statements = []
    for table in Base.metadata.sorted_tables:
        create_statement = str(CreateTable(table).compile(engine))
        ddl_statements.append(create_statement)
    
    # Write to file
    ddl_content = "-- Generated DDL from SQLAlchemy Models\n"
    ddl_content += "-- Use this file to visualize ERD in PyCharm or other IDEs\n\n"
    ddl_content += "\n\n".join(ddl_statements)
    
    with open("generated_schema.sql", "w") as f:
        f.write(ddl_content)
    
    print("✅ DDL script generated: generated_schema.sql")

def generate_dbml():
    """Generate DBML (Database Markup Language) file for dbdiagram.io"""
    dbml_content = '''
// MetaHub Database Schema in DBML format
// Use at https://dbdiagram.io to generate ERD

Project MetaHub {
  database_type: 'PostgreSQL'
  Note: 'MetaHub - Metadata Management System. Supports Taxonomies, CodeSets, and Custom Meta Types'
}

// Taxonomy Domain
Table tx_taxonomy {
  taxonomy_id varchar(36) [pk]
  taxonomy_code varchar(100) [unique, not null]
  name varchar(200) [not null]
  description text
  created_at timestamp [default: `now()`]
}

Table tx_term {
  term_id varchar(36) [pk]
  taxonomy_id varchar(36) [ref: > tx_taxonomy.taxonomy_id]
  term_key varchar(150) [not null]
  display_name varchar(200) [not null]
  parent_term_id varchar(36) [ref: > tx_term.term_id]
  created_at timestamp [default: `now()`]
  
  indexes {
    (taxonomy_id, term_key) [unique]
  }
}

Table tx_term_content {
  content_id varchar(36) [pk]
  term_id varchar(36) [ref: - tx_term.term_id, unique]
  current_version_id varchar(36)
  created_at timestamp [default: `now()`]
}

Table tx_term_content_version {
  content_version_id varchar(36) [pk]
  content_id varchar(36) [ref: > tx_term_content.content_id]
  version_no integer [not null]
  body_json text
  body_markdown text
  tx_time timestamp [default: `now()`]
  valid_from timestamp [default: `now()`]
  valid_to timestamp
  author varchar(200)
  change_reason varchar(1000)
  
  indexes {
    (content_id, version_no) [unique]
  }
}

// CodeSet Domain
Table cm_codeset {
  codeset_id varchar(36) [pk]
  codeset_code varchar(100) [unique, not null]
  name varchar(200) [not null]
  description text
  created_at timestamp [default: `now()`]
}

Table cm_code {
  code_id varchar(36) [pk]
  codeset_id varchar(36) [ref: > cm_codeset.codeset_id]
  code_key varchar(150) [not null]
  current_version_id varchar(36)
  created_at timestamp [default: `now()`]
  
  indexes {
    (codeset_id, code_key) [unique]
  }
}

Table cm_code_version {
  code_version_id varchar(36) [pk]
  code_id varchar(36) [ref: > cm_code.code_id]
  version_no integer [not null]
  label_default varchar(200) [not null]
  sort_order integer [default: 0]
  parent_code_id varchar(36) [ref: > cm_code.code_id]
  valid_from timestamp [default: `now()`]
  valid_to timestamp
  tx_time timestamp [default: `now()`]
  is_active boolean [default: true]
  extra_json text
  
  indexes {
    (code_id, version_no) [unique]
  }
}

// Custom Meta Types
Table custom_meta_type {
  type_id varchar(36) [pk]
  type_code varchar(100) [unique, not null]
  name varchar(200) [not null]
  type_kind varchar(30) [default: 'PRIMITIVE', note: 'PRIMITIVE|CODESET|TAXONOMY']
  schema_json text [note: 'validation rules for PRIMITIVE']
  created_at timestamp [default: `now()`]
}

Table custom_meta_group {
  group_id varchar(36) [pk]
  group_code varchar(100) [unique, not null]
  display_name varchar(200) [not null]
  sort_order integer [default: 0]
  created_at timestamp [default: `now()`]
}

Table custom_meta_item {
  item_id varchar(36) [pk]
  item_code varchar(150) [unique, not null]
  display_name varchar(200) [not null]
  group_id varchar(36) [ref: > custom_meta_group.group_id]
  type_id varchar(36) [ref: > custom_meta_type.type_id]
  is_required boolean [default: false]
  default_json text
  selection_mode varchar(10) [default: 'SINGLE', note: 'SINGLE|MULTI for TAXONOMY']
  created_at timestamp [default: `now()`]
}

// Meta Type Links
Table custom_meta_type_codeset {
  type_id varchar(36) [pk, ref: - custom_meta_type.type_id]
  codeset_id varchar(36) [ref: > cm_codeset.codeset_id]
}

Table custom_meta_type_taxonomy {
  type_id varchar(36) [pk, ref: - custom_meta_type.type_id]
  taxonomy_id varchar(36) [ref: > tx_taxonomy.taxonomy_id]
}

// Meta Values
Table custom_meta_value {
  value_id varchar(36) [pk]
  target_type varchar(50) [not null, note: 'table, column, job, etc.']
  target_id varchar(200) [not null]
  item_id varchar(36) [ref: > custom_meta_item.item_id]
  current_version_id varchar(36)
  created_at timestamp [default: `now()`]
  
  indexes {
    (target_type, target_id, item_id) [unique]
    (target_type, target_id)
  }
}

Table custom_meta_value_version {
  version_id varchar(36) [pk]
  value_id varchar(36) [ref: > custom_meta_value.value_id]
  version_no integer [not null]
  value_json text [note: 'PRIMITIVE payload']
  code_id varchar(36) [ref: > cm_code.code_id, note: 'CODESET payload']
  taxonomy_term_id varchar(36) [ref: > tx_term.term_id, note: 'TAXONOMY single payload']
  valid_from timestamp [default: `now()`]
  valid_to timestamp
  tx_time timestamp [default: `now()`]
  author varchar(200)
  reason varchar(1000)
  
  indexes {
    (value_id, version_no) [unique]
  }
}

Table custom_meta_value_version_term {
  version_id varchar(36) [pk, ref: > custom_meta_value_version.version_id]
  term_id varchar(36) [pk, ref: > tx_term.term_id]
  
  Note: 'Multi-term taxonomy values for MULTI selection mode'
}
'''
    
    with open("metahub_schema.dbml", "w") as f:
        f.write(dbml_content.strip())
    
    print("✅ DBML file generated: metahub_schema.dbml")
    print("   → Upload to https://dbdiagram.io to generate visual ERD")

def main():
    """Main function to generate all schema artifacts"""
    print("🔧 Generating database schema artifacts...")
    
    try:
        # Generate SQLite database
        generate_sqlite_db()
        
        # Generate DDL script
        generate_ddl_script()
        
        # Generate DBML
        generate_dbml()
        
        print("\n✨ All schema artifacts generated successfully!")
        print("\n📋 How to use:")
        print("1. PyCharm Database Tool: Connect to 'test.db' SQLite file")
        print("2. Visual ERD: Upload 'metahub_schema.dbml' to https://dbdiagram.io")
        print("3. Custom SQL: Use 'database_schema.sql' or 'generated_schema.sql'")
        
    except Exception as e:
        print(f"❌ Error generating schema artifacts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()