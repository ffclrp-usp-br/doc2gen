import os
import sys
import threading
import webbrowser
from pathlib import Path

# ==========================================================
# BASE DIR
# ==========================================================

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

# ==========================================================
# APP DIR
# ==========================================================

APP_DIR = BASE_DIR / "app"

sys.path.insert(0, str(APP_DIR))

print("BASE_DIR =", BASE_DIR)
print("APP_DIR =", APP_DIR)

# DEBUG IMPORT
try:
    import myproject
    print("myproject importado com sucesso")
except Exception as e:
    print("ERRO IMPORTANDO MYPROJECT:", e)

# ==========================================================
# DJANGO
# ==========================================================

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "myproject.settings"
)

import django

django.setup()

from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from waitress import serve

call_command("migrate", interactive=False)

application = get_wsgi_application()

def abrir():
    webbrowser.open("http://127.0.0.1:8000")

threading.Timer(2, abrir).start()

serve(
    application,
    host="127.0.0.1",
    port=8000,
)
