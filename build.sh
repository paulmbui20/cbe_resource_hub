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

echo "Prepopulating Kenyan CBC (CBE) structure........................"
python manage.py prepopulate_cbe

echo "Prepopulating Primary Header and Footer menus..................."
python manage.py populate_menus

echo "Starting application............................................"
exec daphne -b 0.0.0.0 -p 8000 cbe_res_hub.asgi:application
