from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.sensores.models import Sensor
from apps.sensores.queries import balance_hoy, estado_bomba


def red(request):
    ctx = balance_hoy()
    ctx['bomba'] = estado_bomba()
    ctx['casas'] = [
        {'codigo': 'rama_a', 'nombre': 'Casa A', **ctx['rama_a']},
        {'codigo': 'rama_b', 'nombre': 'Casa B', **ctx['rama_b']},
    ]
    return render(request, 'red/red.html', ctx)


def detalle(request, codigo):
    sensor = get_object_or_404(Sensor, codigo=codigo)
    hoy = timezone.localdate()
    lecturas_hoy = list(sensor.lecturas.filter(ts_ingesta__date=hoy).order_by('ts_ingesta').values('q', 'ts_ingesta'))
    desde7 = timezone.now() - timezone.timedelta(days=7)
    vals7 = list(sensor.lecturas.filter(ts_ingesta__gte=desde7).values_list('q', flat=True))
    prom7 = round(sum(vals7) / len(vals7), 3) if vals7 else 0
    vals_hoy = [r['q'] for r in lecturas_hoy]
    prom_hoy = round(sum(vals_hoy) / len(vals_hoy), 3) if vals_hoy else 0
    paso = max(1, len(lecturas_hoy) // 120)
    return render(request, 'red/detalle.html', {
        'sensor': sensor,
        'n_hoy': len(vals_hoy),
        'prom_hoy': prom_hoy,
        'prom_7d': prom7,
        'max_hoy': round(max(vals_hoy), 3) if vals_hoy else 0,
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
    return redirect('red')
