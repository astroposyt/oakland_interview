# Documentation

## Table of Contents

1. [How to Run](#how-to-run)
2. [CI/CD](#cicd)

---

# How to Run

## Requirements

- Docker engine running

## Getting Started

A Makefile has been created to simplify development. The available commands are:

- `make start` - Starts the application
- `make stop` - Stops the application
- `make clean` - Clears the database and stops the application
- `make init` - Initializes the database tables

## Starting the Application

1. Ensure Docker is running
2. Run `make start`
3. Access the frontend at `http://localhost:8000/`

## Stopping and Cleaning Up

To stop the application, run `make stop`.

To reset the database and start fresh, run `make clean`.

---

# CI/CD

GitHub Actions automates deployment and testing for this project.

## Setup

To deploy the application, add the following secrets to your repository settings under **Actions → Secrets and variables → Repository secrets**:

- `SSH_HOST` - The IP address or hostname of your deployment server
- `SSH_USERNAME` - SSH username for server access
- `SSH_PRIVATE_KEY` - Private SSH key for authentication

These credentials can be obtained from your cloud VM provider. For this project, Hetzner was chosen for its lightweight and cost-effective approach, though these steps work with any provider.

## Deployment Workflow

The `deploy.yml` workflow file (in `.github/workflows/`) automates server synchronization whenever you push changes. This workflow:

- Reduces human error
- Accelerates development cycles
- Runs automatically on every deployment

## Testing

Unit tests are automatically run as part of the CI/CD pipeline via `test.yml`.

## Future Improvements

A manual approval step should be introduced in GitHub to prevent bugs from propagating to production.