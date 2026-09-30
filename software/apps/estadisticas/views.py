from django.http import JsonResponse
from django.shortcuts import render

from apps.sensores.queries import resumen_periodo

PERIODOS = {'hoy': 1, 'semana': 7, 'mes': 30}


def estadisticas(request):
    return render(request, 'estadisticas/estadisticas.html',
                  {'periodo': request.GET.get('periodo', 'hoy')})


def datos(request):
    periodo = request.GET.get('periodo', 'hoy')
    dias = PERIODOS.get(periodo, 1)
    out = {c: resumen_periodo(c, dias) for c in ('troncal', 'rama_a', 'rama_b')}
    t, a, b = out['troncal']['acumulado'], out['rama_a']['acumulado'], out['rama_b']['acumulado']
    perd = round(t - a - b, 2)
    return JsonResponse({
        'periodo': periodo,
        'sensores': out,
        'volumen_total': round(t, 2),
        'perdidas': perd,
        'pct_perdida': round(100 * perd / t, 1) if t else 0,
    })
