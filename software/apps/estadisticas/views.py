import statistics

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.sensores.models import Sensor

PERIODOS = {'hoy': 1, 'semana': 7, 'mes': 30}


def _lecturas(codigo, dias):
    desde = timezone.now() - timezone.timedelta(days=dias)
    return list(
        Sensor.objects.get(codigo=codigo).lecturas
        .filter(ts_ingesta__gte=desde).order_by('ts_ingesta')
        .values_list('q', flat=True)
    )


def _serie(codigo, dias, max_pts=120):
    desde = timezone.now() - timezone.timedelta(days=dias)
    qs = Sensor.objects.get(codigo=codigo).lecturas.filter(
        ts_ingesta__gte=desde).order_by('ts_ingesta').values('q', 'ts_ingesta')
    vals = [(r['ts_ingesta'].isoformat(), r['q']) for r in qs]
    paso = max(1, len(vals) // max_pts)
    return vals[::paso]


def _stats(vals):
    if not vals:
        return {'n': 0, 'media': 0, 'mediana': 0, 'moda': 0,
                'desv': 0, 'min': 0, 'max': 0}
    modas = statistics.multimode([round(v, 2) for v in vals])
    return {
        'n': len(vals),
        'media': round(statistics.fmean(vals), 3),
        'mediana': round(statistics.median(vals), 3),
        'moda': modas[0] if len(modas) == 1 else None,
        'desv': round(statistics.stdev(vals), 3) if len(vals) > 1 else 0,
        'min': round(min(vals), 3),
        'max': round(max(vals), 3),
    }


def estadisticas(request):
    return render(request, 'estadisticas/estadisticas.html',
                  {'periodo': request.GET.get('periodo', 'hoy')})


def datos(request):
    periodo = request.GET.get('periodo', 'hoy')
    dias = PERIODOS.get(periodo, 1)
    out = {}
    for codigo in ('troncal', 'rama_a', 'rama_b'):
        vals = _lecturas(codigo, dias)
        st = _stats(vals)
        st['acumulado'] = round(sum(vals) / 60.0, 2)
        st['serie'] = _serie(codigo, dias)
        out[codigo] = st
    return JsonResponse({'periodo': periodo, 'sensores': out})
