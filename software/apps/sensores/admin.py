from django.contrib import admin

from .models import EstadoBomba, Lectura, ResumenDia, ResumenHora, ResumenMinuto, Sensor


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'k_factor', 'activo')
    list_filter = ('activo',)


@admin.register(Lectura)
class LecturaAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'q', 'ts_nodo', 'ts_ingesta')
    list_filter = ('sensor',)
    date_hierarchy = 'ts_ingesta'


@admin.register(ResumenMinuto)
class ResumenMinutoAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'inicio', 'n', 'promedio', 'minimo', 'maximo')
    list_filter = ('sensor',)


@admin.register(ResumenHora)
class ResumenHoraAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'inicio', 'n', 'promedio', 'minimo', 'maximo')
    list_filter = ('sensor',)


@admin.register(ResumenDia)
class ResumenDiaAdmin(admin.ModelAdmin):
    list_display = ('sensor', 'inicio', 'n', 'promedio', 'minimo', 'maximo')
    list_filter = ('sensor',)


@admin.register(EstadoBomba)
class EstadoBombaAdmin(admin.ModelAdmin):
    list_display = ('estado', 'origen', 'ts')
    list_filter = ('estado', 'origen')
