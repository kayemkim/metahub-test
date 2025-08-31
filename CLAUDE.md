# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MetaHub Test is a FastAPI-based metadata management system that provides REST APIs for managing taxonomies, codesets, and custom meta types. It uses SQLAlchemy with async support and SQLite for data persistence.

## Development Commands

### Environment Setup
- Uses `uv` as the package manager - dependencies are locked in `uv.lock`
- Virtual environment is in `.venv/` directory
- Python 3.11+ required

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
- Database tables created automatically on application startup
- Models support hierarchical taxonomies and flexible metadata types

### API Structure
All API endpoints are under `/api/v1/` prefix:
- `/health` - Health check endpoint
- `/taxonomy` - Taxonomy management
- `/codeset` - Codeset operations
- `/meta-types` - Custom metadata type definitions
- `/meta-values` - Metadata value management
- `/bootstrap` - Data initialization and seeding

### Key Patterns
- **Async/await**: All database operations and API handlers are asynchronous
- **Dependency Injection**: Uses FastAPI's dependency system for database sessions
- **Settings Management**: Environment-based configuration with Pydantic Settings
- **Error Handling**: Structured exception handling throughout the application
- **Type Safety**: Full type annotations with mypy configuration

### Testing Strategy
- **Unit Tests**: Service layer and utility function testing
- **API Tests**: Endpoint validation and response testing
- **Integration Tests**: Full application workflow testing including performance and security
- Uses pytest with asyncio support for async test functions