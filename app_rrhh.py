
import streamlit as st
import pandas as pd
import sqlite3
import io
import hashlib
import secrets
import json
import re
import unicodedata
from streamlit_folium import st_folium
import folium
from datetime import datetime, timedelta, date, time
from pathlib import Path

# ============================================================
# PORTAL CORPORATIVO RRHH - DR. SIMI
# ============================================================
# Versión integral:
# - Login corporativo y control de sesión
# - Contraseñas con PBKDF2
# - Roles y permisos
# - Dashboard ejecutivo
# - Personas / fichas
# - Asistencia y control de jornada
# - Vacaciones / permisos
# - Licencias
# - Coberturas / movimientos
# - Incidencias / bitácora
# - Alertas QF
# - Reportes y exportación
# - Carga masiva segura con previsualización
# - Backup / restauración
# - Auditoría
# ============================================================

st.set_page_config(
    page_title="Portal Corporativo RRHH | Dr. Simi",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_NAME = "base_rrhh_corporativa.db"
UPLOAD_DIR = Path("backups_rrhh")
UPLOAD_DIR.mkdir(exist_ok=True)

ROLES = [
    "Admin Supremo",
    "Jefatura RRHH",
    "Encargado Asistencia",
    "Supervisor Zonal",
    "Gestor RRHH",
    "Auditoría Operativa",
]

PERMISSIONS = {
    "Admin Supremo": {"*"},
    "Jefatura RRHH": {
        "dashboard", "personas", "asistencia", "vacaciones", "licencias",
        "coberturas", "incidencias", "reportes", "sucursales"
    },
    "Encargado Asistencia": {
        "dashboard", "personas", "asistencia", "vacaciones", "licencias",
        "coberturas", "incidencias", "reportes", "sucursales"
    },
    "Supervisor Zonal": {
        "dashboard", "personas", "asistencia", "vacaciones", "licencias",
        "coberturas", "incidencias", "reportes", "sucursales"
    },
    "Gestor RRHH": {
        "dashboard", "personas", "asistencia", "vacaciones", "licencias",
        "coberturas", "incidencias", "reportes", "sucursales"
    },
    "Auditoría Operativa": {
        "dashboard", "reportes", "sucursales", "incidencias"
    },
}


# -------------------------
# Estilos
# -------------------------
st.markdown(
    """
    <style>
    :root{
      --navy:#062543; --navy2:#0b355c; --blue:#1f5bd5;
      --blue2:#eaf2ff; --bg:#f4f7fb; --text:#142a40; --muted:#687b8f;
      --border:#d8e2ec; --white:#ffffff; --green:#198754; --yellow:#b7791f; --red:#c53030;
    }

    #MainMenu, footer, header {visibility:hidden;}
    .stApp{background:var(--bg) !important;color:var(--text) !important;}
    section[data-testid="stSidebar"]{
      background:linear-gradient(180deg,var(--navy) 0%,var(--navy2) 100%) !important;
      border-right:1px solid rgba(255,255,255,.08);
    }
    section[data-testid="stSidebar"] *{color:#fff !important;}
    .block-container{max-width:1480px;padding-top:1.7rem;padding-bottom:2.5rem;}

    /* Executive header / text */
    .title{font-size:32px;font-weight:850;line-height:1.15;color:var(--navy) !important;margin:0 0 4px 0;}
    .subtitle{font-size:14px;color:var(--muted) !important;margin:0 0 22px 0;}
    h1,h2,h3,h4,h5,h6{color:var(--navy) !important;}
    .section{
      background:var(--navy);color:#fff !important;border-radius:11px;
      padding:12px 16px;margin:18px 0 12px 0;font-weight:800;
      box-shadow:0 3px 12px rgba(6,37,67,.10);
    }
    .section *{color:#fff !important;}

    /* Sidebar */
    .brand{padding:10px 5px 18px;text-align:center;border-bottom:1px solid rgba(255,255,255,.16);margin-bottom:16px;}
    .brand-title{font-size:25px;font-weight:950;letter-spacing:1.3px;color:#fff;}
    .brand-sub{font-size:10px;font-weight:700;opacity:.78;letter-spacing:1.2px;text-transform:uppercase;color:#dbeafe;}
    section[data-testid="stSidebar"] .stRadio label{font-weight:600 !important;}
    section[data-testid="stSidebar"] .stButton > button{
      background:#fff !important;color:var(--navy) !important;border:1px solid #dce6f0 !important;
      font-weight:800 !important;border-radius:9px !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover{background:#edf4ff !important;color:var(--navy) !important;}
    section[data-testid="stSidebar"] .stButton > button,
    section[data-testid="stSidebar"] .stButton > button *,
    section[data-testid="stSidebar"] .stButton > button span{
      color:var(--navy) !important;
    }

    /* Cards / metrics */
    .card{background:#fff;border:1px solid var(--border);border-radius:15px;padding:18px;height:100%;
      box-shadow:0 5px 18px rgba(16,42,67,.055);}
    .metric-label{font-size:12px;color:#5d7084 !important;}
    .metric-value{font-size:29px;font-weight:900;color:var(--navy) !important;margin-top:5px;}
    .metric-note{font-size:10px;color:#8393a5 !important;margin-top:2px;}

    /* Inputs, selects, textareas - visibles y ejecutivos */
    label,[data-testid="stWidgetLabel"] *, .stMarkdown p{color:var(--text) !important;}

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stDateInput input,
    .stTimeInput input,
    .stSelectbox input {
      color:var(--text) !important;
      background:#f4f8fc !important;
      border:1.5px solid #9fb3c7 !important;
      border-radius:9px !important;
      box-shadow:inset 0 1px 2px rgba(6,37,67,.04) !important;
    }

    .stTextInput input:hover,
    .stTextArea textarea:hover,
    .stNumberInput input:hover,
    .stDateInput input:hover,
    .stTimeInput input:hover,
    .stSelectbox input:hover {
      background:#eef5fb !important;
      border-color:#718da8 !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stNumberInput input:focus,
    .stDateInput input:focus,
    .stTimeInput input:focus {
      background:#ffffff !important;
      border:2px solid var(--blue) !important;
      box-shadow:0 0 0 2px rgba(31,91,213,.10) !important;
    }

    input::placeholder,textarea::placeholder{color:#788b9f !important;opacity:1 !important;}

    /* Selectores */
    div[data-baseweb="select"] > div{
      min-height:42px !important;
      background:#f4f8fc !important;
      color:var(--text) !important;
      border:1.5px solid #9fb3c7 !important;
      border-radius:9px !important;
      box-shadow:inset 0 1px 2px rgba(6,37,67,.04) !important;
    }
    div[data-baseweb="select"] > div:hover{
      background:#eef5fb !important;
      border-color:#718da8 !important;
    }
    div[data-baseweb="select"] *{color:var(--text) !important;}
    div[data-baseweb="popover"],div[role="listbox"],ul[role="listbox"]{
      background:#ffffff !important;
      border:1px solid #c6d4e2 !important;
      box-shadow:0 10px 30px rgba(16,42,67,.14) !important;
    }
    div[role="option"]{background:#ffffff !important;color:var(--text) !important;}
    div[role="option"]:hover{background:#eaf2ff !important;color:var(--navy) !important;}

    /* Date/Time controls */
    [data-testid="stDateInput"] button,
    [data-testid="stTimeInput"] button{
      color:var(--navy) !important;
      background:#e8f0f8 !important;
      border-left:1px solid #9fb3c7 !important;
    }

    /* Checkboxes / radios */
    [data-testid="stCheckbox"] label,
    [data-testid="stRadio"] label {color:var(--text) !important;}
    [data-testid="stCheckbox"] input:checked + div,
    [data-testid="stRadio"] input:checked + div{
      border-color:var(--blue) !important;
      background:var(--blue) !important;
    }

    /* Buttons */
    .stButton > button,.stDownloadButton > button{
      background:var(--navy) !important;color:#fff !important;border:1px solid var(--navy) !important;
      border-radius:9px !important;font-weight:800 !important;min-height:40px;
    }
    .stButton > button:hover,.stDownloadButton > button:hover{
      background:#10436d !important;color:#fff !important;border-color:#10436d !important;
    }
    .stFormSubmitButton > button{
      background:var(--blue) !important;color:#fff !important;border-color:var(--blue) !important;
      font-weight:900 !important;min-height:44px !important;
    }
    .stFormSubmitButton > button:hover{background:#1848ab !important;color:#fff !important;}

    /* Forms */
    div[data-testid="stForm"]{
      background:#fff !important;border:1px solid var(--border) !important;border-radius:16px !important;
      padding:23px !important;box-shadow:0 9px 28px rgba(16,42,67,.07) !important;
    }
    div[data-testid="stForm"] label,div[data-testid="stForm"] p{color:var(--text) !important;}

    /* Dataframe */
    [data-testid="stDataFrame"]{background:#fff !important;border:1px solid var(--border) !important;border-radius:10px !important;overflow:hidden;}

    /* Login - all real Streamlit widgets stay inside the centered column */
    .login-page-bg{
      background:radial-gradient(circle at 84% 10%,#1c4a78 0%,#0a2038 40%,#020b18 100%) !important;
      min-height:100vh !important;
    }
    .login-brand-main{text-align:center;color:#fff;font-size:42px;font-weight:950;letter-spacing:2.2px;margin:2vh 0 2px;}
    .login-brand-line{width:58px;height:3px;background:#4d7ff0;margin:9px auto 11px;border-radius:3px;}
    .login-brand-sub{text-align:center;color:#c1d2e5;font-size:12px;letter-spacing:2px;text-transform:uppercase;margin-bottom:20px;}
    .login-small{text-align:center;color:#9eb2c7;font-size:11px;margin-top:15px;}
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# Database
# -------------------------
def db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def ensure_columns(cur, table_name, columns):
    """
    Agrega columnas faltantes sin borrar información de una base existente.
    columns: dict {nombre_columna: tipo_sql}
    """
    existing = {row[1] for row in cur.execute(f"PRAGMA table_info({table_name})").fetchall()}
    for name, col_type in columns.items():
        if name not in existing:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {name} {col_type}")


def init_db():
    con = db()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sucursales (
            codigo TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            direccion TEXT,
            comuna TEXT,
            region TEXT,
            director_tecnico TEXT,
            dt_complementario TEXT,
            latitud REAL,
            longitud REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS colaboradores (
            rut TEXT PRIMARY KEY,
            nombre_completo TEXT NOT NULL,
            codigo_sucursal TEXT,
            cargo TEXT,
            celular TEXT,
            email TEXT,
            jornada_horas REAL DEFAULT 40,
            activo INTEGER DEFAULT 1
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes (
            id_solicitud TEXT PRIMARY KEY,
            estado TEXT,
            rut TEXT,
            nombre TEXT,
            cargo TEXT,
            codigo_sucursal TEXT,
            fecha_desde TEXT,
            fecha_hasta TEXT,
            dias INTEGER,
            tipo TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS licencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rut TEXT,
            nombre TEXT,
            apellido_p TEXT,
            apellido_m TEXT,
            sucursal TEXT,
            cargo TEXT,
            fecha_desde TEXT,
            fecha_hasta TEXT,
            dias INTEGER,
            tipo_ausencia TEXT,
            estado TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_registro TIMESTAMP,
            usuario_realiza TEXT,
            rut_colaborador TEXT,
            sucursal_origen TEXT,
            sucursal_destino TEXT,
            rut_reemplazado TEXT,
            fecha_inicio DATE,
            fecha_fin DATE,
            nuevo_horario TEXT,
            motivo TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bitacora_diaria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP,
            sucursal TEXT,
            usuario TEXT,
            novedad TEXT,
            prioridad TEXT DEFAULT 'Media',
            estado TEXT DEFAULT 'Abierta'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS incidencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP,
            fecha_evento DATE,
            sucursal TEXT,
            rut TEXT,
            tipo TEXT,
            descripcion TEXT,
            prioridad TEXT,
            estado TEXT,
            responsable TEXT,
            fecha_cierre TIMESTAMP,
            resolucion TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS asistencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            rut TEXT NOT NULL,
            codigo_sucursal TEXT,
            entrada TEXT,
            salida TEXT,
            colacion_min INTEGER DEFAULT 30,
            estado TEXT DEFAULT 'Completa',
            observacion TEXT,
            UNIQUE(fecha, rut)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            nombre_completo TEXT NOT NULL,
            rol TEXT NOT NULL,
            activo INTEGER DEFAULT 1
        )
    """)

    # Migración compatible con la versión anterior, que no tenía columna activo.
    cols_usuarios = [row[1] for row in cur.execute("PRAGMA table_info(usuarios)").fetchall()]
    if "activo" not in cols_usuarios:
        cur.execute("ALTER TABLE usuarios ADD COLUMN activo INTEGER DEFAULT 1")


    cur.execute("""
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TIMESTAMP,
            usuario TEXT,
            accion TEXT,
            detalle TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ausentismo_historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rut TEXT,
            nombre TEXT,
            empresa TEXT,
            cargo TEXT,
            gerencia TEXT,
            sucursal TEXT,
            centro_costo TEXT,
            tipo_ausencia TEXT,
            motivo_ausencia TEXT,
            dias INTEGER,
            fecha_inicio TEXT,
            fecha_fin TEXT,
            hora_inicio TEXT,
            hora_fin TEXT,
            horas TEXT,
            minutos TEXT,
            fecha_creacion TEXT,
            observaciones TEXT,
            activo INTEGER DEFAULT 0,
            dias_restantes INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS solicitudes_historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id TEXT,
            fecha_solicitud TEXT,
            estado TEXT,
            rut TEXT,
            nombre_fuente TEXT,
            nombre_colaborador TEXT,
            cargo TEXT,
            codigo_sucursal TEXT,
            dias INTEGER,
            tipo TEXT,
            detalle TEXT,
            en_proceso INTEGER DEFAULT 0
        )
    """)
    # Migración de columnas nuevas para bases de versiones anteriores.
    col_info = [r[1] for r in cur.execute("PRAGMA table_info(colaboradores)").fetchall()]
    if "sucursal_nombre" not in col_info:
        cur.execute("ALTER TABLE colaboradores ADD COLUMN sucursal_nombre TEXT")
    if "vigencia" not in col_info:
        cur.execute("ALTER TABLE colaboradores ADD COLUMN vigencia TEXT")
    if "sucursal_bm" not in col_info:
        cur.execute("ALTER TABLE colaboradores ADD COLUMN sucursal_bm TEXT")
    if "datos_json" not in col_info:
        cur.execute("ALTER TABLE colaboradores ADD COLUMN datos_json TEXT")

    # Migración completa de Sucursales para compatibilidad con el cargador oficial.
    ensure_columns(cur, "sucursales", {
        "ciudad": "TEXT",
        "telefono": "TEXT",
        "telfdt": "TEXT",
        "telfdt2": "TEXT",
        "horario_lunes_viernes": "TEXT",
        "horario_sabado": "TEXT",
        "horario_domingo": "TEXT",
        "fecha_apertura": "TEXT",
        "supervisor": "TEXT",
        "jefe_comercial": "TEXT",
        "email": "TEXT",
        "geolocalizacion": "TEXT",
        "ecommerce": "TEXT",
    })

    # Migración de Solicitudes para el historial general oficial.
    ensure_columns(cur, "solicitudes", {
        "fecha_solicitud": "TEXT",
        "detalle": "TEXT",
        "en_proceso": "INTEGER DEFAULT 0",
    })

    # Índices útiles para las consultas del dashboard y alertas.

    # Campos ampliados del Directorio oficial. Se agregan sin borrar información.
    ensure_columns(cur, "sucursales", {
        "ciudad": "TEXT",
        "telefono": "TEXT",
        "telfdt": "TEXT",
        "telfdt2": "TEXT",
        "horario_lunes_viernes": "TEXT",
        "horario_sabado": "TEXT",
        "horario_domingo": "TEXT",
        "fecha_apertura": "TEXT",
        "supervisor": "TEXT",
        "jefe_comercial": "TEXT",
        "email": "TEXT",
        "geolocalizacion": "TEXT",
        "ecommerce": "TEXT",
    })

    cur.execute("CREATE INDEX IF NOT EXISTS idx_aus_active ON ausentismo_historico(activo)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_aus_rut ON ausentismo_historico(rut)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_aus_branch ON ausentismo_historico(sucursal)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sol_process ON solicitudes_historial(en_proceso)")

    count = cur.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    if count == 0:
        cur.execute(
            "INSERT INTO usuarios VALUES (?,?,?,?,?)",
            ("admin", hash_password("simi2026"), "Administrador Maestro RRHH", "Admin Supremo", 1),
        )
    else:
        # Mantener compatibilidad con el admin creado por la versión antigua.
        admin_row = cur.execute(
            "SELECT password,activo FROM usuarios WHERE usuario='admin'"
        ).fetchone()
        if admin_row and admin_row[0] == "simi2026":
            cur.execute(
                "UPDATE usuarios SET password=?, activo=1 WHERE usuario='admin'",
                (hash_password("simi2026"),)
            )

    defaults = {
        "jornada_qf": "40",
        "jornada_af": "42",
        "tolerancia_atraso_min": "10",
        "hora_inicio_operativa": "08:00",
    }
    for key, value in defaults.items():
        cur.execute(
            "INSERT OR IGNORE INTO configuracion(clave,valor) VALUES(?,?)",
            (key, value),
        )

    con.commit()
    return con



# -------------------------
# Seguridad
# -------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    rounds = 160000
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), rounds
    ).hex()
    return f"pbkdf2_sha256${rounds}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, rounds, salt, digest = stored.split("$", 3)
            calc = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(rounds)
            ).hex()
            return secrets.compare_digest(calc, digest)
        except Exception:
            return False
    # Compatibilidad con usuarios creados por la versión anterior.
    return secrets.compare_digest(password, stored)


