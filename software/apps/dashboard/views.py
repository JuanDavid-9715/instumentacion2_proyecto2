from django.shortcuts import render

from apps.sensores.queries import balance_hoy, estado_bomba, ultimos


def prueba(request):
    return render(request, 'dashboard/prueba.html')


def panel(request):
    ctx = balance_hoy()
    ctx['bomba'] = estado_bomba()
    ctx['spark'] = ultimos('troncal')
    return render(request, 'dashboard/panel.html', ctx)
