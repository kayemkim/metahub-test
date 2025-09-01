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

#### 🆕 UPDATED: Meta Type Management (Code-based)
- **Meta Types**: Defined in `app/core/meta_types.py` (no database storage)
- **Meta Items**: Database-managed with direct `type_kind` storage (no FK to meta_type)
- **Meta Values**: Database-managed with code-based type validation
- **Benefits**: Better type safety, faster operations, Git-based versioning

### API Structure
All API endpoints are under `/api/v1/` prefix:
- `/health` - Health check endpoint
- `/taxonomy` - Taxonomy management (database-managed)
- `/codeset` - Codeset operations (database-managed)
- `/meta/types` - 🆕 Code-based meta type definitions (read-only from code)
- `/meta/groups` - Meta group management (database-managed)
- `/meta/items` - Meta item management (database-managed with code validation)
- `/meta-values` - Metadata value management with Spring @Transactional style
- `/bootstrap` - Data initialization and seeding

### Key Patterns
- **Async/await**: All database operations and API handlers are asynchronous
- **Dependency Injection**: Uses FastAPI's dependency system for database sessions
- **🆕 Spring @Transactional Style**: Transaction management with `@transactional` decorator
- **🆕 Repository Pattern**: Clean separation of data access layer
- **🆕 Code-based Type Management**: Meta types defined as Python enums and dataclasses
- **Settings Management**: Environment-based configuration with Pydantic Settings
- **Error Handling**: Structured exception handling throughout the application
- **Type Safety**: Full type annotations with mypy configuration

### Testing Strategy
- **Unit Tests**: Service layer and utility function testing
- **API Tests**: Endpoint validation and response testing
- **Integration Tests**: Full application workflow testing including performance and security
- Uses pytest with asyncio support for async test functions

## 🆕 Recent Architecture Updates

### Meta Type Management Refactoring
The system was recently refactored from database-driven to **code-driven meta type management**:

#### Before (Database-driven)
```python
# Custom meta types stored in database tables
custom_meta_type
custom_meta_type_codeset  
custom_meta_type_taxonomy
custom_meta_item.type_id -> FK to custom_meta_type
```

#### After (Code-driven) 🎉
```python
# Meta types defined in code
app/core/meta_types.py:
  - MetaTypeKind enum (PRIMITIVE|STRING|CODESET|TAXONOMY)
  - SYSTEM_META_TYPES definitions
  - get_meta_item_type_kind() validation function

custom_meta_item.type_kind -> Direct string storage
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
- Add new meta types in `app/core/meta_types.py`
- Use `MetaTypeKind` enum for type safety
- Update `SYSTEM_META_TYPES` for system-defined types
- No database changes needed for new meta types!

### Transaction Management
- Use `@transactional()` decorator on service methods
- Context propagation handled automatically via contextvars
- Compatible with FastAPI, batch jobs, and tests
- Automatic commit/rollback based on success/failure

### Database Schema
- Current ERD: Upload `metahub_schema.dbml` to https://dbdiagram.io
- 7 tables (down from 10) - removed meta type tables
- Better performance with fewer JOINs