def can(permission: str) -> bool:
    role = st.session_state.get("rol_actual", "")
    return "*" in PERMISSIONS.get(role, set()) or permission in PERMISSIONS.get(role, set())


def audit(action: str, detail: str = ""):
    try:
        con = db()
        con.execute(
            "INSERT INTO auditoria(fecha,usuario,accion,detalle) VALUES(?,?,?,?)",
            (datetime.now(), st.session_state.get("usuario_actual", ""), action, detail),
        )
        con.commit()
        con.close()
    except Exception:
        pass


# Database connection is initialized only after security helpers exist.
conn = init_db()

# -------------------------
# Helpers
# -------------------------
@st.cache_data(ttl=45)
def query_df(sql, params=()):
    con = db()
    try:
        return pd.read_sql_query(sql, con, params=params)
    finally:
        con.close()


def execute(sql, params=()):
    con = db()
    cur = con.cursor()
    cur.execute(sql, params)
    con.commit()
    con.close()


def excel_bytes(df, sheet_name="Reporte"):
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return out.getvalue()


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8-sig")


def safe_num(v, default=0):
    try:
        return float(v)
    except Exception:
        return default


def parse_time(value):
    if pd.isna(value):
        return None
    txt = str(value).strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(txt, fmt).time()
        except Exception:
            pass
    return None


def net_hours(entrada, salida, colacion_min=30):
    e = parse_time(entrada) if not isinstance(entrada, time) else entrada
    s = parse_time(salida) if not isinstance(salida, time) else salida
    if not e or not s:
        return 0.0
    de = datetime.combine(date.today(), e)
    ds = datetime.combine(date.today(), s)
    if ds < de:
        ds += timedelta(days=1)
    mins = max(0, (ds - de).total_seconds() / 60 - int(colacion_min or 0))
    return round(mins / 60, 2)


def get_config(key, default=""):
    row = query_df("SELECT valor FROM configuracion WHERE clave=?", (key,))
    return str(row.iloc[0, 0]) if not row.empty else default


def set_config(key, value):
    execute(
        "INSERT INTO configuracion(clave,valor) VALUES(?,?) "
        "ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor",
        (key, str(value)),
    )


def download_backup():
    con = db()
    out = io.BytesIO()
    # SQLite online backup hacia una base temporal en disco.
    tmp = UPLOAD_DIR / f"backup_{datetime.now():%Y%m%d_%H%M%S}.db"
    target = sqlite3.connect(str(tmp))
    con.backup(target)
    target.close()
    con.close()
    return tmp


def normalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def get_col(df, aliases, default=""):
    mapping = {str(c).strip().lower(): c for c in df.columns}
    for alias in aliases:
        if alias.lower() in mapping:
            return df[mapping[alias.lower()]]
    for c in df.columns:
        cl = str(c).strip().lower()
        if any(alias.lower() in cl for alias in aliases):
            return df[c]
    return pd.Series([default] * len(df), index=df.index)


# -------------------------
# Datos oficiales / alertas
# -------------------------
def normalize_text(value):
    txt = "" if value is None else str(value).strip().upper()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9]+", " ", txt)).strip()


def excel_serial_to_iso(value):
    try:
        if value in ("", None):
            return ""
        # Acepta serial Excel y formatos de fecha comunes.
        if isinstance(value, (int, float)) or str(value).replace(".", "", 1).isdigit():
            return (datetime(1899, 12, 30) + timedelta(days=float(value))).strftime("%Y-%m-%d")
        dt = pd.to_datetime(value, errors="coerce")
        return "" if pd.isna(dt) else dt.strftime("%Y-%m-%d")
    except Exception:
        return ""


def current_absences(limit=500):
    hoy = date.today().isoformat()
    return query_df(f'''
        SELECT id AS ID, rut AS RUT, nombre AS Colaborador, cargo AS Cargo,
               sucursal AS Sucursal, tipo_ausencia AS "Tipo Ausencia",
               fecha_inicio AS "Fecha Inicio", fecha_fin AS "Fecha Término",
               dias AS Días,
               CAST(julianday(fecha_fin)-julianday(?) AS INTEGER) AS "Días restantes",
               CASE
                 WHEN date(fecha_fin)=date(?) THEN 'RETORNO HOY'
                 WHEN julianday(fecha_fin)-julianday(?) <= 3 THEN 'RETORNO PRÓXIMO'
                 ELSE 'ACTIVO'
               END AS Alerta
        FROM ausentismo_historico
        WHERE date(fecha_inicio) <= date(?)
          AND date(fecha_fin) >= date(?)
        ORDER BY date(fecha_fin), nombre
        LIMIT {int(limit)}
    ''', (hoy,hoy,hoy,hoy,hoy))


def upcoming_absences(days_ahead=7, limit=500):
    hoy = date.today().isoformat()
    return query_df(f'''
        SELECT id AS ID, rut AS RUT, nombre AS Colaborador, cargo AS Cargo,
               sucursal AS Sucursal, tipo_ausencia AS "Tipo Ausencia",
               fecha_inicio AS "Fecha Inicio", fecha_fin AS "Fecha Término",
               dias AS Días
        FROM ausentismo_historico
        WHERE date(fecha_inicio) > date(?)
          AND date(fecha_inicio) <= date(?, '+{int(days_ahead)} day')
        ORDER BY date(fecha_inicio), nombre
        LIMIT {int(limit)}
    ''', (hoy,hoy))


def requests_in_process(limit=500):
    return query_df(f"""
        SELECT h.id AS ID, h.fecha_solicitud AS 'Fecha Solicitud',
               h.estado AS Estado, h.rut AS RUT,
               COALESCE(c.nombre_completo,h.nombre_colaborador,h.nombre_fuente) AS Colaborador,
               h.cargo AS Cargo, s.nombre AS Sucursal,
               h.dias AS Días, h.tipo AS Tipo, h.en_proceso AS 'En proceso'
        FROM solicitudes_historial h
        LEFT JOIN colaboradores c ON h.rut=c.rut
        LEFT JOIN sucursales s ON h.codigo_sucursal=s.codigo
        WHERE h.en_proceso=1
        ORDER BY datetime(h.fecha_solicitud) DESC
        LIMIT {int(limit)}
    """)


