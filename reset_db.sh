#!/bin/bash

echo "Stopping any running FastAPI server..."
pkill -f "uvicorn main:app"

echo "Removing old database..."
rm -f real_estate.db

echo "Removing old migrations..."
rm -f alembic/versions/*

echo "Creating new migration..."
alembic revision --autogenerate -m "Initial schema"

echo "Applying migration..."
alembic upgrade head

echo "Running sample data generation..."
python generate_sample_data.py

echo "Done! Database has been reset and populated with sample data."
