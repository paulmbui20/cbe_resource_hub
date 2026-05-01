#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# This script is run by every 'web' replica.
# Migrations and seeding should be run via release.sh on a single-replica service.

echo "Starting application............................................"
exec gunicorn cbe_res_hub.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers=2 \
    --threads=2 \
    --timeout=500 \
    --log-level=info
