# 📈 SOFR Dashboard

Panel web interactivo que obtiene, mantiene y visualiza el histórico diario de la tasa **SOFR** (Secured Overnight Financing Rate) desde la **API oficial de FRED** (Federal Reserve Bank of St. Louis).

---

## 📁 Estructura del proyecto

```
get_sofr/
├── get_sofr.py          ← Script original (NO modificado)
├── app.py               ← Servidor Flask
├── vercel.json          ← Configuración de despliegue en Vercel
├── requirements.txt     ← Dependencias Python
├── .env                 ← API key local (NO va a GitHub)
├── .env.example         ← Plantilla para otros desarrolladores
├── .gitignore           ← Excluye .env y el Excel generado
├── templates/
│   └── index.html       ← Frontend del dashboard
└── README.md
```

---

## 🔑 API Key — cómo funciona la seguridad

| Lugar | Cómo se guarda la clave |
|-------|------------------------|
| **Local** | Archivo `.env` (excluido de Git por `.gitignore`) |
| **GitHub** | La clave **no aparece** — `.env` está ignorado |
| **Vercel** | Panel → Settings → Environment Variables |

En todos los casos el código la lee igual: `os.getenv("FRED_API_KEY")`. Nunca está escrita directamente en el código fuente.

---

## 🚀 Ejecución local

### 1. Instalar dependencias
```powershell
pip install -r requirements.txt
```

### 2. Lanzar el servidor
```powershell
python app.py
```

### 3. Abrir en el navegador
**http://localhost:5000**

> El archivo `.env` ya incluye la clave de API configurada.

---

## ☁️ Despliegue en Vercel

### 1. Subir a GitHub
```bash
git init
git add .
git commit -m "SOFR Dashboard"
git remote add origin https://github.com/tu-usuario/get_sofr.git
git push -u origin main
```

### 2. Importar en Vercel
1. Ir a [vercel.com](https://vercel.com) → **Add New Project**
2. Seleccionar el repositorio `get_sofr`
3. Antes de hacer Deploy → ir a **Environment Variables**
4. Agregar: `FRED_API_KEY` = `tu_clave_de_fred`
5. Click en **Deploy**

> La clave nunca es visible en el código de GitHub. Solo existe dentro de Vercel de forma segura.

---

## 🖥️ Funcionalidades del Dashboard

| Acción | Descripción |
|--------|-------------|
| **⟳ Actualizar datos** | Llama al script original y actualiza el historial con los datos más recientes de FRED |
| **⬇ Descargar Excel** | Descarga `historico_sofr_YYYYMMDD.xlsx` |
| **↺ Refrescar gráfico** | Recarga el gráfico sin nueva petición a FRED |
| **Filtros 3M / 6M / 1A / 3A / Todo** | Filtra el gráfico por ventana de tiempo |

---

## ❓ Notas técnicas

- **¿Se modificó `get_sofr.py`?** No. Se importa como módulo y se llama `update_sofr_official_api()`.
- **Vercel y el archivo Excel:** Vercel es serverless — el Excel se guarda en `/tmp` y persiste durante la sesión activa. Presionar "Actualizar" siempre obtiene los datos más recientes.
- **Clave de la API:** Obtenla gratis en [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html).
