# Technology Stack Analysis

**Generated:** 2026-01-26T12:17:00Z
**Scan Mode:** Deep Scan
**Scan Scope:** Backend + Frontend

---

## Backend Technology Stack

### Core Framework

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **Language** | Python | 3.11+ | Required by pyproject.toml |
| **Web Framework** | Django | 3.2.15 | Stable LTS version for production |
| **API Framework** | Django REST Framework | 3.14.0 | RESTful API layer |
| **Async Layer** | Django Channels | 4.0.0 | WebSocket support for real-time features |
| **ASGI Server** | Daphne | 4.2.1 | ASGI server for Channels |
| **Task Queue** | Celery | 5.5.0b2 | Async task processing (beta version) |
| **Task Scheduler** | django-celery-beat | 2.2.1 | Periodic task management |
| **Task Results** | django-celery-results | 2.4.0 | Celery result backend |

### Authentication & Security

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **JWT Auth** | djangorestframework-simplejwt | 5.3.1 | JWT token authentication |
| **JWT Legacy** | djangorestframework-jwt | 1.11.0 | Legacy JWT support |
| **CORS** | django-cors-headers | 4.5.0 | Cross-origin resource sharing |
| **Password Validation** | Django validators | Built-in | Password security |

### Database & Caching

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **Database (Dev)** | SQLite | 3.x | Development database |
| **Database (Prod)** | PostgreSQL | Recommended | Production database |
| **Redis** | redis-py | 5.4.0+ | Multiple databases for different purposes |
| **Cache Backend** | django-redis | 5.4.0+ | Django cache framework with Redis |

### AI & Integration

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **HTTP Client** | aiohttp | 3.13.0+ | Async HTTP client for AI APIs |
| **WebSocket Client** | websocket-client | 1.9.0 | WebSocket connections |
| **HTTP Client (Sync)** | requests | 2.32.5+ | Synchronous HTTP requests |
| **Video Processing** | pyjianyingdraft | 0.2.5 | JianYing (剪映) draft format |
| **Image Processing** | Pillow | 12.0.0+ | Image manipulation |

### Utilities

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **Environment** | python-dotenv | 1.2.1+ | Environment variable management |
| **Templating** | Jinja2 | 3.1.6+ | Template engine |
| **Concurrency** | gevent | 25.9.1+ | Async networking library |

### Backend Architecture Pattern

**Architecture Style:** Layered Service-Oriented Architecture

- **API Layer:** Django REST Framework ViewSets (apps/*/views.py)
- **Business Logic Layer:** Services (apps/*/services.py) + Tasks (apps/*/tasks.py)
- **Workflow Engine:** Pipeline with Chain of Responsibility (core/pipeline/)
- **AI Client Layer:** Strategy + Factory Pattern (core/ai_client/)
- **Data Layer:** Django ORM Models (apps/*/models.py)
- **Infrastructure:** Redis (5 databases), Celery workers, Channels

---

## Frontend Technology Stack

### Core Framework

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **Language** | JavaScript | ES6+ | Modern JavaScript |
| **Framework** | Vue.js | 2.7.14 | Stable Vue 2 version |
| **State Management** | Vuex | 3.6.2 | Centralized state management |
| **Routing** | Vue Router | 3.6.5 | Client-side routing |
| **HTTP Client** | Axios | 1.6.2 | Promise-based HTTP client |
| **Real-time** | Socket.IO Client | 4.6.1 | WebSocket client for real-time updates |

### Build Tools

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **Bundler** | Webpack | 5.89.0 | Module bundler |
| **Dev Server** | webpack-dev-server | 4.15.1 | Development server |
| **Module Loader** | babel-loader | 9.1.3 | Babel webpack loader |
| **CSS Loader** | css-loader | 6.8.1 | CSS module loader |
| **Style Loader** | style-loader | 3.3.3 | Style injection |
| **Vue Loader** | vue-loader | 15.11.1 | Vue SFC loader |
| **Template Compiler** | vue-template-compiler | 2.7.14 | Vue template compilation |

### Styling

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **CSS Framework** | Tailwind CSS | 3.4.17 | Utility-first CSS |
| **UI Components** | daisyUI | 4.12.23 | Component library on Tailwind |
| **PostCSS** | postcss | 8.4.32 | CSS transformation |
| **Autoprefixer** | autoprefixer | 10.4.16 | Vendor prefixing |

### Development Tools

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **Babel Core** | @babel/core | 7.23.5 | JavaScript compiler |
| **Babel Preset** | @babel/preset-env | 7.23.5 | Modern JavaScript targets |
| **ESLint** | eslint | 8.55.0 | JavaScript linter |
| **ESLint Vue** | eslint-plugin-vue | 9.19.2 | Vue.js linting |
| **Webpack Merge** | webpack-merge | 5.10.0 | Webpack config merging |

### Utilities

| Category | Technology | Version | Justification |
|----------|-----------|---------|---------------|
| **Utilities** | Lodash | 4.17.21 | Utility functions |
| **Date/Time** | Day.js | 1.11.10 | Date manipulation |

### Frontend Architecture Pattern

**Architecture Style:** Component-Based Architecture with Centralized State

- **View Layer:** Vue Components (src/views/, src/components/)
- **State Management:** Vuex Store (src/store/)
- **Routing:** Vue Router (src/router/)
- **Service Layer:** API Services (src/services/, src/api/)
- **Utilities:** Helper functions (src/utils/)
- **Build Pipeline:** Webpack with Babel, PostCSS, Tailwind

