from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.sensores.models import EstadoBomba, Sensor
from apps.sensores.queries import balance_hoy, estado_bomba, resumen_periodo, ultimos


def _vs_prom(sensor, dias=7):
    hoy = timezone.localdate()
    vals_hoy = list(sensor.lecturas.filter(ts_ingesta__date=hoy).values_list('q', flat=True))
    desde = timezone.now() - timezone.timedelta(days=dias)
    vals_ref = list(sensor.lecturas.filter(ts_ingesta__gte=desde).values_list('q', flat=True))
    prom_hoy = sum(vals_hoy) / len(vals_hoy) if vals_hoy else 0
    prom_ref = sum(vals_ref) / len(vals_ref) if vals_ref else 0
    pct = round(100 * (prom_hoy - prom_ref) / prom_ref, 1) if prom_ref else 0
    return {'prom_hoy': round(prom_hoy, 3), 'prom_ref': round(prom_ref, 3), 'vs': pct}


def red(request):
    ctx = balance_hoy()
    ctx['bomba'] = estado_bomba()
    eb = EstadoBomba.objects.order_by('-ts').first()
    ctx['bomba_ts'] = eb.ts if eb else None
    ctx['casas'] = []
    for codigo, nombre in (('rama_a', 'Casa A'), ('rama_b', 'Casa B')):
        sensor = Sensor.objects.get(codigo=codigo)
        ctx['casas'].append({
            'codigo': codigo, 'nombre': nombre,
            **ctx[codigo], **_vs_prom(sensor), 'spark': ultimos(codigo, 40),
        })
    return render(request, 'red/red.html', ctx)


def detalle(request, codigo):
    sensor = get_object_or_404(Sensor, codigo=codigo)
    hoy = timezone.localdate()
    lecturas_hoy = list(sensor.lecturas.filter(ts_ingesta__date=hoy).order_by('ts_ingesta').values('q', 'ts_ingesta'))
    vals_hoy = [r['q'] for r in lecturas_hoy]
    comp = _vs_prom(sensor)
    otro_cod = 'rama_b' if codigo == 'rama_a' else 'rama_a'
    otro = _vs_prom(get_object_or_404(Sensor, codigo=otro_cod)) if codigo in ('rama_a', 'rama_b') else None
    caja = resumen_periodo(codigo, 1)
    paso = max(1, len(lecturas_hoy) // 120)
    veredicto = ('sin datos hoy' if not vals_hoy else
                 f"{comp['vs']:+.1f}% sobre su promedio 7d" if comp['vs'] >= 0 else
                 f"{comp['vs']:.1f}% bajo su promedio 7d")
    bal = balance_hoy()
    t_acum = bal['troncal']['acumulado']
    mi_acum = bal[codigo]['acumulado'] if codigo in bal else 0
    return render(request, 'red/detalle.html', {
        'sensor': sensor,
        'color': 'ramaa' if codigo == 'rama_a' else 'ramab',
        'n_hoy': len(vals_hoy),
        'prom_hoy': comp['prom_hoy'],
        'prom_7d': comp['prom_ref'],
        'vs': comp['vs'],
        'veredicto': veredicto,
        'max_hoy': round(max(vals_hoy), 3) if vals_hoy else 0,
        'otro': otro,
        'otro_cod': otro_cod,
        'share': round(100 * mi_acum / t_acum, 1) if t_acum else 0,
        'caja': caja,
        'serie': [[r['ts_ingesta'].isoformat(), r['q']] for r in lecturas_hoy[::paso]],
    })


@require_POST
def bomba(request):
    from apps.ingesta.mqtt import publicar_orden_bomba
    orden = request.POST.get('orden', 'TOGGLE')
    try:
        publicar_orden_bomba(orden)
    except Exception:
        pass
    destino = request.POST.get('next', '')
    if destino.startswith('/') and not destino.startswith('//'):
        return redirect(destino)
    return redirect('red')
