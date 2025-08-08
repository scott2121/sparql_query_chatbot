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

### Backend API
The backend API (FastAPI) provides endpoints for chatbot interaction and database queries. Access it at `http://localhost:8000` after starting the Docker containers.

### SPARQL Generation Benchmark
Scripts in `sparql_gen_benchmark/functions/` allow you to generate, execute, and evaluate SPARQL queries. See the scripts for usage examples.

## RDF Configurations
The `sparql_gen_benchmark/rdf-config/` directory contains RDF configuration files for various biological and chemical datasets. Refer to its README for details.

## Contributing
Pull requests and issues are welcome. Please follow standard Python and Docker best practices.

## License
All files in this repository are distributed under the [MIT License](https://opensource.org/license/mit "The MIT License").