---

## Infrastructure & DevOps

### Message Queue & Real-time

| Category | Technology | Purpose | Redis DB |
|----------|-----------|---------|----------|
| **Task Queue** | Celery | Async task processing | DB 0 |
| **Result Backend** | Celery | Task result storage | DB 1 |
| **Pub/Sub** | Custom Redis | Real-time notifications | DB 2 |
| **WebSocket** | Django Channels | WebSocket connections | DB 3 |
| **Cache** | Django Cache | Query/response caching | DB 4 |

### Containerization

| Category | Technology | Purpose |
|----------|-----------|---------|
| **Container** | Docker | Application containerization |
| **Orchestration** | docker-compose | Multi-container management |

### Package Management

| Part | Tool | Config File |
|------|------|-------------|
| **Backend** | uv (Python) | pyproject.toml, uv.lock |
| **Frontend** | npm | package.json, package-lock.json |

---

## Architecture Patterns by Part

### Backend (Django)

**Pattern:** Service-Oriented Layered Architecture

```
┌─────────────────────────────────────┐
│     API Layer (DRF ViewSets)        │  ← REST endpoints
├─────────────────────────────────────┤
│  Business Logic Layer (Services)    │  ← Domain logic
├─────────────────────────────────────┤
│   Workflow Engine (Pipeline)        │  ← Chain of Responsibility
├─────────────────────────────────────┤
│      AI Client Layer (Strategy)     │  ← AI abstraction
├─────────────────────────────────────┤
│    Data Layer (Django ORM)          │  ← Database models
└─────────────────────────────────────┘
```

**Key Design Patterns:**
- **Chain of Responsibility:** Pipeline workflow engine (core/pipeline/)
- **Strategy Pattern:** AI client abstraction (core/ai_client/)
- **Factory Pattern:** AI client factory (core/ai_client/factory.py)
- **Domain-Driven Design (DDD):** apps/ as domain boundaries

### Frontend (Vue 2)

**Pattern:** Component-Based Architecture with Centralized State

```
┌─────────────────────────────────────┐
│    View Components (views/)         │  ← Page-level components
├─────────────────────────────────────┤
│   Reusable Components (components/) │  ← Shared UI components
├─────────────────────────────────────┤
│   Vuex Store (store/)               │  ← Global state
├─────────────────────────────────────┤
│   Vue Router (router/)              │  ← Navigation
├─────────────────────────────────────┤
│   API Services (services/)          │  → Backend API
└─────────────────────────────────────┘
```

**Key Concepts:**
- **Single File Components (SFC):** .vue files
- **Vuex Modules:** Modular state management
- **Axios Interceptors:** HTTP request/response handling
- **Socket.IO:** Real-time event handling

---

## Integration Architecture

### Backend ↔ Frontend Communication

| Layer | Protocol | Tool | Purpose |
|-------|----------|------|---------|
| **REST API** | HTTP/HTTPS | Axios | CRUD operations |
| **Real-time** | WebSocket | Socket.IO + Channels | Live updates, streaming |
| **SSE** | Server-Sent Events | Custom implementation | Progress streaming |

### Data Flow

```
Frontend (Vue)                      Backend (Django)
     │                                    │
     ├─ Axios ─────────────────────────→ ├─ DRF ViewSets
     │                                    │
     ├─ Socket.IO ──────────────────────→ ├─ Django Channels
     │                                    │
     └─ SSE EventSource ────────────────→ ├─ Celery → Redis Pub/Sub
                                          │
                                          ├─ Pipeline (Workflow)
                                          │
                                          ├─ AI Client (Strategy)
                                          │
                                          └─ Celery Tasks (Async)
```

---

## Development Environment

### Backend Requirements

- **Python:** 3.11+
- **Package Manager:** uv (modern Python package manager)
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Redis:** 5 separate databases for different purposes
- **Celery Worker:** For async task processing
- **ASGI Server:** Daphne for WebSocket support

### Frontend Requirements

- **Node.js:** >=16.0.0
- **npm:** >=8.0.0
- **Modern browser:** Chrome, Firefox, Safari, Edge

---

## Testing & Quality

### Backend Testing

- **Test Framework:** pytest (inferred from common Django practices)
- **Test Files:** test_*.py, *_test.py patterns
- **Coverage:** pytest-cov (common)

### Frontend Testing

- **Linter:** ESLint with Vue plugin
- **Build Verification:** Webpack compilation

---

## Deployment Architecture

### Container Strategy

- **Backend:** Dockerized Django + Daphne ASGI server
- **Frontend:** Nginx serving built static assets
- **Celery:** Separate worker containers
- **Redis:** Single Redis instance with 5 databases

### Environment Variables

- `.env` files for configuration
- `SECRET_KEY`, `REDIS_HOST`, `REDIS_PORT` critical variables
- Separate configs for development/production

---

## Summary

**Backend Stack:**
- Django 3.2.15 + DRF + Channels + Celery
- Redis (5 databases) for multi-purpose caching/messaging
- AI integration via aiohttp + custom AI client layer
- Pipeline workflow engine for complex business logic

**Frontend Stack:**
- Vue 2.7.14 + Vuex + Vue Router
- Tailwind CSS + daisyUI for styling
- Axios + Socket.IO for backend communication
- Webpack 5 for build pipeline

**Integration:**
- REST API + WebSocket + SSE
- Real-time updates via Redis Pub/Sub
- Async task processing via Celery
