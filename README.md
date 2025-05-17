# GitHub Wiki Exporter

A modern web application that allows you to download GitHub wikis in various formats (Markdown, PDF, EPUB).

## Features

- **Complete Wiki Export**: Retrieves all pages from GitHub wikis, not just the home page
- **Multiple Formats**: Export to Markdown, PDF, and EPUB formats
- **Real-time Tracking**: Monitor export progress in real-time
- **Responsive UI**: Clean interface with dark/light mode support
- **Resource Management**: Delete jobs and exports when no longer needed
- **RESTful API**: Programmatic access to all features
- **Clean Architecture**: Built with Hexagonal Architecture and CQRS/ES patterns

## Architecture

This application implements:

- **Hexagonal Architecture** (Ports and Adapters): Clean separation of concerns with domain at the center
- **CQRS** (Command Query Responsibility Segregation): Separate models for reading and writing data
- **Event Sourcing**: All changes captured as a sequence of events

### Project Structure

```
gh_wikis/
   │
   ├── domain/           # Core business logic and interfaces
   │   ├── model/        # Domain entities and value objects
   │   ├── repositories/ # Repository interfaces
   │   ├── services/     # Service interfaces
   │   └── events/       # Domain events
   │
   ├── application/      # Application services and use cases
   │   ├── commands/     # Command handlers
   │   ├── queries/      # Query handlers
   │   └── events/       # Event handlers
   │
   ├── infrastructure/   # External systems and implementations
   │   ├── db/           # Database models and repositories
   │   ├── services/     # External services implementations
   │   └── tasks/        # Background tasks
   │
   └── interfaces/       # User interfaces
       ├── api/          # REST API
       └── web/          # Web UI
```

## Technology Stack

- **Backend**
    - Python 3.11+ with FastAPI
    - SQLAlchemy ORM
    - Alembic for migrations

- **Frontend**
    - Jinja2 templates
    - Tailwind CSS with DaisyUI components
    - JavaScript for real-time updates

- **Storage & Processing**
    - PostgreSQL for data persistence
    - MinIO for file storage (S3-compatible)
    - Redis + Celery for async processing

- **Deployment**
    - Docker and Docker Compose for containerization

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/gh-wikis.git
   cd gh-wikis
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env file with your GitHub token and other settings
   ```

3. **Start with Docker Compose**

   ```bash
   docker-compose up -d
   ```

4. **Or set up for local development**

   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Install dependencies
   pip install -e .
   
   # Start only infrastructure services
   docker-compose up -d postgres redis minio init-minio
   
   # Run the application
   python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Access the application at [http://localhost:8000](http://localhost:8000)**

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST   | `/api/jobs` | Create a new wiki export job |
| GET    | `/api/jobs` | List all jobs |
| GET    | `/api/jobs/{job_id}` | Get job details |
| DELETE | `/api/jobs/{job_id}` | Delete a job and its files |
| GET    | `/api/jobs/{job_id}/files` | Get export files for a job |
| GET    | `/api/files/{file_id}` | Download a file |
| DELETE | `/api/files/{file_id}` | Delete a specific file |

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
