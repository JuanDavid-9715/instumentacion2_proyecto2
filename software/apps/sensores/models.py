from django.db import models


class Sensor(models.Model):
    TRONCAL = 'troncal'
    RAMA_A = 'rama_a'
    RAMA_B = 'rama_b'
    TIPOS = [
        (TRONCAL, 'Troncal'),
        (RAMA_A, 'Rama A'),
        (RAMA_B, 'Rama B'),
    ]

    codigo = models.CharField(max_length=16, unique=True, choices=TIPOS)
    nombre = models.CharField(max_length=64)
    k_factor = models.FloatField(default=7.5)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} ({self.nombre})"


class Lectura(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='lecturas')
    q = models.FloatField(help_text='Caudal L/min')
    ts_nodo = models.FloatField(null=True, blank=True, help_text='Epoch del ESP32')
    ts_ingesta = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-ts_ingesta']
        indexes = [
            models.Index(fields=['sensor', '-ts_ingesta']),
        ]

    def __str__(self):
        return f"{self.sensor.codigo} {self.q:.3f} L/min @ {self.ts_ingesta:%H:%M:%S}"


class ResumenMinuto(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='resumen_minuto')
    inicio = models.DateTimeField(db_index=True)
    n = models.IntegerField()
    suma = models.FloatField()
    promedio = models.FloatField()
    minimo = models.FloatField()
    maximo = models.FloatField()

    class Meta:
        ordering = ['-inicio']
        unique_together = [('sensor', 'inicio')]
        indexes = [models.Index(fields=['sensor', '-inicio'])]


class ResumenHora(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='resumen_hora')
    inicio = models.DateTimeField(db_index=True)
    n = models.IntegerField()
    suma = models.FloatField()
    promedio = models.FloatField()
    minimo = models.FloatField()
    maximo = models.FloatField()

    class Meta:
        ordering = ['-inicio']
        unique_together = [('sensor', 'inicio')]
        indexes = [models.Index(fields=['sensor', '-inicio'])]


class ResumenDia(models.Model):
    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name='resumen_dia')
    inicio = models.DateField(db_index=True)
    n = models.IntegerField()
    suma = models.FloatField()
    promedio = models.FloatField()
    minimo = models.FloatField()
    maximo = models.FloatField()

    class Meta:
        ordering = ['-inicio']
        unique_together = [('sensor', 'inicio')]
        indexes = [models.Index(fields=['sensor', '-inicio'])]


class EstadoBomba(models.Model):
    ENCENDIDA = 'ON'
    APAGADA = 'OFF'
    ESTADOS = [(ENCENDIDA, 'Encendida'), (APAGADA, 'Apagada')]

    estado = models.CharField(max_length=3, choices=ESTADOS)
    origen = models.CharField(max_length=16, default='mqtt')
    ts = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-ts']

    def __str__(self):
        return f"Bomba {self.estado} ({self.origen}) @ {self.ts:%H:%M:%S}"
