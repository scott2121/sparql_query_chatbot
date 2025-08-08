# SPARQL Query Chatbot

This project provides a chatbot interface for generating and executing SPARQL queries, integrating with various biological and chemical databases. It includes a backend API, benchmarking tools, and RDF configuration management.

## Features
- Chatbot for SPARQL query generation
- Backend API with database integration
- Benchmarking and evaluation tools
- RDF configuration for multiple datasets

## Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.8+

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/scott2121/sparql_query_chatbot.git
   cd sparql_query_chatbot
   ```
2. Build and start services:
   ```bash
   docker compose up --build
   ```

## Usage

### Chat UI
The chat interface for SPARQL query generation is available at `http://localhost:8502` after starting the Docker containers.

### Database Management
Database administration interface (Adminer) is accessible at `http://localhost:8080` for managing the PostgreSQL database.

Default database connection details:
- **Username**: user
- **Password**: password
- **Database**: chatdb

### Backend API
The backend API (FastAPI) provides endpoints for chatbot interaction and database queries. Access it at `http://localhost:8000` after starting the Docker containers.

### SPARQL Generation Benchmark
Scripts in `sparql_gen_benchmark/functions/` allow you to generate, execute, and evaluate SPARQL queries. See the scripts for usage examples.

## RDF Configurations
The `rdf-config` repository (with updated `model.yaml` variable names and added Uniprot & Bgee set models) is included in this project and is required for the SPARQL query generation process. This is based on the [dbcls/rdf-config](https://github.com/dbcls/rdf-config) project with custom modifications for enhanced biological and chemical dataset support.

## License
All files in this repository are distributed under the [MIT License](https://opensource.org/license/mit "The MIT License").
