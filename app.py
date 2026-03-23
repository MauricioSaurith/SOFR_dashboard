"""
app.py — Servidor Flask para el visualizador de datos SOFR.
Importa y ejecuta get_sofr.py sin modificarlo en absoluto.

Funciona tanto en local como desplegado en Vercel:
  - Local  → el Excel se guarda en la carpeta del proyecto
  - Vercel → el Excel se guarda en /tmp (efímero, pero funcional por sesión)
             La API key viaja como variable de entorno configurada en el
             dashboard de Vercel (nunca expuesta en el código ni en GitHub).
"""

import os
import sys
import threading
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, request
from flask_cors import CORS

# ──────────────────────────────────────────────────────────────
# Variables de entorno
#   · Local  → se leen desde el archivo .env (excluido de GitHub)
#   · Vercel → se leen desde el panel Environment Variables de Vercel
# En ambos casos el código es idéntico: os.getenv("FRED_API_KEY")
# ──────────────────────────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("FRED_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "No se encontró FRED_API_KEY.\n"
        "  · Local:  crea un archivo .env con FRED_API_KEY=tu_clave\n"
        "  · Vercel: agrégala en Project → Settings → Environment Variables\n"
        "Obtén una clave gratis en https://fred.stlouisfed.org/docs/api/api_key.html"
    )

# ──────────────────────────────────────────────────────────────
# Ruta del archivo Excel
#   · Local  → misma carpeta del proyecto
#   · Vercel → /tmp  (único directorio con escritura en entorno serverless)
# ──────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
ON_VERCEL  = bool(os.getenv("VERCEL"))          # Vercel inyecta esta var automáticamente
EXCEL_FILE = "/tmp/historico_sofr.xlsx" if ON_VERCEL else str(BASE_DIR / "historico_sofr.xlsx")

# ──────────────────────────────────────────────────────────────
# Importar la función del script original SIN MODIFICARLO
# ──────────────────────────────────────────────────────────────
sys.path.insert(0, str(BASE_DIR))
from get_sofr import update_sofr_official_api   # ← tu script, intacto

app = Flask(__name__, template_folder="templates")
CORS(app)

# Estado del hilo de actualización
update_state = {"running": False, "log": [], "error": None}
state_lock   = threading.Lock()


# ──────────────────────────────────────────────────────────────
# Hilo de actualización — llama directamente a tu función
# ──────────────────────────────────────────────────────────────
def _run_update():
    """
    Llama a update_sofr_official_api() (de get_sofr.py, sin cambios)
    en un hilo separado. Captura los print() para mostrarlos en el dashboard.
    """
    with state_lock:
        update_state["running"] = True
        update_state["log"]     = []
        update_state["error"]   = None

    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            update_sofr_official_api(api_key=API_KEY, filename=EXCEL_FILE)
        with state_lock:
            update_state["log"] = buf.getvalue().splitlines()
    except Exception as exc:
        with state_lock:
            update_state["error"] = str(exc)
            update_state["log"]   = buf.getvalue().splitlines()
    finally:
        with state_lock:
            update_state["running"] = False


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────

@app.route("/api/update", methods=["POST"])
def api_update():
    """Lanza la actualización en background."""
    with state_lock:
        if update_state["running"]:
            return jsonify({"status": "already_running"}), 202
    threading.Thread(target=_run_update, daemon=True).start()
    return jsonify({"status": "started"}), 202


@app.route("/api/status", methods=["GET"])
def api_status():
    """Estado en tiempo real del proceso de actualización."""
    with state_lock:
        return jsonify({
            "running": update_state["running"],
            "log":     update_state["log"],
            "error":   update_state["error"],
        })


@app.route("/api/data", methods=["GET"])
def api_data():
    """Datos del Excel como JSON para el gráfico y la tabla."""
    if not os.path.exists(EXCEL_FILE):
        return jsonify({"error": "Sin datos aún. Presiona 'Actualizar'."}), 404

    df = pd.read_excel(EXCEL_FILE)
    df["DATE"] = pd.to_datetime(df["DATE"]).dt.strftime("%Y-%m-%d")
    df = df.sort_values("DATE", ascending=True)

    stats = {
        "last_date":  df["DATE"].iloc[-1],
        "last_value": round(float(df["SOFR"].iloc[-1]), 4),
        "max_value":  round(float(df["SOFR"].max()),    4),
        "min_value":  round(float(df["SOFR"].min()),    4),
        "avg_value":  round(float(df["SOFR"].mean()),   4),
        "total_rows": int(len(df)),
    }
    return jsonify({"dates": df["DATE"].tolist(), "values": df["SOFR"].tolist(), "stats": stats})


@app.route("/api/download", methods=["GET"])
def api_download():
    """
    Descarga el Excel generado.
    Respuesta construida con headers explícitos para máxima compatibilidad
    entre navegadores (evita el problema del nombre UUID en Opera/Chrome).
    """
    if not os.path.exists(EXCEL_FILE):
        return jsonify({"error": "Archivo no encontrado. Actualiza primero."}), 404

    fname = f"historico_sofr_{datetime.now().strftime('%Y%m%d')}.xlsx"
    data  = Path(EXCEL_FILE).read_bytes()

    resp = make_response(data)
    resp.headers["Content-Type"]        = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    resp.headers["Content-Disposition"] = f'attachment; filename="{fname}"; filename*=UTF-8\'\'{fname}'
    resp.headers["Content-Length"]      = len(data)
    resp.headers["Cache-Control"]       = "no-cache, no-store, must-revalidate"
    resp.headers["X-Filename"]          = fname
    return resp


@app.route("/", methods=["GET"])
def index():
    """Sirve el frontend."""
    return (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
