# Docker Setup for Salon Management System

This project includes Docker configuration for both development and production deployments.

## Quick Start

### Option 1: Docker Compose (Recommended for Development)

Run both frontend and backend with hot-reload:

```bash
# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up --build
```

Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000

### Option 2: Single Container (Production)

Build and run everything in one container:

```bash
# Build the image
docker build -t salon-app .

# Run the container
docker run -p 5000:5000 salon-app

# Run with volume for database persistence
docker run -p 5000:5000 -v $(pwd)/backend/instance:/app/instance salon-app
```

Access the application: http://localhost:5000

## Configuration

### Environment Variables

**Backend:**
- `FLASK_APP=app.py`
- `FLASK_ENV=development` (or `production`)
- `PYTHONUNBUFFERED=1`

**Frontend:**
- `VITE_API_URL=http://localhost:5000`

### Ports

- Frontend: 5173 (Vite dev server)
- Backend: 5000 (Flask API)

## File Structure

```
D:/Salon/
├── Dockerfile              # Single container (production)
├── docker-compose.yml      # Multi-container (development)
├── .dockerignore          # Files to exclude from Docker
├── backend/
│   ├── Dockerfile.backend  # Backend-specific Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── instance/
│       └── salon.db       # SQLite database (persisted)
└── frontend/
    ├── Dockerfile.frontend # Frontend-specific Dockerfile
    ├── package.json
    └── src/
```

## Development Workflow

1. **Start services:**
   ```bash
   docker-compose up
   ```

2. **Make code changes:**
   - Frontend: Changes auto-reload (hot module replacement)
   - Backend: Changes auto-reload (Flask debug mode)

3. **View logs:**
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f frontend
   ```

4. **Stop services:**
   ```bash
   docker-compose down
   ```

## Production Deployment

### Build Single Container

```bash
# Build production image
docker build -t salon-app:latest .

# Run production container
docker run -d \
  --name salon-app \
  -p 80:5000 \
  -v /path/to/data:/app/instance \
  --restart unless-stopped \
  salon-app:latest
```

### Database Persistence

The SQLite database is stored in `backend/instance/salon.db`. To persist data:

**Docker Compose:**
```yaml
volumes:
  - ./backend/instance:/app/instance
```

**Docker Run:**
```bash
-v $(pwd)/backend/instance:/app/instance
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
netstat -ano | findstr :5000
netstat -ano | findstr :5173

# Kill the process or change port in docker-compose.yml
```

### Database Issues

```bash
# Access backend container
docker exec -it salon-backend bash

# Check database
sqlite3 instance/salon.db
```

### Rebuild from Scratch

```bash
# Remove all containers and images
docker-compose down
docker system prune -a

# Rebuild
docker-compose up --build
```

## Commands Cheat Sheet

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Rebuild specific service
docker-compose build backend
docker-compose build frontend

# Restart specific service
docker-compose restart backend
docker-compose restart frontend

# Access container shell
docker exec -it salon-backend bash
docker exec -it salon-frontend sh

# Remove volumes (careful: deletes data!)
docker-compose down -v
```

## Notes

- The single Dockerfile builds the React app and serves it through Flask (production setup)
- Docker Compose runs frontend and backend separately (development setup with hot-reload)
- Database is persisted via volumes
- CORS is configured for localhost development
- For production, update CORS settings and use environment variables

