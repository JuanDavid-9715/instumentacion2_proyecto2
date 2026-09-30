import os

from django.core.management.base import BaseCommand

from apps.ingesta.recolector import bucle


class Command(BaseCommand):
    help = 'Suscribe flujo 1Hz + estado bomba y guarda en BD'

    def handle(self, *args, **options):
        bucle(f"dashboard-{os.getpid()}", log=self.stdout.write)
