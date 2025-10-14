# from app import run_app

# app = run_app()

# if __name__ == "__main__":
#     app.run()
import subprocess
from app import run_app

app = run_app()

def start_core():
    """Inicia core.py en un proceso separado."""
    try:
        # Ejecuta el proceso en segundo plano, sin bloquear Flask
        subprocess.Popen(["python", "core.py"])
        print("✅ core.py iniciado correctamente en segundo plano.")
    except Exception as e:
        print(f"⚠️ Error al iniciar core.py: {e}")

# Lanza el proceso al inicio del servidor
start_core()

if __name__ == "__main__":
    # Flask escucha en todas las interfaces para Render
    app.run(host="0.0.0.0", port=5000)