def style_alert_rows(df, alert_col="Alerta"):
    if df.empty or alert_col not in df.columns:
        return df
    def row_style(row):
        color = "#ffe2e2"
        if str(row.get(alert_col,"")) == "RETORNO PRÓXIMO":
            color = "#fff1cc"
        elif str(row.get(alert_col,"")) == "ACTIVO":
            color = "#eef7ee"
        return [f"background-color:{color}" for _ in row.index]
    return df.style.apply(row_style, axis=1)


# -------------------------
# Estado de sesión
# -------------------------
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_actual = ""
    st.session_state.rol_actual = ""
    st.session_state.login_intentos = 0
    st.session_state.bloqueo_hasta = None


# -------------------------
# Login
# -------------------------
if not st.session_state.autenticado:
    # Login limpio: columnas reales de Streamlit + formulario real.
    st.markdown(
        """
        <style>
        .stApp{background:radial-gradient(circle at 84% 10%,#1c4a78 0%,#0a2038 40%,#020b18 100%) !important;}
        [data-testid="stMainViewContainer"]{background:transparent !important;}
        section[data-testid="stMain"]{background:transparent !important;}
        .block-container{min-height:100vh;max-width:1200px;padding-top:3vh !important;padding-bottom:40px !important;}
        div[data-testid="stForm"]{
          max-width:520px;margin:0 auto !important;background:rgba(255,255,255,.98) !important;
          border:1px solid rgba(255,255,255,.55) !important;border-radius:20px !important;
          padding:28px !important;box-shadow:0 24px 70px rgba(0,0,0,.34) !important;
        }
        div[data-testid="stForm"] input{
          background:#f2f6fb !important;
          border:1.5px solid #9fb3c7 !important;
          color:#142a40 !important;
        }
        div[data-testid="stForm"] input:focus{
          background:#fff !important;
          border:2px solid #1f5bd5 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    spacer_l, center, spacer_r = st.columns([1, 1.2, 1])
    with center:
        st.markdown('<div class="login-brand-main">DR. SIMI</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-brand-line"></div>', unsafe_allow_html=True)
        st.markdown('<div class="login-brand-sub">Portal Corporativo de Gestión RRHH</div>', unsafe_allow_html=True)

        bloqueo = st.session_state.bloqueo_hasta
        if bloqueo and datetime.now() < bloqueo:
            st.error("Acceso temporalmente bloqueado por múltiples intentos fallidos.")
            st.stop()

        with st.form("login_form", clear_on_submit=False):
            st.markdown(
                "<div style='text-align:center;font-size:20px;font-weight:850;color:#062543;margin-bottom:18px;'>"
                "🔐 Identificación segura</div>",
                unsafe_allow_html=True
            )
            usuario = st.text_input("Usuario", placeholder="Ingrese su usuario", autocomplete="username")
            password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña", autocomplete="current-password")
            ingresar = st.form_submit_button("INGRESAR AL PORTAL", use_container_width=True)

        st.markdown(
            "<div class='login-small'>Acceso interno · Recursos Humanos · Dr. Simi</div>",
            unsafe_allow_html=True
        )

        if ingresar:
            con = db()
            row = con.execute(
                "SELECT usuario,password,nombre_completo,rol,activo FROM usuarios WHERE usuario=?",
                (usuario.strip(),),
            ).fetchone()
            con.close()

            if row and row[4] == 1 and verify_password(password, row[1]):
                if not str(row[1]).startswith("pbkdf2_sha256$"):
                    execute(
                        "UPDATE usuarios SET password=? WHERE usuario=?",
                        (hash_password(password), row[0]),
                    )
                st.session_state.autenticado = True
                st.session_state.usuario_actual = row[2]
                st.session_state.usuario_login = row[0]
                st.session_state.rol_actual = row[3]
                st.session_state.login_intentos = 0
                st.session_state.bloqueo_hasta = None
                audit("LOGIN", f"Inicio de sesión: {row[0]}")
                st.rerun()
            else:
                st.session_state.login_intentos += 1
                audit("LOGIN_FALLIDO", f"Usuario intentado: {usuario.strip()}")
                if st.session_state.login_intentos >= 5:
                    st.session_state.bloqueo_hasta = datetime.now() + timedelta(minutes=5)
                    st.error("Demasiados intentos. Espere 5 minutos para volver a intentar.")
                else:
                    st.error("Credenciales inválidas o usuario desactivado.")
    st.stop()


# -------------------------
# Sidebar
# -------------------------
st.sidebar.markdown(
    """
    <div class="brand">
        <div class="brand-title">DR. SIMI</div>
        <div class="brand-sub">Operaciones & RRHH</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    f"**👤 {st.session_state.usuario_actual}**<br><span style='font-size:11px;opacity:.75;'>"
    f"{st.session_state.rol_actual}</span>",
    unsafe_allow_html=True,
)

menu = []
if can("dashboard"):
    menu.append("🏠 Inicio / Dashboard")
if can("personas"):
    menu.append("👥 Personas")
if can("asistencia"):
    menu.append("🕐 Asistencia")
if can("vacaciones"):
    menu.append("🏖️ Vacaciones y Permisos")
if can("licencias"):
    menu.append("🏥 Licencias")
if can("coberturas"):
    menu.append("🔄 Coberturas y Movimientos")
if can("sucursales"):
    menu.append("🏪 Sucursales")
    menu.append("🗺️ Mapa de Sucursales")
if can("incidencias"):
    menu.append("🚨 Alertas de Ausentismo")
    menu.append("🚨 Incidencias y Bitácora")
if can("reportes"):
    menu.append("📈 Reportes")
if st.session_state.rol_actual == "Admin Supremo":
    menu += ["👤 Usuarios", "🛡️ Auditoría", "⚙️ Configuración"]

menu.append("ℹ️ Ayuda")
opcion = st.sidebar.radio("Navegación", menu)

st.sidebar.markdown("---")
st.sidebar.caption(f"Sesión: {datetime.now():%d-%m-%Y %H:%M}")

if st.sidebar.button("🚪 CERRAR SESIÓN", use_container_width=True):
    audit("LOGOUT", "Cierre de sesión")
    for key in ["autenticado", "usuario_actual", "rol_actual", "usuario_login"]:
        st.session_state.pop(key, None)
    st.session_state.autenticado = False
    st.rerun()


