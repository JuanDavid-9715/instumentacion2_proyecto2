#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py shell -c "
from apps.sensores.models import Sensor
Sensor.objects.get_or_create(codigo='troncal', defaults={'nombre': 'Troncal principal', 'k_factor': 7.5})
Sensor.objects.get_or_create(codigo='rama_a', defaults={'nombre': 'Casa A', 'k_factor': 7.5})
Sensor.objects.get_or_create(codigo='rama_b', defaults={'nombre': 'Casa B', 'k_factor': 7.5})
print('seed OK')
"
