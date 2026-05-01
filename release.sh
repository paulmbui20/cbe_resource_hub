#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "Applying migrations............................................."
python manage.py migrate --noinput

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

echo "Release process completed successfully!"
