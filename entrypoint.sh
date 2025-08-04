#!/bin/bash
# Start Xvfb
Xvfb :99 -screen 0 1280x1024x24 &
sleep 1

# Execute the command passed to docker run
exec "$@"
