# API Functions

This is a TypeScript-based API service using Google's Functions Framework, designed to work with a PostgreSQL database.

## Architecture

```
┌──────────────┐
│  Developer   │
│  (Docker)    │
└──────┬───────┘
       │ docker-compose up
┌──────▼───────────────────────────────────────────────┐
│                        bridge network               │
│                                                     │
│  ┌───────────────┐  HTTP  ┌───────────────────────┐ │
│  │ api-functions │◀──────▶│  postgres-db          │ │
│  │ (Functions FW)│        │  (PostgreSQL)         │ │
│  └───────────────┘        └───────────────────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Features

- Built with TypeScript and Express
- Uses Google's Functions Framework for compatibility with Cloud Functions v2
- Connects to PostgreSQL database
- Provides REST API endpoints for ticket management
- Supports filtering, sorting, and pagination

## Development

### Prerequisites

- Docker and Docker Compose
- Node.js (for local development outside Docker)

### Getting Started

1. Clone the repository
2. Run the application:

```bash
docker-compose up
```

The API will be available at http://localhost:8080

### Local Development without Docker

```bash
cd api
npm install
npm run dev
```

## API Endpoints

### GET /tickets

Retrieves a list of tickets with filtering and pagination.

Query Parameters:
- `personInChargeId`: Filter by person in charge ID
- `accountId`: Filter by account ID
- `statusId`: Filter by status ID
- `scheduledCompletionDateFrom`: Filter by scheduled completion date (from)
- `scheduledCompletionDateTo`: Filter by scheduled completion date (to)
- `showCompleted`: Whether to show completed tickets (default: true)
- `searchQuery`: Search in summary, account name, and requestor name
- `sortBy`: Field to sort by (default: "reception_date_time")
- `sortOrder`: Sort order ("asc" or "desc", default: "desc")
- `limit`: Maximum number of tickets to return (default: 20)
- `offset`: Number of tickets to skip (default: 0)

### GET /health

Health check endpoint to verify the API is running.

## Deployment to GCP

This application can be deployed to Google Cloud Platform using:

1. Cloud Functions v2 (source upload)
2. Cloud Run (with the provided Dockerfile)
3. Cloud Functions v2 (container mode)

For database connectivity in production, use Cloud SQL for PostgreSQL with Cloud SQL Auth Proxy or Cloud SQL Python Connector.