# Project Structure Analysis

**Generated:** 2026-01-26T12:12:48Z
**Scan Mode:** Deep Scan
**Project Root:** /home/code/ai_story

---

## Repository Type

**Classification:** Multi-part Project (Monorepo-style)

This project contains 2 distinct parts that work together to form a complete application.

---

## Project Parts

### Part 1: Backend

- **Part ID:** `backend`
- **Project Type:** `backend`
- **Root Path:** `/home/code/ai_story/backend`
- **Primary Language:** Python
- **Framework:** Django 3.2.15
- **Description:** Django-based REST API backend with Celery task queue and WebSocket support

### Part 2: Frontend

- **Part ID:** `frontend`
- **Project Type:** `web`
- **Root Path:** `/home/code/ai_story/frontend`
- **Primary Language:** JavaScript (Vue 2.7.14)
- **Framework:** Vue 2.7.14 + Vuex + Vue Router
- **Build Tool:** Webpack 5.89.0
- **Description:** Vue 2 frontend application with daisyUI and Tailwind CSS

---

## Integration Pattern

- **Communication:** REST API + WebSocket (Socket.IO)
- **Frontend → Backend:** HTTP requests via Axios
- **Backend → Frontend:** Real-time updates via Django Channels + Socket.IO client

---

## Project Type Detection Details

### Backend Part

**Matched Patterns:**
- Django framework (Django 3.2.15)
- DRF (Django REST Framework 3.14.0)
- Celery task queue
- Python 3.11+

**Key Files:**
- `/home/code/ai_story/pyproject.toml`
- `/home/code/ai_story/backend/manage.py`
- `/home/code/ai_story/backend/config/`

### Frontend Part

**Matched Patterns:**
- Vue 2.7.14
- package.json
- Webpack config
- Tailwind CSS + daisyUI

**Key Files:**
- `/home/code/ai_story/frontend/package.json`
- `/home/code/ai_story/frontend/src/`
- `/home/code/ai_story/frontend/config/`

---

## Documentation Requirements by Part

### Backend (project_type_id: backend)

**Required Scans:**
- ✓ API contracts (requires_api_scan: true)
- ✓ Data models (requires_data_models: true)
- ✓ Configuration patterns (requires_deployment_config: true)

**Critical Directories:**
- src/, api/, services/, models/, routes/, controllers/, middleware/, handlers/

### Frontend (project_type_id: web)

**Required Scans:**
- ✓ API contracts (requires_api_scan: true)
- ✓ Data models (requires_data_models: true)
- ✓ State management (requires_state_management: true)
- ✓ UI components (requires_ui_components: true)
- ✓ Deployment config (requires_deployment_config: true)

**Critical Directories:**
- src/, app/, pages/, components/, api/, lib/, styles/, public/, static/