def page_title(title, subtitle=""):
    st.markdown(
        f"""
        <div style="display:flex;justify-content:space-between;align-items:flex-end;
                    border-bottom:1px solid #dce5ee;padding-bottom:12px;margin-bottom:18px;">
            <div>
                <div class="title">{title}</div>
                <div class="subtitle" style="margin-bottom:0;">{subtitle}</div>
            </div>
            <div style="text-align:right;font-size:11px;color:#6b7f93;">
                <b style="color:#0b355c;">{st.session_state.get("rol_actual","")}</b><br>
                {datetime.now():%d/%m/%Y · %H:%M}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DASHBOARD
# ============================================================
if opcion == "🏠 Inicio / Dashboard":
    page_title(
        "Centro de Control RRHH",
        f"Bienvenido/a, {st.session_state.usuario_actual}. Resumen operacional.",
    )

    tot_suc = int(query_df("SELECT COUNT(*) n FROM sucursales").iloc[0, 0])
    tot_col = int(query_df("SELECT COUNT(*) n FROM colaboradores WHERE activo=1").iloc[0, 0])
    hoy = date.today().isoformat()
    tot_aus = int(query_df("SELECT COUNT(*) n FROM ausentismo_historico WHERE date(fecha_inicio)<=date(?) AND date(fecha_fin)>=date(?)",(hoy,hoy)).iloc[0, 0])
    tot_cov = int(query_df("SELECT COUNT(*) n FROM movimientos WHERE date(fecha_inicio)<=date(?) AND date(fecha_fin)>=date(?)",(hoy,hoy)).iloc[0, 0])
    tot_inc = int(query_df("SELECT COUNT(*) n FROM incidencias WHERE estado<>'Cerrada'").iloc[0, 0])
    tot_proc = int(query_df("SELECT COUNT(*) n FROM solicitudes_historial WHERE en_proceso=1").iloc[0, 0])
    tot_fin3 = int(query_df("SELECT COUNT(*) n FROM ausentismo_historico WHERE date(fecha_inicio)<=date(?) AND date(fecha_fin)>=date(?) AND julianday(fecha_fin)-julianday(?) BETWEEN 0 AND 3",(hoy,hoy,hoy)).iloc[0, 0])

    metrics = [
        ("🏪 Sucursales", tot_suc),
        ("👥 Colaboradores activos", tot_col),
        ("🏥 Ausencias activas", tot_aus),
        ("🔄 Coberturas activas", tot_cov),
        ("🏖️ Solicitudes en proceso", tot_proc),
        ("⏰ Retornos próximos (≤3 días)", tot_fin3),
    ]

    cols = st.columns(6)
    for col, (label, val) in zip(cols, metrics):
        with col:
            st.markdown(
                f'<div class="card"><div class="metric-label">{label}</div>'
                f'<div class="metric-value">{val}</div><div class="metric-note">Actualizado al ingresar</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section">🚨 Alertas de Ausentismo y Continuidad</div>', unsafe_allow_html=True)

    active_df = current_absences(120)
    soon_df = upcoming_absences(7, 60)

    if active_df.empty:
        st.success("🟢 No hay personas con ausentismo activo según las fechas cargadas.")
    else:
        st.warning(f"⚠️ Actualmente hay **{len(active_df)} registros de ausentismo activos**. Revise las coberturas asociadas.")
        st.dataframe(style_alert_rows(active_df), use_container_width=True, hide_index=True)

    if not soon_df.empty:
        st.info(f"📅 Hay **{len(soon_df)} ausentismos futuros** dentro de los próximos 7 días.")
        with st.expander("Ver próximos ausentismos"):
            st.dataframe(soon_df, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section">🏥 Licencias por tipo</div>', unsafe_allow_html=True)
        df = query_df("""
            SELECT COALESCE(tipo_ausencia,'Sin tipo') Tipo, COUNT(*) Cantidad
            FROM licencias GROUP BY tipo_ausencia ORDER BY Cantidad DESC
        """)
        if df.empty:
            st.info("Sin licencias cargadas.")
        else:
            st.bar_chart(df.set_index("Tipo"))

    with c2:
        st.markdown('<div class="section">🏪 Sucursales por región</div>', unsafe_allow_html=True)
        df = query_df("""
            SELECT COALESCE(region,'Sin región') Región, COUNT(*) Cantidad
            FROM sucursales GROUP BY region ORDER BY Cantidad DESC
        """)
        if df.empty:
            st.info("Sin sucursales cargadas.")
        else:
            st.bar_chart(df.set_index("Región"))


# ============================================================
# PERSONAS
# ============================================================
elif opcion == "👥 Personas":
    page_title("Gestión de Personas", "Buscador y ficha operativa del colaborador.")

    df = query_df("""
        SELECT c.rut AS RUT, c.nombre_completo AS Colaborador,
               c.cargo AS Cargo, COALESCE(c.sucursal_nombre,s.nombre,c.sucursal_bm) AS Sucursal,
               c.jornada_horas AS Jornada, c.celular AS Celular,
               c.email AS Email, c.activo AS Activo
        FROM colaboradores c
        LEFT JOIN sucursales s ON c.codigo_sucursal=s.codigo
        ORDER BY c.nombre_completo
    """)

    if df.empty:
        st.info("No existen colaboradores cargados.")
    else:
        filtro = st.text_input("🔎 Buscar por RUT, nombre, cargo o sucursal")
        if filtro:
            mask = df.astype(str).apply(
                lambda x: x.str.contains(filtro, case=False, na=False)
            ).any(axis=1)
            df = df[mask]

        st.dataframe(df, use_container_width=True, hide_index=True)

        opciones = df["RUT"].tolist()
        if opciones:
            rut = st.selectbox("Seleccionar colaborador", opciones)
            persona = query_df("""
                SELECT c.*, s.nombre sucursal_nombre, s.region, s.comuna
                FROM colaboradores c
                LEFT JOIN sucursales s ON c.codigo_sucursal=s.codigo
                WHERE c.rut=?
            """, (rut,))
            r = persona.iloc[0]
            st.markdown('<div class="section">👤 Ficha del colaborador</div>', unsafe_allow_html=True)

            a, b, c = st.columns(3)
            a.metric("Nombre", r["nombre_completo"])
            b.metric("Cargo", r["cargo"] or "Sin informar")
            c.metric("Jornada", f"{safe_num(r['jornada_horas'],40):g} h")

            a, b, c = st.columns(3)
            a.write(f"**RUT:** {r['rut']}")
            b.write(f"**Sucursal:** {r['sucursal_nombre'] or 'Sin asignar'}")
            c.write(f"**Región:** {r['region'] or 'Sin informar'}")
            st.write(f"**Contacto:** {r['celular'] or '-'} · {r['email'] or '-'}")

            t1, t2, t3, t4 = st.tabs(["Asistencia", "Licencias", "Vacaciones", "Coberturas"])
            with t1:
                st.dataframe(query_df("""
                    SELECT fecha,entrada,salida,colacion_min,estado,observacion
                    FROM asistencia WHERE rut=? ORDER BY date(fecha) DESC LIMIT 100
                """, (rut,)), use_container_width=True, hide_index=True)
            with t2:
                st.dataframe(query_df("""
                    SELECT fecha_desde,fecha_hasta,dias,tipo_ausencia,estado
                    FROM licencias WHERE rut=? ORDER BY date(fecha_desde) DESC
                """, (rut,)), use_container_width=True, hide_index=True)
            with t3:
                st.dataframe(query_df("""
                    SELECT fecha_desde,fecha_hasta,dias,tipo,estado
                    FROM solicitudes WHERE rut=? ORDER BY date(fecha_desde) DESC
                """, (rut,)), use_container_width=True, hide_index=True)
            with t4:
                st.dataframe(query_df("""
                    SELECT fecha_registro,sucursal_origen,sucursal_destino,fecha_inicio,fecha_fin,motivo
                    FROM movimientos WHERE rut_colaborador=? ORDER BY id DESC
                """, (rut,)), use_container_width=True, hide_index=True)


# ============================================================
# ASISTENCIA
# ============================================================
elif opcion == "🕐 Asistencia":
    page_title("Control de Asistencia", "Registro diario, jornada neta y alertas de cumplimiento.")

    tab1, tab2 = st.tabs(["📅 Registro diario", "📊 Análisis de jornada"])

    with tab1:
        fecha_reg = st.date_input("Fecha", value=date.today())
        col1, col2 = st.columns(2)
        dfc = query_df("""
            SELECT rut,nombre_completo,codigo_sucursal,cargo,jornada_horas
            FROM colaboradores WHERE activo=1 ORDER BY nombre_completo
        """)
        if dfc.empty:
            st.warning("Carga primero la nómina de colaboradores.")
        else:
            rut = col1.selectbox(
                "Colaborador",
                dfc["rut"].tolist(),
                format_func=lambda r: dfc.loc[dfc["rut"] == r, "nombre_completo"].iloc[0] + f" ({r})",
            )
            row = dfc[dfc["rut"] == rut].iloc[0]
            entrada = col1.time_input("Entrada", value=time(9,0))
            salida = col2.time_input("Salida", value=time(18,0))
            colacion = col2.number_input("Colación (minutos)", min_value=0, max_value=180, value=30, step=5)
            estado = st.selectbox("Estado", ["Completa","Atraso","Falta de marca","Inasistencia","Permiso","Licencia","Vacaciones","Descanso"])
            obs = st.text_area("Observación")

            horas = net_hours(entrada, salida, colacion)
            st.metric("Jornada neta del día", f"{horas:.2f} h")

            if st.button("💾 Guardar asistencia", type="primary"):
                execute("""
                    INSERT INTO asistencia(fecha,rut,codigo_sucursal,entrada,salida,colacion_min,estado,observacion)
                    VALUES(?,?,?,?,?,?,?,?)
                    ON CONFLICT(fecha,rut) DO UPDATE SET
                      codigo_sucursal=excluded.codigo_sucursal,
                      entrada=excluded.entrada,
                      salida=excluded.salida,
                      colacion_min=excluded.colacion_min,
                      estado=excluded.estado,
                      observacion=excluded.observacion
                """, (
                    fecha_reg.isoformat(), rut, row["codigo_sucursal"],
                    entrada.strftime("%H:%M"), salida.strftime("%H:%M"),
                    int(colacion), estado, obs
                ))
                audit("ASISTENCIA", f"{rut} {fecha_reg} {estado} {horas:.2f}h")
                st.cache_data.clear()
                st.success("Asistencia guardada correctamente.")

        st.markdown('<div class="section">Registro de la fecha seleccionada</div>', unsafe_allow_html=True)
        df = query_df("""
            SELECT a.fecha,c.nombre_completo Colaborador,c.cargo,
                   s.nombre Sucursal,a.entrada,a.salida,a.colacion_min,
                   a.estado,a.observacion
            FROM asistencia a
            LEFT JOIN colaboradores c ON a.rut=c.rut
            LEFT JOIN sucursales s ON a.codigo_sucursal=s.codigo
            WHERE a.fecha=? ORDER BY c.nombre_completo
        """, (fecha_reg.isoformat(),))
        if df.empty:
            st.info("No hay registros para esta fecha.")
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                "📥 Descargar Excel",
                excel_bytes(df, "Asistencia"),
                f"asistencia_{fecha_reg}.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with tab2:
        desde = st.date_input("Desde", value=date.today()-timedelta(days=6), key="ass_desde")
        hasta = st.date_input("Hasta", value=date.today(), key="ass_hasta")
        df = query_df("""
            SELECT a.fecha,a.rut,c.nombre_completo,c.jornada_horas,a.entrada,a.salida,a.colacion_min,a.estado
            FROM asistencia a
            LEFT JOIN colaboradores c ON a.rut=c.rut
            WHERE date(a.fecha) BETWEEN date(?) AND date(?)
            ORDER BY date(a.fecha), c.nombre_completo
        """, (desde.isoformat(), hasta.isoformat()))

        if df.empty:
            st.info("No hay asistencia en el período.")
        else:
            df["Horas netas"] = df.apply(
                lambda r: net_hours(r["entrada"], r["salida"], r["colacion_min"]), axis=1
            )
            resumen = df.groupby(["rut","nombre_completo"], as_index=False).agg(
                Dias=("fecha","count"), Horas_net=("Horas netas","sum")
            )
            resumen["Horas objetivo aprox."] = resumen["Dias"] * 8
            resumen["Diferencia"] = (resumen["Horas_net"] - resumen["Horas objetivo aprox."]).round(2)
            st.dataframe(resumen, use_container_width=True, hide_index=True)
            st.download_button(
                "📥 Descargar análisis",
                excel_bytes(resumen, "Analisis"),
                "analisis_jornada.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )


# ============================================================
# VACACIONES / PERMISOS
# ============================================================
elif opcion == "🏖️ Vacaciones y Permisos":
    page_title("Vacaciones y Permisos", "Registro, consulta y seguimiento de ausencias programadas.")

    dfc = query_df("SELECT rut,nombre_completo,codigo_sucursal,cargo FROM colaboradores WHERE activo=1 ORDER BY nombre_completo")
    if dfc.empty:
        st.warning("No existen colaboradores cargados.")
    else:
        with st.form("solicitud_form"):
            rut = st.selectbox(
                "Colaborador", dfc["rut"].tolist(),
                format_func=lambda r: dfc.loc[dfc["rut"]==r, "nombre_completo"].iloc[0]
            )
            r = dfc[dfc["rut"]==rut].iloc[0]
            tipo = st.selectbox("Tipo", ["Vacaciones","Permiso con goce","Permiso sin goce","Otro"])
            estado = st.selectbox("Estado", ["Pendiente","Pre Aprobada","Aprobada","Rechazada"])
            c1, c2 = st.columns(2)
            f1 = c1.date_input("Fecha inicio", value=date.today())
            f2 = c2.date_input("Fecha término", value=date.today())
            dias = st.number_input("Días", min_value=1, max_value=365, value=max(1,(f2-f1).days+1))
            guardar = st.form_submit_button("💾 Registrar solicitud", use_container_width=True)

        if guardar:
            if f2 < f1:
                st.error("La fecha de término no puede ser anterior al inicio.")
            else:
                sid = f"{rut}-{f1.isoformat()}-{tipo}"
                execute("""
                    INSERT INTO solicitudes(id_solicitud,estado,rut,nombre,cargo,codigo_sucursal,fecha_desde,fecha_hasta,dias,tipo)
                    VALUES(?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(id_solicitud) DO UPDATE SET
                      estado=excluded.estado, fecha_hasta=excluded.fecha_hasta,
                      dias=excluded.dias, tipo=excluded.tipo
                """, (sid, estado, rut, r["nombre_completo"], r["cargo"], r["codigo_sucursal"],
                      f1.isoformat(), f2.isoformat(), int(dias), tipo))
                audit("SOLICITUD", f"{tipo} {rut} {f1} a {f2}")
                st.cache_data.clear()
                st.success("Solicitud registrada correctamente.")

    df = query_df("""
        SELECT s.id_solicitud ID,s.estado Estado,s.tipo Tipo,s.rut RUT,s.nombre Colaborador,
               s.cargo Cargo,sc.nombre Sucursal,s.fecha_desde Inicio,s.fecha_hasta Termino,
               s.dias Días
        FROM solicitudes s LEFT JOIN sucursales sc ON s.codigo_sucursal=sc.codigo
        ORDER BY date(s.fecha_desde) DESC
    """)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.download_button("📥 Descargar Excel", excel_bytes(df, "Solicitudes"), "vacaciones_permisos.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ============================================================
# LICENCIAS
# ============================================================
elif opcion == "🏥 Licencias":
    page_title("Licencias Médicas", "Control y seguimiento del ausentismo por licencia.")

    with st.form("lic_form"):
        rut = st.text_input("RUT")
        nombre = st.text_input("Nombre")
        apellido_p = st.text_input("Apellido paterno")
        apellido_m = st.text_input("Apellido materno")
        cargo = st.text_input("Cargo")
        sucursal = st.text_input("Sucursal")
        tipo = st.selectbox("Tipo de ausencia", ["Licencia Médica","Pre y post natal","Accidente","Otro"])
        estado = st.selectbox("Estado", ["Aprobada","Pendiente","Rechazada"])
        c1,c2 = st.columns(2)
        f1 = c1.date_input("Fecha inicio", value=date.today())
        f2 = c2.date_input("Fecha término", value=date.today())
        dias = c2.number_input("Días", min_value=1, value=max(1,(f2-f1).days+1))
        guardar = st.form_submit_button("💾 Registrar licencia", use_container_width=True)

    if guardar:
        if f2 < f1:
            st.error("La fecha de término no puede ser anterior al inicio.")
        elif not rut or not nombre:
            st.error("RUT y nombre son obligatorios.")
        else:
            execute("""
                INSERT INTO licencias(rut,nombre,apellido_p,apellido_m,sucursal,cargo,fecha_desde,fecha_hasta,dias,tipo_ausencia,estado)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)
            """, (rut.strip(),nombre.strip(),apellido_p.strip(),apellido_m.strip(),sucursal.strip(),cargo.strip(),
                  f1.isoformat(),f2.isoformat(),int(dias),tipo,estado))
            audit("LICENCIA", f"{rut} {f1} a {f2} {estado}")
            st.cache_data.clear()
            st.success("Licencia registrada correctamente.")

    df = query_df("""
        SELECT id ID,rut RUT,nombre Nombre,apellido_p Apellido_Paterno,apellido_m Apellido_Materno,
               sucursal Sucursal,cargo Cargo,fecha_desde Inicio,fecha_hasta Termino,
               dias Días,tipo_ausencia Tipo,estado Estado
        FROM licencias ORDER BY date(fecha_desde) DESC
    """)
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.download_button("📥 Descargar Excel", excel_bytes(df, "Licencias"), "licencias.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ============================================================
# COBERTURAS
# ============================================================
elif opcion == "🔄 Coberturas y Movimientos":
    page_title("Coberturas y Movimientos", "Asignación de apoyo, reemplazos y jornada neta.")

    colabs = query_df("SELECT rut,nombre_completo,codigo_sucursal,cargo FROM colaboradores WHERE activo=1 ORDER BY nombre_completo")
    sucs = query_df("SELECT codigo,nombre FROM sucursales ORDER BY nombre")

    if colabs.empty or sucs.empty:
        st.warning("Carga primero colaboradores y sucursales.")
    else:
        with st.form("cobertura_form"):
            c1,c2 = st.columns(2)
            rut_apoyo = c1.selectbox(
                "Colaborador de apoyo", colabs["rut"].tolist(),
                format_func=lambda r: colabs.loc[colabs["rut"]==r,"nombre_completo"].iloc[0]
            )
            rut_reemplaza = c2.selectbox(
                "¿A quién cubre?",
                [""] + colabs["rut"].tolist(),
                format_func=lambda r: "Apoyo por alta demanda" if r=="" else colabs.loc[colabs["rut"]==r,"nombre_completo"].iloc[0]
            )
            suc_origen = c1.selectbox("Sucursal origen", sucs["codigo"].tolist(),
                                      format_func=lambda c: sucs.loc[sucs["codigo"]==c,"nombre"].iloc[0])
            suc_dest = c2.selectbox("Sucursal destino", sucs["codigo"].tolist(),
                                    format_func=lambda c: sucs.loc[sucs["codigo"]==c,"nombre"].iloc[0])

            motivo = st.selectbox("Motivo", ["Cobertura Vacaciones QF","Licencia Médica","Permiso Administrativo",
                                             "Refuerzo Apertura","Refuerzo Cierre","Otro"])
            motivo_final = st.text_input("Detalle del motivo") if motivo=="Otro" else motivo

            st.markdown("#### ⏱️ Jornada")
            dias_sem = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
            horas = []
            for i in range(7):
                a,b,c = st.columns([1.2,1.2,1.2])
                activo = a.checkbox(dias_sem[i], key=f"cov_act_{i}")
                ent = b.time_input("Entrada", value=time(9,0), key=f"cov_ent_{i}")
                sal = c.time_input("Salida", value=time(18,0), key=f"cov_sal_{i}")
                if activo:
                    horas.append((dias_sem[i],ent,sal))
            colacion = st.number_input("Colación por día (min)", min_value=0,max_value=180,value=30,step=5)
            f1,f2 = st.columns(2)
            inicio = f1.date_input("Inicio cobertura", value=date.today())
            termino = f2.date_input("Fin cobertura", value=date.today())
            guardar = st.form_submit_button("💾 Guardar cobertura", use_container_width=True)

        if guardar:
            if termino < inicio:
                st.error("El fin no puede ser anterior al inicio.")
            elif not horas:
                st.error("Seleccione al menos un día.")
            else:
                total = sum(net_hours(e,s,colacion) for _,e,s in horas)
                detalle = " | ".join([f"{d[:3]} {e:%H:%M}-{s:%H:%M}" for d,e,s in horas])
                detalle += f" | Jornada semanal configurada: {total:.2f} h | Colación: {colacion} min"
                execute("""
                    INSERT INTO movimientos(fecha_registro,usuario_realiza,rut_colaborador,sucursal_origen,
                    sucursal_destino,rut_reemplazado,fecha_inicio,fecha_fin,nuevo_horario,motivo)
                    VALUES(?,?,?,?,?,?,?,?,?,?)
                """, (datetime.now(), st.session_state.usuario_actual, rut_apoyo, suc_origen, suc_dest,
                      rut_reemplaza or None, inicio.isoformat(), termino.isoformat(), detalle, motivo_final))
                audit("COBERTURA", f"{rut_apoyo} {suc_origen}->{suc_dest} {inicio}->{termino} {total:.2f}h")
                st.cache_data.clear()
                st.success("Cobertura registrada correctamente.")

        df = query_df("""
            SELECT m.id ID,m.fecha_registro Registro,c.nombre_completo Colaborador,
                   so.nombre Origen,sd.nombre Destino,c2.nombre_completo 'Cubrió a',
                   m.fecha_inicio Inicio,m.fecha_fin Término,m.nuevo_horario Jornada,m.motivo Motivo
            FROM movimientos m
            LEFT JOIN colaboradores c ON m.rut_colaborador=c.rut
            LEFT JOIN colaboradores c2 ON m.rut_reemplazado=c2.rut
            LEFT JOIN sucursales so ON m.sucursal_origen=so.codigo
            LEFT JOIN sucursales sd ON m.sucursal_destino=sd.codigo
            ORDER BY m.id DESC
        """)
        st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================
# SUCURSALES
# ============================================================
elif opcion == "🏪 Sucursales":
    page_title("Sucursales", "Dotación, responsables y estado operativo por local.")

    df = query_df("""
        SELECT codigo Código,nombre Sucursal,direccion Dirección,comuna Comuna,region Región,
               director_tecnico 'QF Titular',dt_complementario 'DT Complementario',latitud, longitud
        FROM sucursales ORDER BY nombre
    """)
    if df.empty:
        st.info("No existen sucursales cargadas.")
    else:
        filtro = st.text_input("🔎 Buscar sucursal, comuna o región")
        if filtro:
            mask = df.astype(str).apply(lambda x: x.str.contains(filtro,case=False,na=False)).any(axis=1)
            df = df[mask]
        st.dataframe(df, use_container_width=True, hide_index=True)
        if not df.empty:
            cod = st.selectbox("Ver detalle de sucursal", df["Código"].tolist())
            s = query_df("SELECT * FROM sucursales WHERE codigo=?", (cod,)).iloc[0]
            a,b,c,d = st.columns(4)
            a.metric("Colaboradores", int(query_df("SELECT COUNT(*) n FROM colaboradores WHERE codigo_sucursal=? AND activo=1",(cod,)).iloc[0,0]))
            b.metric("Coberturas", int(query_df("SELECT COUNT(*) n FROM movimientos WHERE sucursal_destino=?",(cod,)).iloc[0,0]))
            c.metric("Licencias asociadas", int(query_df("SELECT COUNT(*) n FROM licencias WHERE sucursal=?",(s["nombre"],)).iloc[0,0]))
            d.metric("Vacaciones", int(query_df("SELECT COUNT(*) n FROM solicitudes WHERE codigo_sucursal=?",(cod,)).iloc[0,0]))
            st.write(f"**Dirección:** {s['direccion']}, {s['comuna']} · {s['region']}")
            st.write(f"**QF Titular:** {s['director_tecnico'] or '-'}")
            st.write(f"**DT Complementario:** {s['dt_complementario'] or '-'}")



# ============================================================
# MAPA
# ============================================================
elif opcion == "🗺️ Mapa de Sucursales":
    page_title("Mapa de Sucursales", "Radar georreferenciado de locales y estado operativo.")

    df = query_df("""
        SELECT codigo,nombre,direccion,comuna,region,director_tecnico,dt_complementario,latitud,longitud
        FROM sucursales
        WHERE latitud IS NOT NULL AND longitud IS NOT NULL
    """)

    if df.empty:
        st.info("No hay sucursales con coordenadas válidas. Puede cargarlas desde Configuración → Carga masiva.")
    else:
        lat_c = float(df["latitud"].mean())
        lon_c = float(df["longitud"].mean())
        mapa = folium.Map(location=[lat_c, lon_c], zoom_start=6, tiles="OpenStreetMap")
        bounds = []

        for _, r in df.iterrows():
            codigo = r["codigo"]
            nombre = r["nombre"]
            lic = int(query_df(
                "SELECT COUNT(*) n FROM licencias WHERE sucursal=? AND estado='Aprobada'",
                (nombre,)
            ).iloc[0,0])
            vac = int(query_df(
                "SELECT COUNT(*) n FROM solicitudes WHERE codigo_sucursal=? AND estado IN ('Aprobada','Pre Aprobada','Pendiente')",
                (codigo,)
            ).iloc[0,0])
            cov = int(query_df(
                "SELECT COUNT(*) n FROM movimientos WHERE sucursal_destino=? AND date(fecha_inicio)<=date('now') AND date(fecha_fin)>=date('now')",
                (codigo,)
            ).iloc[0,0])

            riesgo = lic > 0 and cov == 0
            color = "red" if riesgo else ("orange" if vac > 0 else "blue")
            popup = folium.Popup(
                f"""
                <div style="font-family:Arial;font-size:13px;min-width:230px">
                <b>{nombre} ({codigo})</b><br>
                📍 {r['direccion'] or ''}, {r['comuna'] or ''}<br>
                💊 QF: {r['director_tecnico'] or '-'}<br>
                💊 DT 2: {r['dt_complementario'] or '-'}<br>
                🏥 Licencias: {lic}<br>
                🏖️ Ausencias: {vac}<br>
                🔄 Coberturas activas: {cov}<br>
                {"⚠️ Requiere revisión de cobertura" if riesgo else "✅ Sin alerta crítica detectada"}
                </div>
                """,
                max_width=320,
            )
            folium.Marker(
                [r["latitud"], r["longitud"]],
                popup=popup,
                tooltip=f"{nombre} ({codigo})",
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(mapa)
            bounds.append([r["latitud"], r["longitud"]])

        mapa.fit_bounds(bounds)
        st_folium(mapa, width=1300, height=620)
        st.caption("🔴 licencia sin cobertura activa · 🟠 ausencia programada · 🔵 sin alerta crítica")

# ============================================================
# ALERTAS DE AUSENTISMO
# ============================================================
elif opcion == "🚨 Alertas de Ausentismo":
    page_title("Centro de Alertas de Ausentismo", "Ausencias activas, retornos próximos y solicitudes en proceso.")

    active = current_absences(1000)
    upcoming = upcoming_absences(14, 1000)
    process = requests_in_process(1000)

    a,b,c = st.columns(3)
    a.metric("Ausentismos activos", len(active))
    b.metric("Retornos próximos ≤3 días", int((active["Días restantes"] <= 3).sum()) if not active.empty else 0)
    c.metric("Solicitudes en proceso", len(process))

    st.markdown('<div class="section">🔴 Personas actualmente ausentes</div>', unsafe_allow_html=True)
    if active.empty:
        st.success("No hay ausencias activas hoy.")
    else:
        filtro = st.text_input("🔎 Filtrar persona, RUT, sucursal o tipo")
        view = active.copy()
        if filtro:
            mask=view.astype(str).apply(lambda col: col.str.contains(filtro,case=False,na=False)).any(axis=1)
            view=view[mask]
        st.dataframe(style_alert_rows(view),use_container_width=True,hide_index=True)
        st.download_button("📥 Descargar ausentismo activo",
                           excel_bytes(view,"Activos"),"ausentismo_activo.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown('<div class="section">🟠 Ausentismos próximos</div>', unsafe_allow_html=True)
    st.dataframe(upcoming,use_container_width=True,hide_index=True) if not upcoming.empty else st.info("No hay ausentismos iniciando en los próximos 14 días.")

    st.markdown('<div class="section">🟡 Vacaciones y permisos en proceso</div>', unsafe_allow_html=True)
    if process.empty:
        st.success("No existen solicitudes pendientes/pre-aprobadas.")
    else:
        st.dataframe(process,use_container_width=True,hide_index=True)
        st.info("El archivo Historial_General no contiene fecha de inicio/término de la ausencia; por eso las solicitudes aprobadas históricas no se clasifican automáticamente como vigentes. Las pendientes/pre-aprobadas sí se muestran como 'en proceso'.")
        st.download_button("📥 Descargar solicitudes en proceso",
                           excel_bytes(process,"EnProceso"),"solicitudes_en_proceso.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ============================================================
# INCIDENCIAS / BITÁCORA
# ============================================================
elif opcion == "🚨 Incidencias y Bitácora":
    page_title("Incidencias y Bitácora", "Seguimiento de novedades, responsables y resolución.")

    tab1, tab2 = st.tabs(["🚨 Incidencias", "📝 Bitácora"])

    with tab1:
        with st.form("inc_form"):
            c1,c2 = st.columns(2)
            fecha_evento = c1.date_input("Fecha del evento", value=date.today())
            sucursal = c2.text_input("Sucursal")
            rut = c1.text_input("RUT (opcional)")
            tipo = c2.selectbox("Tipo", ["Asistencia","Cobertura","Licencia","Vacaciones","Turno","Sistema","Otro"])
            prioridad = c1.selectbox("Prioridad", ["Baja","Media","Alta","Crítica"])
            responsable = c2.text_input("Responsable")
            descripcion = st.text_area("Descripción")
            guardar = st.form_submit_button("➕ Registrar incidencia", use_container_width=True)
        if guardar:
            if not descripcion.strip():
                st.error("Debe ingresar una descripción.")
            else:
                execute("""
                    INSERT INTO incidencias(fecha,fecha_evento,sucursal,rut,tipo,descripcion,prioridad,estado,responsable)
                    VALUES(?,?,?,?,?,?,?,?,?)
                """, (datetime.now(), fecha_evento.isoformat(),sucursal.strip(),rut.strip(),tipo,
                      descripcion.strip(),prioridad,"Abierta",responsable.strip()))
                audit("INCIDENCIA", f"{tipo} {prioridad} {sucursal}")
                st.cache_data.clear()
                st.success("Incidencia registrada.")

        df = query_df("""
            SELECT id ID,fecha_evento Evento,sucursal Sucursal,rut RUT,tipo Tipo,
                   descripcion Descripción,prioridad Prioridad,estado Estado,responsable Responsable,
                   fecha_cierre Cierre,resolucion Resolución
            FROM incidencias ORDER BY id DESC
        """)
        st.dataframe(df, use_container_width=True, hide_index=True)

        if not df.empty:
            id_inc = st.selectbox("Incidencia a gestionar", df["ID"].tolist())
            estado_n = st.selectbox("Nuevo estado", ["Abierta","En gestión","Resuelta","Cerrada"])
            resol = st.text_area("Resolución / comentario")
            if st.button("💾 Actualizar incidencia"):
                cierre = datetime.now() if estado_n=="Cerrada" else None
                execute("UPDATE incidencias SET estado=?,resolucion=?,fecha_cierre=? WHERE id=?",
                        (estado_n,resol,cierre,id_inc))
                audit("INCIDENCIA_UPDATE", f"ID {id_inc} -> {estado_n}")
                st.cache_data.clear()
                st.success("Incidencia actualizada.")

    with tab2:
        with st.form("bit_form"):
            suc = st.text_input("Sucursal", key="bit_suc")
            prioridad = st.selectbox("Prioridad", ["Baja","Media","Alta","Crítica"], key="bit_pri")
            novedad = st.text_area("Novedad / nota operativa")
            guardar = st.form_submit_button("📝 Registrar nota", use_container_width=True)
        if guardar:
            if not novedad.strip():
                st.warning("Ingrese una nota.")
            else:
                execute("""
                    INSERT INTO bitacora_diaria(fecha,sucursal,usuario,novedad,prioridad,estado)
                    VALUES(?,?,?,?,?,?)
                """, (datetime.now(),suc,st.session_state.usuario_actual,novedad,prioridad,"Abierta"))
                audit("BITACORA", f"{suc} {prioridad}")
                st.cache_data.clear()
                st.success("Nota registrada.")

        df = query_df("""
            SELECT fecha Fecha,sucursal Sucursal,usuario Usuario,novedad Novedad,prioridad Prioridad,estado Estado
            FROM bitacora_diaria ORDER BY id DESC
        """)
        st.dataframe(df, use_container_width=True, hide_index=True)


# ============================================================
# REPORTES
# ============================================================
elif opcion == "📈 Reportes":
    page_title("Reportería RRHH", "Generación de reportes Excel y CSV.")

    reporte = st.selectbox("Seleccione un reporte", [
        "Dotación",
        "Asistencia",
        "Licencias",
        "Vacaciones y permisos",
        "Coberturas",
        "Incidencias",
        "Auditoría"
    ])

    df = pd.DataFrame()
    if reporte == "Dotación":
        df = query_df("""
            SELECT c.rut RUT,c.nombre_completo Colaborador,c.cargo Cargo,
                   s.nombre Sucursal,s.region Región,c.jornada_horas Jornada,c.activo Activo
            FROM colaboradores c LEFT JOIN sucursales s ON c.codigo_sucursal=s.codigo
            ORDER BY c.nombre_completo
        """)
    elif reporte == "Asistencia":
        df = query_df("""
            SELECT a.fecha Fecha,c.rut RUT,c.nombre_completo Colaborador,s.nombre Sucursal,
                   a.entrada Entrada,a.salida Salida,a.colacion_min Colación,
                   a.estado Estado,a.observacion Observación
            FROM asistencia a LEFT JOIN colaboradores c ON a.rut=c.rut
            LEFT JOIN sucursales s ON a.codigo_sucursal=s.codigo
            ORDER BY date(a.fecha) DESC
        """)
    elif reporte == "Licencias":
        df = query_df("SELECT * FROM licencias ORDER BY date(fecha_desde) DESC")
    elif reporte == "Vacaciones y permisos":
        df = query_df("SELECT * FROM solicitudes ORDER BY date(fecha_desde) DESC")
    elif reporte == "Coberturas":
        df = query_df("SELECT * FROM movimientos ORDER BY id DESC")
    elif reporte == "Incidencias":
        df = query_df("SELECT * FROM incidencias ORDER BY id DESC")
    elif reporte == "Auditoría":
        df = query_df("SELECT * FROM auditoria ORDER BY id DESC")

    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.download_button("📥 Descargar Excel",
                           excel_bytes(df, reporte[:31]),
                           f"{reporte.lower().replace(' ','_')}.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("📥 Descargar CSV",
                           csv_bytes(df),
                           f"{reporte.lower().replace(' ','_')}.csv",
                           "text/csv")


# ============================================================
# USUARIOS
# ============================================================
elif opcion == "👤 Usuarios":
    page_title("Administración de Usuarios", "Altas, bajas, activación y cambio de contraseña.")

    tab1,tab2,tab3 = st.tabs(["➕ Crear","👥 Administrar","🔐 Mi contraseña"])

    with tab1:
        with st.form("usr_create"):
            c1,c2 = st.columns(2)
            nuevo_usuario = c1.text_input("Usuario")
            nuevo_nombre = c2.text_input("Nombre completo")
            nuevo_rol = c1.selectbox("Rol", ROLES)
            nuevo_pass = c2.text_input("Contraseña inicial", type="password")
            guardar = st.form_submit_button("Crear usuario", use_container_width=True)
        if guardar:
            if not nuevo_usuario.strip() or not nuevo_nombre.strip() or len(nuevo_pass) < 8:
                st.error("Complete los campos y use una contraseña de al menos 8 caracteres.")
            else:
                try:
                    execute("INSERT INTO usuarios(usuario,password,nombre_completo,rol,activo) VALUES(?,?,?,?,1)",
                            (nuevo_usuario.strip(),hash_password(nuevo_pass),nuevo_nombre.strip(),nuevo_rol))
                    audit("CREAR_USUARIO", nuevo_usuario.strip())
                    st.success("Usuario creado correctamente.")
                except sqlite3.IntegrityError:
                    st.error("El usuario ya existe.")

    with tab2:
        df = query_df("SELECT usuario Usuario,nombre_completo Nombre,rol Rol,activo Activo FROM usuarios ORDER BY usuario")
        st.dataframe(df,use_container_width=True,hide_index=True)
        if not df.empty:
            u = st.selectbox("Usuario",df["Usuario"].tolist())
            activo_n = st.selectbox("Estado",[1,0],format_func=lambda x:"Activo" if x==1 else "Desactivado")
            rol_n = st.selectbox("Rol",ROLES,index=ROLES.index(df.loc[df["Usuario"]==u,"Rol"].iloc[0]) if df.loc[df["Usuario"]==u,"Rol"].iloc[0] in ROLES else 0)
            if st.button("💾 Guardar cambios"):
                if u=="admin" and activo_n==0:
                    st.error("No se puede desactivar el administrador maestro principal.")
                else:
                    execute("UPDATE usuarios SET activo=?,rol=? WHERE usuario=?",(activo_n,rol_n,u))
                    audit("USUARIO_UPDATE",f"{u} {rol_n} activo={activo_n}")
                    st.success("Cambios guardados.")

    with tab3:
        with st.form("change_pass"):
            actual = st.text_input("Contraseña actual", type="password")
            nueva = st.text_input("Nueva contraseña", type="password")
            confirmar = st.text_input("Confirmar nueva contraseña", type="password")
            guardar = st.form_submit_button("Cambiar contraseña",use_container_width=True)
        if guardar:
            con = db()
            row = con.execute("SELECT password FROM usuarios WHERE usuario=?",(st.session_state.get("usuario_login","admin"),)).fetchone()
            con.close()
            if not row or not verify_password(actual,row[0]):
                st.error("La contraseña actual no es correcta.")
            elif len(nueva)<8:
                st.error("La nueva contraseña debe tener al menos 8 caracteres.")
            elif nueva!=confirmar:
                st.error("Las contraseñas no coinciden.")
            else:
                execute("UPDATE usuarios SET password=? WHERE usuario=?",(hash_password(nueva),st.session_state.get("usuario_login","admin")))
                audit("CAMBIO_PASSWORD","Cambio de contraseña")
                st.success("Contraseña cambiada correctamente.")


# ============================================================
# AUDITORÍA
# ============================================================
elif opcion == "🛡️ Auditoría":
    page_title("Auditoría y Seguridad", "Registro de acciones ejecutadas dentro del portal.")

    df = query_df("""
        SELECT id ID,fecha Fecha,usuario Usuario,accion Acción,detalle Detalle
        FROM auditoria ORDER BY id DESC LIMIT 2000
    """)
    st.dataframe(df,use_container_width=True,hide_index=True)
    if not df.empty:
        st.download_button("📥 Exportar auditoría", excel_bytes(df,"Auditoria"), "auditoria_rrhh.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ============================================================
# CONFIGURACIÓN + CARGA MASIVA
# ============================================================
elif opcion == "⚙️ Configuración":
    page_title("Configuración y Carga de Datos", "Parámetros operativos, importación segura y respaldo.")

    tab1,tab2,tab3 = st.tabs(["⚙️ Parámetros","📥 Carga masiva","💾 Backup"])

    with tab1:
        qf = st.number_input("Jornada semanal QF", min_value=1.0,max_value=60.0,value=float(get_config("jornada_qf","40")),step=1.0)
        af = st.number_input("Jornada semanal AF", min_value=1.0,max_value=60.0,value=float(get_config("jornada_af","42")),step=1.0)
        tol = st.number_input("Tolerancia de atraso (min)",min_value=0,max_value=120,value=int(get_config("tolerancia_atraso_min","10")),step=1)
        hora = st.text_input("Hora inicio operativa", value=get_config("hora_inicio_operativa","08:00"))
        if st.button("💾 Guardar parámetros"):
            set_config("jornada_qf",qf); set_config("jornada_af",af)
            set_config("tolerancia_atraso_min",tol); set_config("hora_inicio_operativa",hora)
            audit("CONFIG", "Parámetros actualizados")
            st.success("Configuración guardada.")

        st.info("Los parámetros quedan guardados en la base local de la aplicación.")

    with tab2:
        st.markdown('<div class="section">📦 Paquete oficial de actualización</div>', unsafe_allow_html=True)
        st.caption("Use los cuatro archivos oficiales de operación. La sucursal del colaborador se toma exclusivamente desde la columna BM 'Sucursal' de la nómina y se cruza con 'NOMBRE SUCURSAL' del Directorio.")

        f_dir = st.file_uploader("1. Directorio de sucursales", type=["xlsx"], key="official_dir")
        f_emp = st.file_uploader("2. Lista de empleados", type=["xlsx"], key="official_emp")
        f_aus = st.file_uploader("3. Historial de ausentismo", type=["xlsx"], key="official_aus")
        f_hist = st.file_uploader("4. Historial general de vacaciones/permisos", type=["xlsx"], key="official_hist")

        if st.button("🚀 Cargar paquete oficial", type="primary", use_container_width=True):
            faltan=[name for name,file in [
                ("Directorio",f_dir),("Empleados",f_emp),("Ausentismo",f_aus),("Historial general",f_hist)
            ] if file is None]
            if faltan:
                st.error("Faltan: " + ", ".join(faltan))
            else:
                try:
                    # Directorio
                    d=pd.read_excel(f_dir); d.columns=[str(x).strip() for x in d.columns]
                    required_dir=["UNIDAD","NOMBRE SUCURSAL","DIRECCIÓN","COMUNA","REGIÓN"]
                    if not all(x in d.columns for x in required_dir):
                        st.error("El Directorio no tiene la estructura esperada.")
                        st.stop()
                    dm={normalize_text(r["NOMBRE SUCURSAL"]):str(r["UNIDAD"]).strip() for _,r in d.iterrows() if str(r["NOMBRE SUCURSAL"]).strip()}
                    conx=db(); curx=conx.cursor()
                    for _,r in d.iterrows():
                        geo=str(r.get("GEOLOCALIZACION","") or "")
                        lat=lon=None
                        if "," in geo:
                            try: lat,lon=[float(v.strip()) for v in geo.split(",",1)]
                            except: pass
                        curx.execute("""INSERT INTO sucursales
                        (codigo,nombre,direccion,comuna,ciudad,region,telefono,director_tecnico,telfdt,dt_complementario,telfdt2,
                         horario_lunes_viernes,horario_sabado,horario_domingo,fecha_apertura,supervisor,jefe_comercial,email,geolocalizacion,ecommerce,latitud,longitud)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(codigo) DO UPDATE SET nombre=excluded.nombre,direccion=excluded.direccion,
                        comuna=excluded.comuna,ciudad=excluded.ciudad,region=excluded.region,
                        director_tecnico=excluded.director_tecnico,dt_complementario=excluded.dt_complementario,
                        supervisor=excluded.supervisor,email=excluded.email,geolocalizacion=excluded.geolocalizacion,
                        ecommerce=excluded.ecommerce,latitud=excluded.latitud,longitud=excluded.longitud""",(
                            str(r["UNIDAD"]).strip(),str(r["NOMBRE SUCURSAL"]).strip(),str(r.get("DIRECCIÓN","") or ""),
                            str(r.get("COMUNA","") or ""),str(r.get("CIUDAD","") or ""),str(r.get("REGIÓN","") or ""),
                            str(r.get("TEL. FIJO","") or ""),str(r.get("DIRECTOR TÉCNICO","") or ""),str(r.get("TELFDT","") or ""),
                            str(r.get("DT COMPLEMENTARIO","") or ""),str(r.get("TELFDT2","") or ""),
                            str(r.get("LUNES A VIERNES","") or ""),str(r.get("SABADO","") or ""),str(r.get("DOMINGO","") or ""),
                            str(r.get("FECHA APERTURA","") or ""),str(r.get("SUPERVISOR","") or ""),str(r.get("JEFE COMERCIAL","") or ""),
                            str(r.get("CORREO ELECTRONICO","") or ""),geo,str(r.get("E-COMMERCE","") or ""),lat,lon
                        ))

                    # Empleados: BM = col 65, header 'Sucursal'
                    e=pd.read_excel(f_emp); e.columns=[str(x).strip() for x in e.columns]
                    if "Sucursal" not in e.columns or "RUT" not in e.columns:
                        st.error("La nómina no contiene la columna BM 'Sucursal' y RUT.")
                        conx.rollback(); conx.close(); st.stop()
                    for _,r in e.iterrows():
                        rut=str(r.get("RUT","") or "").strip()
                        if not rut: continue
                        full=" ".join(str(r.get(k,"") or "").strip() for k in ["Nombre","Apellido Paterno","Apellido Materno"]).strip()
                        suc_bm=str(r.get("Sucursal","") or "").strip()
                        code=dm.get(normalize_text(suc_bm))
                        try:jornada=float(r.get("Horas de la Jornada",40))
                        except:jornada=40.0
                        raw={k:(None if pd.isna(v) else v) for k,v in r.to_dict().items()}
                        for k,v in list(raw.items()):
                            if isinstance(v,(pd.Timestamp,datetime,date)): raw[k]=v.isoformat()
                        curx.execute("""INSERT INTO colaboradores(rut,nombre_completo,codigo_sucursal,sucursal_nombre,cargo,celular,email,jornada_horas,activo,vigencia,sucursal_bm,datos_json)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                        ON CONFLICT(rut) DO UPDATE SET nombre_completo=excluded.nombre_completo,codigo_sucursal=excluded.codigo_sucursal,
                        sucursal_nombre=excluded.sucursal_nombre,cargo=excluded.cargo,celular=excluded.celular,email=excluded.email,
                        jornada_horas=excluded.jornada_horas,activo=excluded.activo,vigencia=excluded.vigencia,
                        sucursal_bm=excluded.sucursal_bm,datos_json=excluded.datos_json""",(
                            rut,full,code,suc_bm,str(r.get("Cargo","") or ""),str(r.get("Celular","") or ""),
                            str(r.get("Email Personal","") or r.get("Email","") or ""),jornada,
                            1 if normalize_text(r.get("Vigente",""))=="SI" else 0,str(r.get("Vigente","") or ""),suc_bm,json.dumps(raw,ensure_ascii=False)
                        ))

                    # Ausentismo completo
                    a=pd.read_excel(f_aus); a.columns=[str(x).strip() for x in a.columns]
                    req_a=["Rut","Nombre","Sucursal","Tipo de Ausencia","Número de días de Ausencia","Fecha Inicio Ausencia","Fecha Fin Ausencia"]
                    if not all(x in a.columns for x in req_a):
                        st.error("El archivo de ausentismo no contiene la estructura esperada.")
                        conx.rollback(); conx.close(); st.stop()
                    curx.execute("DELETE FROM ausentismo_historico")
                    for _,r in a.iterrows():
                        sd=pd.to_datetime(r.get("Fecha Inicio Ausencia"),errors="coerce")
                        ed=pd.to_datetime(r.get("Fecha Fin Ausencia"),errors="coerce")
                        curx.execute("""INSERT INTO ausentismo_historico
                        (rut,nombre,empresa,cargo,gerencia,sucursal,centro_costo,tipo_ausencia,motivo_ausencia,dias,fecha_inicio,fecha_fin,hora_inicio,hora_fin,horas,minutos,fecha_creacion,observaciones,activo,dias_restantes)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
                            str(r.get("Rut","") or ""),str(r.get("Nombre","") or ""),str(r.get("Empresa","") or ""),
                            str(r.get("Cargo","") or ""),str(r.get("Gerencia","") or ""),str(r.get("Sucursal","") or ""),
                            str(r.get("Centro de Costo","") or ""),str(r.get("Tipo de Ausencia","") or ""),
                            str(r.get("Motivo de Ausencia","") or ""),int(pd.to_numeric(r.get("Número de días de Ausencia",0),errors="coerce") or 0),
                            "" if pd.isna(sd) else sd.strftime("%Y-%m-%d"),"" if pd.isna(ed) else ed.strftime("%Y-%m-%d"),
                            str(r.get("Hora Inicio","") or ""),str(r.get("Hora Fin","") or ""),str(r.get("Número Horas","") or ""),
                            str(r.get("Número Minutos","") or ""),excel_serial_to_iso(r.get("Fecha de Creación")),
                            str(r.get("Observaciones","") or ""),
                            int(bool(not pd.isna(sd) and not pd.isna(ed) and sd.date() <= date.today() <= ed.date())),
                            int((ed.date()-date.today()).days) if not pd.isna(ed) else None
                        ))

                    # General history
                    h=pd.read_excel(f_hist,header=None)
                    # Locate the row containing ID/Fecha de Solicitud
                    header_idx=None
                    for i in range(min(10,len(h))):
                        vals=[str(x).strip() for x in h.iloc[i].tolist()]
                        if "ID" in vals and "RUT" in vals and "Tipo" in vals:
                            header_idx=i; break
                    if header_idx is None:
                        st.error("No se encontró la cabecera del Historial_General.")
                        conx.rollback(); conx.close(); st.stop()
                    h.columns=h.iloc[header_idx].astype(str).str.strip(); h=h.iloc[header_idx+1:].reset_index(drop=True)
                    curx.execute("DELETE FROM solicitudes_historial")
                    curx.execute("DELETE FROM solicitudes")
                    for idx,r in h.iterrows():
                        source_id=str(r.get("ID",idx+1) or idx+1)
                        status=str(r.get("Estado","") or "").strip()
                        inproc=1 if status in ("Pendiente","Pre-Aprobada") else 0
                        rut=str(r.get("RUT","") or "").strip()
                        rr=curx.execute("SELECT nombre_completo FROM colaboradores WHERE rut=?",(rut,)).fetchone()
                        cname=rr[0] if rr else str(r.get("Nombre","") or "")
                        try: days=int(float(r.get("Días",0)))
                        except: days=0
                        curx.execute("""INSERT INTO solicitudes_historial(source_id,fecha_solicitud,estado,rut,nombre_fuente,nombre_colaborador,cargo,codigo_sucursal,dias,tipo,detalle,en_proceso)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",(
                            source_id,str(r.get("Fecha de Solicitud","") or ""),status,rut,str(r.get("Nombre","") or ""),
                            cname,str(r.get("Cargo","") or ""),str(r.get("Sucursal","") or ""),days,str(r.get("Tipo","") or ""),
                            str(r.get("Detalle","") or ""),inproc))
                        curx.execute("""INSERT OR REPLACE INTO solicitudes
                        (id_solicitud,estado,rut,nombre,cargo,codigo_sucursal,fecha_solicitud,fecha_desde,fecha_hasta,dias,tipo,detalle,en_proceso)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
                            f"{source_id}#{idx}",status,rut,cname,str(r.get("Cargo","") or ""),str(r.get("Sucursal","") or ""),
                            str(r.get("Fecha de Solicitud","") or ""), "", "", days, str(r.get("Tipo","") or ""),
                            str(r.get("Detalle","") or ""),inproc))
                    conx.commit(); conx.close()
                    audit("CARGA_OFICIAL", "Directorios + empleados BM + ausentismo + historial general")
                    st.cache_data.clear()
                    # Resumen visible de lo cargado.
                    n_dir = len(d)
                    n_emp = len(e)
                    n_aus = len(a)
                    n_hist = len(h)
                    st.success("✅ Paquete oficial cargado correctamente.")
                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Sucursales", n_dir)
                    r2.metric("Empleados", n_emp)
                    r3.metric("Ausentismo histórico", n_aus)
                    r4.metric("Vacaciones/Permisos", n_hist)
                    st.info("🔴 Los ausentismos activos se determinan por fecha. 🟠 Las solicitudes pendientes/pre-aprobadas quedan identificadas para seguimiento.")
                except Exception as exc:
                    try: conx.rollback(); conx.close()
                    except Exception: pass
                    st.error(f"No se pudo completar la carga: {exc}")

        st.markdown("---")
        st.write("### Plantillas")
        p_suc = pd.DataFrame(columns=["codigo","nombre","direccion","comuna","region","director_tecnico","dt_complementario","latitud","longitud"])
        p_col = pd.DataFrame(columns=["rut","nombre_completo","codigo_sucursal","cargo","celular","email","jornada_horas","activo"])
        p_lic = pd.DataFrame(columns=["rut","nombre","apellido_p","apellido_m","sucursal","cargo","fecha_desde","fecha_hasta","dias","tipo_ausencia","estado"])
        p_sol = pd.DataFrame(columns=["id_solicitud","estado","rut","nombre","cargo","codigo_sucursal","fecha_desde","fecha_hasta","dias","tipo"])
        p_ass = pd.DataFrame(columns=["fecha","rut","codigo_sucursal","entrada","salida","colacion_min","estado","observacion"])

        cs = st.columns(3)
        cs[0].download_button("Plantilla sucursales",excel_bytes(p_suc,"Sucursales"),"plantilla_sucursales.xlsx")
        cs[1].download_button("Plantilla colaboradores",excel_bytes(p_col,"Colaboradores"),"plantilla_colaboradores.xlsx")
        cs[2].download_button("Plantilla licencias",excel_bytes(p_lic,"Licencias"),"plantilla_licencias.xlsx")
        cs = st.columns(2)
        cs[0].download_button("Plantilla vacaciones/permisos",excel_bytes(p_sol,"Solicitudes"),"plantilla_solicitudes.xlsx")
        cs[1].download_button("Plantilla asistencia",excel_bytes(p_ass,"Asistencia"),"plantilla_asistencia.xlsx")

        tipo_carga = st.selectbox("Tipo de archivo a cargar",["Sucursales","Colaboradores","Licencias","Solicitudes","Asistencia"])
        archivo = st.file_uploader("Seleccione Excel",type=["xlsx"])
        if archivo:
            df_in = normalize_columns(pd.read_excel(archivo))
            st.write("### Previsualización")
            st.dataframe(df_in.head(20),use_container_width=True,hide_index=True)
            st.caption(f"Filas detectadas: {len(df_in)}")
            confirmar = st.button("🚀 Validar e importar")
            if confirmar:
                errores = []
                con = db()
                cur = con.cursor()

                try:
                    if tipo_carga == "Sucursales":
                        for i,r in df_in.iterrows():
                            codigo = str(get_col(df_in,["codigo","unidad","cc"],"").iloc[i]).strip()
                            nombre = str(get_col(df_in,["nombre","sucursal"],"").iloc[i]).strip()
                            if not codigo or not nombre:
                                errores.append(f"Fila {i+2}: código/nombre obligatorio")
                                continue
                            cur.execute("""
                                INSERT INTO sucursales(codigo,nombre,direccion,comuna,region,director_tecnico,dt_complementario,latitud,longitud)
                                VALUES(?,?,?,?,?,?,?,?,?)
                                ON CONFLICT(codigo) DO UPDATE SET
                                nombre=excluded.nombre,direccion=excluded.direccion,comuna=excluded.comuna,region=excluded.region,
                                director_tecnico=excluded.director_tecnico,dt_complementario=excluded.dt_complementario,
                                latitud=excluded.latitud,longitud=excluded.longitud
                            """, (
                                codigo,nombre,
                                str(get_col(df_in,["direccion","dirección"],"").iloc[i]),
                                str(get_col(df_in,["comuna"],"").iloc[i]),
                                str(get_col(df_in,["region","región"],"").iloc[i]),
                                str(get_col(df_in,["director_tecnico","director técnico","qf titular"],"").iloc[i]),
                                str(get_col(df_in,["dt_complementario","dt complementario"],"").iloc[i]),
                                safe_num(get_col(df_in,["latitud"],None).iloc[i],None),
                                safe_num(get_col(df_in,["longitud"],None).iloc[i],None),
                            ))

                    elif tipo_carga == "Colaboradores":
                        for i,r in df_in.iterrows():
                            rut = str(get_col(df_in,["rut"],"").iloc[i]).strip()
                            nombre = str(get_col(df_in,["nombre_completo","nombre"],"").iloc[i]).strip()
                            if not rut or not nombre:
                                errores.append(f"Fila {i+2}: RUT/nombre obligatorio")
                                continue
                            cur.execute("""
                                INSERT INTO colaboradores(rut,nombre_completo,codigo_sucursal,cargo,celular,email,jornada_horas,activo)
                                VALUES(?,?,?,?,?,?,?,?)
                                ON CONFLICT(rut) DO UPDATE SET
                                nombre_completo=excluded.nombre_completo,codigo_sucursal=excluded.codigo_sucursal,
                                cargo=excluded.cargo,celular=excluded.celular,email=excluded.email,
                                jornada_horas=excluded.jornada_horas,activo=excluded.activo
                            """, (
                                rut,nombre,str(get_col(df_in,["codigo_sucursal","sucursal"],"").iloc[i]),
                                str(get_col(df_in,["cargo"],"").iloc[i]),
                                str(get_col(df_in,["celular","telefono"],"").iloc[i]),
                                str(get_col(df_in,["email"],"").iloc[i]),
                                safe_num(get_col(df_in,["jornada_horas","jornada"],40).iloc[i],40),
                                int(safe_num(get_col(df_in,["activo"],1).iloc[i],1) != 0)
                            ))

                    elif tipo_carga == "Licencias":
                        for i,r in df_in.iterrows():
                            rut = str(get_col(df_in,["rut"],"").iloc[i]).strip()
                            nombre = str(get_col(df_in,["nombre"],"").iloc[i]).strip()
                            f1 = pd.to_datetime(get_col(df_in,["fecha_desde","inicio"],"").iloc[i],errors="coerce")
                            f2 = pd.to_datetime(get_col(df_in,["fecha_hasta","termino","término"],"").iloc[i],errors="coerce")
                            if not rut or not nombre or pd.isna(f1) or pd.isna(f2):
                                errores.append(f"Fila {i+2}: RUT, nombre y fechas son obligatorios")
                                continue
                            cur.execute("""
                                INSERT INTO licencias(rut,nombre,apellido_p,apellido_m,sucursal,cargo,fecha_desde,fecha_hasta,dias,tipo_ausencia,estado)
                                VALUES(?,?,?,?,?,?,?,?,?,?,?)
                            """, (
                                rut,nombre,
                                str(get_col(df_in,["apellido_p","apellido paterno"],"").iloc[i]),
                                str(get_col(df_in,["apellido_m","apellido materno"],"").iloc[i]),
                                str(get_col(df_in,["sucursal"],"").iloc[i]),
                                str(get_col(df_in,["cargo"],"").iloc[i]),
                                f1.strftime("%Y-%m-%d"),f2.strftime("%Y-%m-%d"),
                                int(safe_num(get_col(df_in,["dias","días"],max(1,(f2-f1).days+1)).iloc[i],max(1,(f2-f1).days+1))),
                                str(get_col(df_in,["tipo_ausencia","tipo"],"Licencia Médica").iloc[i]),
                                str(get_col(df_in,["estado"],"Aprobada").iloc[i])
                            ))

                    elif tipo_carga == "Solicitudes":
                        for i,r in df_in.iterrows():
                            rut = str(get_col(df_in,["rut"],"").iloc[i]).strip()
                            ident = str(get_col(df_in,["id_solicitud","id","folio"],f"{rut}-{i}").iloc[i]).strip()
                            f1 = pd.to_datetime(get_col(df_in,["fecha_desde","inicio"],"").iloc[i],errors="coerce")
                            f2 = pd.to_datetime(get_col(df_in,["fecha_hasta","termino","término"],"").iloc[i],errors="coerce")
                            if not rut or pd.isna(f1) or pd.isna(f2):
                                errores.append(f"Fila {i+2}: RUT y fechas obligatorios")
                                continue
                            cur.execute("""
                                INSERT INTO solicitudes(id_solicitud,estado,rut,nombre,cargo,codigo_sucursal,fecha_desde,fecha_hasta,dias,tipo)
                                VALUES(?,?,?,?,?,?,?,?,?,?)
                                ON CONFLICT(id_solicitud) DO UPDATE SET
                                estado=excluded.estado,fecha_hasta=excluded.fecha_hasta,dias=excluded.dias,tipo=excluded.tipo
                            """, (
                                ident,
                                str(get_col(df_in,["estado"],"Aprobada").iloc[i]),
                                rut,
                                str(get_col(df_in,["nombre"],"").iloc[i]),
                                str(get_col(df_in,["cargo"],"").iloc[i]),
                                str(get_col(df_in,["codigo_sucursal","sucursal"],"").iloc[i]),
                                f1.strftime("%Y-%m-%d"),f2.strftime("%Y-%m-%d"),
                                int(safe_num(get_col(df_in,["dias","días"],max(1,(f2-f1).days+1)).iloc[i],1)),
                                str(get_col(df_in,["tipo"],"Vacaciones").iloc[i])
                            ))

                    elif tipo_carga == "Asistencia":
                        for i,r in df_in.iterrows():
                            fecha = pd.to_datetime(get_col(df_in,["fecha"],"").iloc[i],errors="coerce")
                            rut = str(get_col(df_in,["rut"],"").iloc[i]).strip()
                            if pd.isna(fecha) or not rut:
                                errores.append(f"Fila {i+2}: fecha/RUT obligatorios")
                                continue
                            cur.execute("""
                                INSERT INTO asistencia(fecha,rut,codigo_sucursal,entrada,salida,colacion_min,estado,observacion)
                                VALUES(?,?,?,?,?,?,?,?)
                                ON CONFLICT(fecha,rut) DO UPDATE SET
                                codigo_sucursal=excluded.codigo_sucursal,entrada=excluded.entrada,salida=excluded.salida,
                                colacion_min=excluded.colacion_min,estado=excluded.estado,observacion=excluded.observacion
                            """, (
                                fecha.strftime("%Y-%m-%d"),rut,
                                str(get_col(df_in,["codigo_sucursal","sucursal"],"").iloc[i]),
                                str(get_col(df_in,["entrada"],"").iloc[i]),
                                str(get_col(df_in,["salida"],"").iloc[i]),
                                int(safe_num(get_col(df_in,["colacion_min","colacion"],30).iloc[i],30)),
                                str(get_col(df_in,["estado"],"Completa").iloc[i]),
                                str(get_col(df_in,["observacion","observación"],"").iloc[i])
                            ))

                    con.commit()
                    audit("CARGA_MASIVA", f"{tipo_carga}: {len(df_in)} filas; errores={len(errores)}")
                    st.cache_data.clear()
                    st.success(f"Importación finalizada. Filas procesadas: {len(df_in)}")
                    if errores:
                        st.warning(f"Se detectaron {len(errores)} observaciones.")
                        st.dataframe(pd.DataFrame({"Observación": errores}),use_container_width=True)
                except Exception as e:
                    con.rollback()
                    st.error(f"No se pudo completar la importación: {e}")
                finally:
                    con.close()

    with tab3:
        st.write("### Respaldo de la base de datos")
        st.caption("Descargue una copia antes de cargas masivas o cambios importantes.")
        if st.button("💾 Generar backup"):
            path = download_backup()
            audit("BACKUP", str(path.name))
            st.success("Backup generado.")
            st.download_button("📥 Descargar backup",path.read_bytes(),path.name,"application/octet-stream")


# ============================================================
# AYUDA
# ============================================================
elif opcion == "ℹ️ Ayuda":
    page_title("Ayuda del Portal", "Guía rápida para la operación diaria.")
    st.markdown("""
    ### Uso recomendado

    **Inicio / Dashboard**: revise dotación, licencias, coberturas e incidencias.

    **Personas**: busque un colaborador y revise su historial.

    **Asistencia**: registre entradas, salidas, colación y estado.

    **Vacaciones y Permisos**: registre o consulte ausencias programadas.

    **Licencias**: mantenga actualizado el período y estado de las licencias.

    **Coberturas**: registre apoyos, reemplazos y jornadas.

    **Incidencias**: deje trazabilidad de problemas y su resolución.

    **Reportes**: descargue la información en Excel o CSV.

    **Administración**: usuarios, auditoría, parámetros y respaldo.
    """)

st.caption("Portal Corporativo RRHH · Dr. Simi · Versión integral")
