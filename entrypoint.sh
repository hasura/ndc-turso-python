#!/bin/bash

# Export environment variables from .env file
set -a
source .env
set +a

# Logic based on APP_MODE
if [ "$APP_MODE" = "configuration" ]; then
    exec python main.py configuration serve --port $CONFIG_SERVER_PORT
else
    # Initialize the command
    CMD="python main.py serve --configuration $CONFIGURATION_PATH --port $SERVER_PORT"

    # Add the service token secret if it's set
    if [ ! -z "$SERVER_SECRET" ]; then
        CMD="$CMD --service-token-secret $SERVER_SECRET"
    fi

    # Execute the command
    exec $CMD
fi
