#!/bin/sh

# Start the Flask API
cd api
gunicorn app:app &
cd ..

# Start the Node.js frontend
cd frontend
npm run start