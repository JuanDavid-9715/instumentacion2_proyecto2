from django.db.models import Avg, Count, Max, Sum
from django.utils import timezone

from .models import EstadoBomba, Sensor

import statistics


def resumen_sensor(codigo, dia=None):
    dia = dia or timezone.localdate()
    qs = Sensor.objects.get(codigo=codigo).lecturas.filter(ts_ingesta__date=dia)
    agg = qs.aggregate(n=Count('id'), suma=Sum('q'), prom=Avg('q'), mx=Max('q'))
    ultima = qs.order_by('-ts_ingesta').first()
    return {
        'n': agg['n'] or 0,
        'acumulado': round((agg['suma'] or 0) / 60.0, 2),
        'promedio': round(agg['prom'] or 0, 3),
        'maximo': round(agg['mx'] or 0, 3),
        'actual': round(ultima.q, 3) if ultima else 0,
    }


def balance_hoy(dia=None):
    t = resumen_sensor('troncal', dia)
    a = resumen_sensor('rama_a', dia)
    b = resumen_sensor('rama_b', dia)
    # acumulado en "L" aprox: suma de L/min / 60 (1 muestra/s)
    perdidas = round(t['acumulado'] - a['acumulado'] - b['acumulado'], 2)
    pct = round(100 * perdidas / t['acumulado'], 1) if t['acumulado'] else 0
    return {'troncal': t, 'rama_a': a, 'rama_b': b,
            'perdidas': perdidas, 'pct_perdida': pct,
            'estado': 'OK' if abs(pct) < 15 else 'REVISAR'}


def estado_bomba():
    eb = EstadoBomba.objects.order_by('-ts').first()
    return eb.estado if eb else 'OFF'


def _vals_periodo(codigo, dias):
    desde = timezone.now() - timezone.timedelta(days=dias)
    return list(
        Sensor.objects.get(codigo=codigo).lecturas
        .filter(ts_ingesta__gte=desde).order_by('ts_ingesta')
        .values_list('q', flat=True)
    )


def resumen_periodo(codigo, dias, max_pts=120):
    desde = timezone.now() - timezone.timedelta(days=dias)
    filas = list(
        Sensor.objects.get(codigo=codigo).lecturas
        .filter(ts_ingesta__gte=desde).order_by('ts_ingesta')
        .values('q', 'ts_ingesta')
    )
    vals = [r['q'] for r in filas]
    paso = max(1, len(filas) // max_pts)
    serie = [[r['ts_ingesta'].isoformat(), r['q']] for r in filas[::paso]]
    if not vals:
        return {'n': 0, 'media': 0, 'mediana': 0, 'moda': None, 'desv': 0,
                'min': 0, 'max': 0, 'q1': 0, 'q3': 0, 'iqr': 0,
                'w_inf': 0, 'w_sup': 0, 'atipicos': [],
                'acumulado': 0, 'serie': []}
    modas = statistics.multimode([round(v, 2) for v in vals])
    orden = sorted(vals)
    q1, med, q3 = statistics.quantiles(orden, n=4)
    iqr = q3 - q1
    lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    dentro = [v for v in vals if lim_inf <= v <= lim_sup]
    return {
        'n': len(vals),
        'media': round(statistics.fmean(vals), 3),
        'mediana': round(med, 3),
        'moda': modas[0] if len(modas) == 1 else None,
        'desv': round(statistics.stdev(vals), 3) if len(vals) > 1 else 0,
        'min': round(min(vals), 3),
        'max': round(max(vals), 3),
        'q1': round(q1, 3),
        'q3': round(q3, 3),
        'iqr': round(iqr, 3),
        'w_inf': round(min(dentro), 3),
        'w_sup': round(max(dentro), 3),
        'atipicos': sorted(round(v, 3) for v in vals if v < lim_inf or v > lim_sup)[:50],
        'acumulado': round(sum(vals) / 60.0, 2),
        'serie': serie,
    }


def ultimos(codigo, n=60):
    qs = (Sensor.objects.get(codigo=codigo).lecturas
          .order_by('-ts_ingesta').values_list('q', flat=True)[:n])
    return [round(v, 3) for v in reversed(list(qs))]
