# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MetaHub Test is a FastAPI-based metadata management system that provides REST APIs for managing taxonomies, codesets, and custom meta types. It uses SQLAlchemy with async support and SQLite for data persistence.

## Development Commands

### Environment Setup
- Uses `uv` as the package manager - dependencies are locked in `uv.lock`
- Virtual environment is in `.venv/` directory
- Python 3.11+ required

### Database Migrations (Alembic)
```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "Description of changes"

# Apply migrations to database
alembic upgrade head

# Rollback to previous migration
alembic downgrade -1

# Check current migration status
alembic current

# View migration history
alembic history

# Rollback to beginning (drop all tables)
alembic downgrade base
```

### Running the Application
```bash
# Development server with auto-reload
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Alternative using the main module
python -m app.main
```

### Testing
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test types
pytest tests/unit/
pytest tests/integration/
pytest tests/api/
```

### Code Quality
```bash
# Linting and formatting
ruff check                    # Lint code
ruff format                   # Format code (similar to black)

# Type checking
mypy app/                     # Type check the app package

# Format with black (if preferred)
black app/ tests/
```

## Architecture

### Core Structure
- **`app/main.py`**: FastAPI application entry point with startup event handlers
- **`app/core/`**: Configuration and dependency injection
- **`app/db/`**: Database session management and SQLAlchemy setup
- **`app/models/`**: SQLAlchemy ORM models for database entities
- **`app/schemas/`**: Pydantic models for API request/response validation
- **`app/api/v1/`**: REST API route handlers organized by resource
- **`app/services/`**: Business logic layer between API routes and database

### Database Architecture
- Uses SQLAlchemy 2.0+ with async support (`AsyncSession`)
- SQLite database with aiosqlite driver (`sqlite+aiosqlite:///./test.db`)
- **Alembic Migrations**: Database schema managed via Alembic migrations
- **Hybrid Architecture**: Combines database flexibility with code-based type safety
- Models support hierarchical taxonomies and flexible metadata types

#### 🎯 Meta Type Architecture (2-Level Clean Structure)
- **MetaTypeKind**: 4 basic data types (PRIMITIVE, STRING, CODESET, TAXONOMY)
- **Meta Items**: Database entities with direct `type_kind` reference
- **Meta Values**: Database-managed with type validation
- **Benefits**: Simple, clear structure; better performance; Git-based versioning

### API Structure
All API endpoints are under `/api/v1/` prefix:
- `/health` - Health check endpoint
- `/taxonomy` - Taxonomy management (database-managed)
- `/codeset` - Codeset operations (database-managed)
- `/meta/types` - 🎯 Basic meta type kinds (PRIMITIVE, STRING, CODESET, TAXONOMY)
- `/meta/groups` - Meta group management (database-managed)
- `/meta/items` - Meta item management (database-managed with code validation)
- `/meta-values` - Metadata value management with Spring @Transactional style
- `/bootstrap` - Data initialization and seeding

### Key Patterns
- **Async/await**: All database operations and API handlers are asynchronous
- **Dependency Injection**: Uses FastAPI's dependency system for database sessions
- **Spring @Transactional Style**: Transaction management with `@transactional` decorator
- **Repository Pattern**: Clean separation of data access layer
- **🎯 Clean Meta Type System**: 2-level architecture with direct type_kind references
- **Settings Management**: Environment-based configuration with Pydantic Settings
- **Error Handling**: Structured exception handling throughout the application
- **Type Safety**: Full type annotations with mypy configuration

### Testing Strategy
- **Unit Tests**: Service layer and utility function testing
- **API Tests**: Endpoint validation and response testing
- **Integration Tests**: Full application workflow testing including performance and security
- Uses pytest with asyncio support for async test functions

## 🎯 Recent Architecture Updates (2025-09)

### Meta Type System Simplification
Successfully simplified the meta type architecture from confusing 3-level to clean 2-level structure:

#### Before (Confusing 3-Level)
```
MetaTypeKind (PRIMITIVE, STRING, CODESET, TAXONOMY)
    ↓
SYSTEM_META_TYPES (RETENTION_DAYS, TABLE_DESCRIPTION...) ← Unnecessary middle layer
    ↓  
SYSTEM_META_ITEMS (retention_days, table_description...)
```

#### After (Clean 2-Level) 🎉
```
MetaTypeKind (PRIMITIVE, STRING, CODESET, TAXONOMY) ← True Meta Types
    ↓
SYSTEM_META_ITEMS (direct type_kind reference) ← Actual Meta Items
```

**Key Benefits:**
- **Conceptually Clear**: Meta Type vs Meta Item distinction
- **Better Performance**: No unnecessary intermediate layer
- **Simpler API**: `/meta/types` returns 4 basic types, `/meta/items` returns actual items
- **Database Cleanup**: Removed 3 unused tables (custom_meta_type, custom_meta_type_codeset, custom_meta_type_taxonomy)

### Updated API Responses
**`GET /api/v1/meta/types`** now returns only basic type kinds:
```json
[
  {"type_code": "PRIMITIVE", "name": "Primitive"},
  {"type_code": "STRING", "name": "String"},
  {"type_code": "CODESET", "name": "Codeset"},
  {"type_code": "TAXONOMY", "name": "Taxonomy"}
]
```

**`GET /api/v1/meta/items`** returns actual metadata items:
```json
[
  {"item_code": "retention_days", "type_kind": "PRIMITIVE"},
  {"item_code": "table_description", "type_kind": "STRING"},
  {"item_code": "pii_level", "type_kind": "CODESET"},
  {"item_code": "domain", "type_kind": "TAXONOMY"}
]
```

### Spring @Transactional Style Transaction Management
Implemented Spring-style transaction management:

```python
@transactional()                              # REQUIRED (default)
@transactional(read_only=True)                # READ_ONLY  
@transactional(propagation="requires_new")    # Independent transaction
@transactional(propagation="nested")          # Savepoint nesting
```

### Repository Pattern Implementation
Clean architecture with separation of concerns:
- **Repository**: Pure data access (no business logic)
- **Service**: Business logic with `@transactional` 
- **API**: Presentation layer with dependency injection

### STRING Meta Type Support
Added STRING meta type with JSON wrapping:
```json
{"value": "actual string content"}
```

## 🛠️ Development Notes

### Meta Type Development
- **Basic Types**: MetaTypeKind enum is fixed (PRIMITIVE, STRING, CODESET, TAXONOMY)
- **New Items**: Add to `SYSTEM_META_ITEMS` in `app/core/meta_types.py`
- **Type Safety**: Use `MetaTypeKind` enum for type validation
- **Database**: Items use direct `type_kind` string reference
- **API**: Items can be created via `/meta/items` endpoint

### Transaction Management
- Use `@transactional()` decorator on service methods
- Context propagation handled automatically via contextvars
- Compatible with FastAPI, batch jobs, and tests
- Automatic commit/rollback based on success/failure

### Database Schema
- Current ERD: Upload `metahub_schema.dbml` to https://dbdiagram.io
- 7 tables (down from 10) - removed meta type tables
- Better performance with fewer JOINs