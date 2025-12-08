#!/bin/bash
echo "Starting Docker containers..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.dev up -d
echo ""
echo "Waiting for database to be ready..."
sleep 5
echo ""
echo "Checking container status:"
docker-compose ps
