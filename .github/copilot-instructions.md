# DataAlign v2.0 - AI Coding Agent Instructions

## 🏗️ Architecture Overview

DataAlign is a Flask-based file comparison and data alignment application with user-specific access control, Docker deployment, and automated password reset functionality.

**Core Components:**
- **Flask App Factory**: `app/__init__.py` - Uses config-based environments (dev/prod/test)
- **Role-Based Access**: Admin users see all projects, regular users see only their own (`app/routes/projets.py:54-70`)
- **File Processing Pipeline**: Upload → Compare → Generate Excel/PDF/Charts → Archive
- **Multi-Environment Setup**: Development (`docker-compose.dev.yml`), Production (`docker-compose.yml`)

## 🔑 User Authorization Pattern

**Critical Pattern**: All project access is filtered by user role in `app/routes/projets.py`:
```python
if current_user.is_admin():
    projets = Projet.query.order_by(Projet.nom_projet, Projet.date_creation.desc()).all()
else:
    projets = Projet.query.filter_by(user_id=current_user.id).order_by(...)
```

**Decorator Usage**: `@admin_required` from `app/routes/admin.py:12-20` for admin-only routes.

## 🐳 Docker Development Workflow

**Primary Development Setup**: Use `docker-compose.dev.yml` (not `docker-compose.yml`)
- **Ports**: App:5006, MySQL:3307, Adminer:8081, MailHog:8026
- **Build Context**: Uses `Dockerfile.dev` for development
- **Database**: MySQL with user `DataAlign:DataAlign` on `DataAlign_dev` DB

**Automated Scripts**:
- `python docker_start.py` - One-command Docker setup (requires updates for `.dev` files)
- `python deploy.py` - Production deployment automation
- `python maintenance.py` - System health checks and repairs

## 🗄️ Database & Migrations

**Migration Strategy**: Auto-migration controlled by `AUTO_MIGRATION` env var in `app/config.py`
- **Disable Auto**: Set `AUTO_MIGRATION=false` (default in Docker dev)
- **Manual Control**: Use `python bypass_migrations.py` and `python auto_migration.py`
- **Models Location**: `app/models/` - Import all models in `app/__init__.py:42-47`

**Model Relationships**:
- `User.projets` ← → `Projet.owner` (back_populates pattern)
- `Projet.configurations` → `ConfigurationCleComposee` (cascade delete)
- `FichierGenere.projet_id` → `Projet.id` (treatment results)

## 📁 File Processing Architecture

**File Flow**: `uploads/source/` → Processing → `uploads/archive/` → Database records
- **Session State**: File paths stored in Flask session during processing (`app/routes/fichiers.py`)
- **Large Files**: Use `ComparateurFichiersOptimise` for performance (`app/services/comparateur_optimise.py`)
- **Output Generation**: Excel, PDF, and Chart services in `app/services/`

## 🔐 Password Reset System

**Complete Implementation**: Email-less development setup with file logging
- **Token Generation**: `User.generate_reset_token()` in `app/models/user.py`
- **Email Simulation**: Logs to `temp/password_reset_emails.log` in development
- **Admin Management**: `/auth/admin/reset-tokens` route for token oversight
- **Test Script**: `python test_password_reset.py` for system validation

## 🛠️ Development Commands

**Quick Start Options**:
```bash
# Docker (recommended)
python docker_start.py

# Classical setup
python deploy.py && python maintenance.py && python run.py

# Manual troubleshooting
python disable_migrations.py && python bypass_migrations.py && python run.py
```

**Health Checks**: `/health`, `/ready`, `/live` endpoints for monitoring (`app/routes/health.py`)

## 🎯 Common Development Patterns

**Route Structure**: Blueprint-based with consistent decorators
- `@login_required` for authenticated access
- `@admin_required` for admin-only features
- Project permission checks in view functions

**Error Handling**: Try-catch with user flash messages and database rollbacks
**Logging**: `LogExecution` model for system events and admin actions
**File Management**: `app/utils/file_manager.py` for safe file operations

## 🚀 Testing & Validation

**Test Users**: 
- Admin: `testVikinn / admin123` (full access)
- User: `testuser / test123` (own projects only)

**Test Scripts**: 
- `python test_password_reset.py` - Password reset system
- `python create_initial_users.py` - User creation and validation

**Environment URLs**: 
- Development: http://localhost:5006 (Docker) or http://localhost:5004 (local)
- Health: http://localhost:5006/health

## ⚠️ Critical Notes

- **Always use `docker-compose.dev.yml`** for development, not `docker-compose.yml`
- **User filtering is MANDATORY** on all project queries to maintain data isolation
- **File paths must be absolute** due to Docker context differences (`app/routes/projets.py:184-200`)
- **MySQL credentials vary** between environments - check `app/config.py` for current values
- **BuildKit compatibility**: Set `DOCKER_BUILDKIT=0` for WSL/older Docker versions
