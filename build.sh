#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

# Run migrations
echo "Applying migrations............................................."
python manage.py migrate

# echo "Collecting static files......................................."
# python manage.py collectstatic --noinput

echo "Populating Site Settings........................................"
python manage.py populate_site_settings

echo "Populating Academic Sessions ..................................."
python manage.py populate_academic_sessions

echo "Prepopulating Kenyan CBC (CBE) structure........................"
python manage.py prepopulate_cbe

echo "Prepopulating Primary Header and Footer menus..................."
python manage.py populate_menus

echo "Clearing Cache............................."
python manage.py clear_all_cache --force


echo "Starting application............................................"
exec gunicorn cbe_res_hub.wsgi:application --bind 0.0.0.0:8000 --workers=2 --threads=2 --timeout=500 --log-level=info
