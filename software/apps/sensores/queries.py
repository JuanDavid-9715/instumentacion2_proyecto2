from django.db.models import Avg, Count, Max, Sum
from django.utils import timezone

from .models import EstadoBomba, Sensor


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
