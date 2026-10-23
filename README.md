# Containerized Bookstore REST API

A course project developed for **Database Systems and Cloud Computing (AIN-3003)** at Bahçeşehir University. It demonstrates a Python REST API backed by MongoDB, packaged with Docker, and configured for deployment on Kubernetes.

> **Project status:** Educational/portfolio project. The repository contains deployment manifests, but a fresh end-to-end Kubernetes deployment has not been independently verified. This is not a production-ready service.

## Tech Stack

- **Backend:** Python 3.11, Flask, Gunicorn
- **Database:** MongoDB 7, PyMongo
- **Containerization:** Docker
- **Orchestration:** Kubernetes (Deployment, StatefulSet, Services, ConfigMaps, Secrets, and persistent storage)

## Features

- Create, read, update, and delete bookstore records through a REST API
- Store records in a MongoDB `BOOKSTORE` database and `books` collection
- Return MongoDB ObjectIds as strings in API responses
- Run the Flask application in a Docker container with Gunicorn
- Define a MongoDB StatefulSet with persistent storage and a two-replica API Deployment
- Seed MongoDB with example bookstore records on initial database setup

## Architecture

```text
Client
  |
  v
Flask REST API (Gunicorn)
  |
  v
PyMongo / MongoDB

Kubernetes resources:
- bookstore-api Deployment (2 replicas) + Service
- mongo StatefulSet (1 replica) + Service + persistent volume claim
- ConfigMaps for application configuration and sample data
- Secret for MongoDB credentials
```

## Project Structure

```text
bookstore-project/
├── app.py                     # Flask REST API
├── bookstore.json             # Example bookstore records
├── book.json                  # Additional sample data
├── Dockerfile                 # API container image
├── requirements.txt           # Python dependencies
├── .dockerignore
├── .gitignore                 # Excludes local files and secrets
└── k8s/
    ├── 00-namespace.yaml
    ├── 01-mongo-secret.yaml       # Local-only; do not commit
    ├── 02-mongo-seed-configmap.yaml
    ├── 03-mongo-statefulset.yaml
    ├── 04-mongo-service.yaml
    ├── 05-app-configmap.yaml     # Local-only until credentials are separated
    ├── 06-app-deployment.yaml
    └── 07-app-service.yaml
```

The two local-only manifests above are intentionally excluded from the public repository until their credentials/configuration have been handled safely. Kubernetes deployment requires suitable local replacements and secure injection of the MongoDB connection settings.

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/health` | Returns API status and configured database/collection names (does **not** test database connectivity) |
| `GET` | `/books` | List all books |
| `GET` | `/books/<id>` | Retrieve a book by MongoDB ObjectId |
| `POST` | `/books` | Create a book from a JSON request body |
| `PUT` | `/books/<id>` | Update a book by ObjectId |
| `DELETE` | `/books/<id>` | Delete a book by ObjectId |

Example request, after the API is running:

```bash
curl http://localhost:5000/books

curl -X POST http://localhost:5000/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Example Book","author":"Example Author","year":2026}'
```

The API returns MongoDB-generated IDs for newly created records. Replace `<id>` in the other endpoint paths with an actual `_id` value from the API.

## Run Locally with Python

**Requirements:** Python 3.11 and a running MongoDB instance (the commands below assume MongoDB is available without authentication at `localhost:27017`).

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure the database connection using environment variables:

```text
MONGO_URI=mongodb://localhost:27017
DB_NAME=BOOKSTORE
COLLECTION=books
```

Set them in your shell before running the application. **Note:** `app.py` reads environment variables directly; it does not automatically load a `.env` file.

```bash
python app.py
```

The development server listens on `http://localhost:5000`. The original `app.py` enables Flask debug mode when run directly, so use this method only for local development.

## Run with Docker

The commands below start an isolated MongoDB instance and connect the API container to it via a Docker network. They use a local, unauthenticated MongoDB instance for demonstration only.

```bash
docker network create bookstore-net

docker run -d --name bookstore-mongo \
  --network bookstore-net \
  mongo:7

docker build -t bookstore-api:1.0 .

docker run -d --name bookstore-api \
  --network bookstore-net \
  -p 5000:5000 \
  -e MONGO_URI=mongodb://bookstore-mongo:27017 \
  -e DB_NAME=BOOKSTORE \
  -e COLLECTION=books \
  bookstore-api:1.0
```

Optionally, import the included sample books:

```bash
docker cp bookstore.json bookstore-mongo:/tmp/bookstore.json
docker exec bookstore-mongo mongoimport \
  --db BOOKSTORE \
  --collection books \
  --file /tmp/bookstore.json \
  --jsonArray
```

Then test:

```bash
curl http://localhost:5000/books
```

These commands are an example local setup, not a claim of a verified run in the current environment.

## Kubernetes Deployment

The `k8s/` directory defines the namespace, MongoDB StatefulSet and service, sample-data ConfigMap, API Deployment, and API service. The API Deployment uses the local image tag `bookstore-api:1.0`, and the API service exposes port `80` inside the cluster (with NodePort `30080` configured).

**Before deploying:**

1. Install or start a local Kubernetes cluster (for example, Minikube) and ensure `kubectl` is configured.
2. Build the API image: `docker build -t bookstore-api:1.0 .`.
3. For Minikube, make the local image accessible: `minikube image load bookstore-api:1.0`.
4. Supply a MongoDB Secret and configure the application connection **without committing credentials to Git**. The original `01-mongo-secret.yaml` and `05-app-configmap.yaml` contain example credentials and must be sanitized/refactored before public use. In particular, authentication details should be injected through Kubernetes Secrets, not a published ConfigMap.
5. Apply the manifests only after the referenced Secret and application configuration have been created appropriately.

```bash
kubectl apply -f k8s/
kubectl get pods -n bookstore
kubectl get services -n bookstore
kubectl port-forward -n bookstore service/bookstore-api 8080:80
```

With port-forwarding active, the API should be reachable at `http://localhost:8080/books`, provided the pods start successfully and the MongoDB connection is correctly configured.

MongoDB sample data is intended to be imported during **first-time database initialization**. An existing persistent volume may prevent initialization scripts from running again.

## Security and Limitations

- Never commit `.env`, `.venv/`, database passwords, or private Kubernetes Secret files.
- **Base64-encoded Kubernetes Secrets are not encrypted credentials.** Treat their values as sensitive.
- The original Kubernetes application ConfigMap embeds MongoDB connection credentials; move them to Secret-based configuration before publishing or deploying beyond a local lab.
- The API has no user authentication and limited request validation/error handling.
- The `/health` endpoint reports application configuration, not MongoDB readiness.
- Running `python app.py` starts Flask in debug mode; the Docker image uses Gunicorn instead.
- This project is intended to demonstrate core concepts, not production-grade security, observability, or scalability.

Developed as a project for **AIN-3003: Database Systems and Cloud Computing**.The assignment focused on integrating Flask, MongoDB, Docker and Kubernetes, including CRUD operations, service discovery, and deployment configuration.
