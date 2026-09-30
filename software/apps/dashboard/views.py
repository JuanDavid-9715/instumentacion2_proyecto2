from django.shortcuts import render


def prueba(request):
    return render(request, 'dashboard/prueba.html')
