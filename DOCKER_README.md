# LinkedIn Agent Docker Setup

This document explains how to use the Docker setup for the LinkedIn Job Offer Auto-Responder.

## Why Two Services with One Dockerfile?

In our Docker Compose setup, we have two services (`linkedin-agent` and `linkedin-agent-scheduled`) that both use the same Dockerfile. This is a common pattern in Docker Compose when you have:

1. The same codebase and dependencies
2. Different entry points or execution modes
3. Different runtime configurations

Both services use the same Docker image (built from our Dockerfile), but they:
- Run different commands (`linkedin_agent.py` vs `scheduled_agent.py`)
- Have different restart policies
- Serve different purposes (manual vs scheduled checking)

This approach is more efficient than having two separate Dockerfiles that would duplicate most of the same setup steps.

## How to Use the Docker Setup

### Prerequisites

- Docker and Docker Compose installed on your system
- LinkedIn credentials in the `.env` file
- Optional: OpenAI API key in the `.env` file

### Building the Docker Image

```bash
docker-compose build
```

### Running the Manual Mode

This mode checks for messages once and then exits:

```bash
docker-compose up linkedin-agent
```

### Running the Scheduled Mode

This mode checks for messages periodically according to the schedule in `.env`:

```bash
docker-compose up -d linkedin-agent-scheduled
```

The `-d` flag runs the container in detached mode (background).

### Viewing Logs

```bash
# For the scheduled service
docker-compose logs -f linkedin-agent-scheduled
```

### Stopping the Services

```bash
docker-compose down
```

## Troubleshooting

### Chrome/Selenium Issues

If you encounter issues with Chrome or Selenium in the Docker container:

1. Check that the entrypoint script has execute permissions:
   ```bash
   chmod +x entrypoint.sh
   ```

2. Verify that Xvfb is running correctly in the container:
   ```bash
   docker-compose exec linkedin-agent-scheduled ps aux | grep Xvfb
   ```

3. Check the container logs for any error messages:
   ```bash
   docker-compose logs linkedin-agent-scheduled
   ```

### LinkedIn Detection

LinkedIn may detect automation. If you encounter login issues:
- Reduce the frequency of checks
- Consider using a VPN
- Ensure you're not violating LinkedIn's terms of service
