from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.sensores.models import EstadoBomba, Sensor
from apps.sensores.queries import balance_hoy, estado_bomba, ultimos


def prueba(request):
    return render(request, 'dashboard/prueba.html')


def panel(request):
    ctx = balance_hoy()
    ctx['bomba'] = estado_bomba()
    ctx['spark'] = ultimos('troncal')
    return render(request, 'dashboard/panel.html', ctx)


def panel_datos(request):
    ahora = timezone.now()
    sensores = {}
    ultima = None
    for codigo in ('troncal', 'rama_a', 'rama_b'):
        lec = Sensor.objects.get(codigo=codigo).lecturas.order_by('-ts_ingesta').first()
        if lec:
            sensores[codigo] = {'q': round(lec.q, 3), 'ts': lec.ts_ingesta.isoformat()}
            if ultima is None or lec.ts_ingesta > ultima:
                ultima = lec.ts_ingesta
    bal = balance_hoy()
    eb = EstadoBomba.objects.order_by('-ts').first()
    seg = round((ahora - ultima).total_seconds()) if ultima else None
    pct = bal['pct_perdida']
    fresco = seg is not None and seg <= 25
    return JsonResponse({
        'actual': sensores,
        'acumulado': {k: bal[k]['acumulado'] for k in ('troncal', 'rama_a', 'rama_b')},
        'perdidas': bal['perdidas'],
        'pct_perdida': pct,
        'estado': 'OK' if abs(pct) < 10 else ('ATENCION' if abs(pct) < 15 else 'REVISAR'),
        'bomba': eb.estado if eb else 'OFF',
        'seg_desde_muestra': seg,
        'nodo_ok': fresco,
    })
