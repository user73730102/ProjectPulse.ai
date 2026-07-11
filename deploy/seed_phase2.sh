#!/bin/bash
# Run this script on the EC2 instance after docker-compose up -d
# It applies the DB migration and seeds the Phase 2 mock data.

echo "Running Phase 2 Database Migrations..."
docker-compose exec -T backend python migrate_ncr.py

echo "Seeding Phase 2 Database Data..."
docker-compose exec -T backend python seed.py

echo "Phase 2 setup complete! You can now test the modules in the UI."
