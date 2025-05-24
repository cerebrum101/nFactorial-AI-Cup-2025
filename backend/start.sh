#!/bin/bash

# Use PORT environment variable if set, otherwise default to 10000
PORT=${PORT:-10000}

# Start uvicorn with the correct port
uvicorn main:app --host 0.0.0.0 --port $PORT 