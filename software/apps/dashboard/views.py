from django.shortcuts import render

from apps.sensores.queries import balance_hoy, estado_bomba


def prueba(request):
    return render(request, 'dashboard/prueba.html')


def panel(request):
    ctx = balance_hoy()
    ctx['bomba'] = estado_bomba()
    return render(request, 'dashboard/panel.html', ctx)
