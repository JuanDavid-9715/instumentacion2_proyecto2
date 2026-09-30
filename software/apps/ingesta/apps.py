import os
import sys

from django.apps import AppConfig


def debe_autoarrancar(argv=None, env=None):
    env = env if env is not None else os.environ
    if env.get('INGESTA_AUTOSTART', '1') != '1':
        return False
    argv = argv if argv is not None else sys.argv
    if 'runserver' in argv:
        return env.get('RUN_MAIN') == 'true' or '--noreload' in argv
    texto = ' '.join(argv)
    if any(s in texto for s in ('daphne', 'gunicorn', 'uvicorn', 'hypercorn')):
        return True
    return False


class IngestaConfig(AppConfig):
    name = 'apps.ingesta'

    def ready(self):
        if not debe_autoarrancar():
            return
        from .recolector import iniciar_en_hilo
        iniciar_en_hilo(f'autoin-{os.getpid()}')
        print('ingesta: autoarranque en este proceso')
