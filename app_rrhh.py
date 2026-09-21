
import streamlit as st
import pandas as pd
import sqlite3
import io
import hashlib
import secrets
import json
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
    :root {
        --navy:#08233f;
        --navy-2:#0b3158;
        --navy-3:#123f68;
        --blue:#1d4ed8;
        --blue-soft:#eaf2ff;
        --text:#102a43;
        --muted:#64748b;
        --border:#d7e0ea;
        --bg:#f5f7fa;
        --white:#ffffff;
        --danger:#b91c1c;
        --warning:#a16207;
        --success:#166534;
    }

    #MainMenu, footer, header {visibility:hidden;}
    .stApp {background:var(--bg) !important;color:var(--text) !important;}
    .block-container {padding-top:2rem;padding-bottom:3rem;max-width:1500px;}

    /* Sidebar */
    [data-testid="stSidebar"] {
        background:linear-gradient(180deg,var(--navy) 0%,var(--navy-2) 100%) !important;
        border-right:1px solid rgba(255,255,255,.08);
    }
    [data-testid="stSidebar"] * {color:#ffffff !important;}
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {color:#ffffff !important;}
    [data-testid="stSidebar"] .stRadio label {color:#ffffff !important;font-weight:600 !important;}
    [data-testid="stSidebar"] .stRadio > div {gap:4px;}
    [data-testid="stSidebar"] .stButton > button {
        background:#ffffff !important;
        color:var(--navy) !important;
        border:1px solid #dbe3ec !important;
        font-weight:800 !important;
        box-shadow:none !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background:#edf4ff !important;
        color:var(--navy) !important;
        border-color:#b9cae0 !important;
    }

    .brand {
        padding:10px 4px 18px 4px;text-align:center;
        border-bottom:1px solid rgba(255,255,255,.16);margin-bottom:15px;
    }
    .brand-title {font-size:25px;font-weight:900;letter-spacing:1px;color:#fff;}
    .brand-sub {font-size:11px;opacity:.82;letter-spacing:1px;text-transform:uppercase;color:#dbeafe;}

    /* Main text */
    .title {font-size:31px;font-weight:850;color:var(--navy) !important;margin-bottom:3px;}
    .subtitle {color:var(--muted) !important;margin-bottom:22px;}
    h1,h2,h3,h4,h5,h6 {color:var(--navy) !important;}

    /* Cards */
    .card {
        background:var(--white);border:1px solid var(--border);border-radius:16px;
        padding:20px;box-shadow:0 5px 20px rgba(15,23,42,.06);height:100%;
    }
    .metric-label {font-size:13px;color:#526579 !important;}
    .metric-value {font-size:30px;font-weight:850;color:var(--navy) !important;}
    .metric-note {font-size:11px;color:#7c8da1 !important;}
    .section {
        background:var(--navy);color:#fff !important;border-radius:12px;padding:13px 16px;
        font-weight:750;margin:18px 0 12px 0;
    }
    .section * {color:#fff !important;}

    /* All Streamlit controls: dark text on light surfaces */
    label, [data-testid="stWidgetLabel"] *, [data-testid="stMarkdownContainer"] p {
        color:var(--text);
    }
    input, textarea {
        color:var(--text) !important;
        background:#ffffff !important;
        border:1px solid #cbd5e1 !important;
    }
    input::placeholder, textarea::placeholder {color:#8190a3 !important;opacity:1 !important;}

    div[data-baseweb="select"] > div {
        background:#ffffff !important;color:var(--text) !important;
        border-color:#cbd5e1 !important;
    }
    div[data-baseweb="select"] span, div[data-baseweb="select"] input {
        color:var(--text) !important;
    }
    div[data-baseweb="popover"],
    div[role="listbox"],
    ul[role="listbox"] {
        background:#ffffff !important;
        color:var(--text) !important;
    }
    div[role="option"] {
        color:var(--text) !important;
        background:#ffffff !important;
    }
    div[role="option"]:hover {
        background:#edf4ff !important;
        color:var(--navy) !important;
    }

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button,
    button[kind="primary"] {
        background:var(--navy) !important;
        color:#ffffff !important;
        border:1px solid var(--navy) !important;
        border-radius:9px !important;
        font-weight:800 !important;
        min-height:42px !important;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover,
    button[kind="primary"]:hover {
        background:var(--navy-3) !important;
        color:#ffffff !important;
        border-color:var(--navy-3) !important;
    }
    .stFormSubmitButton > button {
        background:var(--blue) !important;color:#fff !important;border-color:var(--blue) !important;
    }
    .stFormSubmitButton > button:hover {
        background:#1e40af !important;color:#fff !important;
    }

    /* Forms */
    div[data-testid="stForm"] {
        background:#ffffff !important;
        border:1px solid var(--border) !important;
        border-radius:14px !important;
        padding:20px !important;
    }
    div[data-testid="stForm"] label,
    div[data-testid="stForm"] p {color:var(--text) !important;}

    /* Dataframes */
    [data-testid="stDataFrame"] {
        border:1px solid var(--border) !important;
        border-radius:10px !important;
        overflow:hidden !important;
        background:#ffffff !important;
    }

    /* Alerts / info panels */
    div[data-testid="stAlert"] * {color:inherit !important;}

    .status-ok {color:var(--success) !important;font-weight:700;}
    .status-warn {color:var(--warning) !important;font-weight:700;}
    .status-bad {color:var(--danger) !important;font-weight:700;}

    /* Login */
    .login-shell {
        min-height:100vh;
        margin:-2rem -1rem -3rem -1rem;
        padding:5vh 20px 70px 20px;
        display:flex;
        justify-content:center;
        align-items:flex-start;
        background:radial-gradient(circle at 80% 10%,#1f4774 0,#0b1d32 38%,#020617 100%);
    }
    .login-card {
        width:min(500px,100%);
        margin-top:4vh;
        padding:34px;
        background:#ffffff !important;
        border-radius:22px;
        box-shadow:0 28px 80px rgba(0,0,0,.35);
        border:1px solid #dbe3ec;
    }
    .login-card .login-brand {
        text-align:center;margin-bottom:25px;
    }
    .login-card .login-brand-name {
        font-size:38px;font-weight:950;color:var(--navy);
        letter-spacing:2px;
    }
    .login-card .login-brand-sub {
        color:#66788d;font-size:12px;letter-spacing:1.8px;text-transform:uppercase;
        margin-top:7px;
    }
    .login-card h3, .login-card h2 {color:var(--navy) !important;}
    .login-card .stTextInput label {color:var(--text) !important;}
    .login-card .stTextInput input {
        background:#f8fafc !important;color:var(--text) !important;
        border:1px solid #cbd5e1 !important;border-radius:9px !important;
    }
    .small-muted {font-size:11px;color:#64748b !important;}
    </style>
    """,
    unsafe_allow_html=True,
)


# -------------------------
# Database
# -------------------------
def db():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


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
    bloqueo = st.session_state.bloqueo_hasta
    st.markdown('<div class="login-shell"><div class="login-card">', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="login-brand">
            <div class="login-brand-name">DR. SIMI</div>
            <div style="height:3px;width:58px;background:#1d4ed8;margin:10px auto 12px auto;"></div>
            <div class="login-brand-sub">Portal Corporativo de Gestión RRHH</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if bloqueo and datetime.now() < bloqueo:
        st.error("Acceso temporalmente bloqueado por múltiples intentos fallidos.")
        st.markdown("</div></div>", unsafe_allow_html=True)
        st.stop()

    st.markdown("### 🔐 Identificación segura")
    st.caption("Ingrese sus credenciales corporativas para acceder al portal.")

    with st.form("login_form", clear_on_submit=False):
        usuario = st.text_input("Usuario", placeholder="Ingrese su usuario", autocomplete="username")
        password = st.text_input("Contraseña", type="password", placeholder="Ingrese su contraseña", autocomplete="current-password")
        ingresar = st.form_submit_button("INGRESAR AL PORTAL", use_container_width=True)

    st.markdown(
        '<div class="small-muted" style="text-align:center;margin-top:16px;">Acceso interno · Recursos Humanos · Dr. Simi</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div></div>", unsafe_allow_html=True)

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
    menu.append("🚨 Incidencias y Bitácora")
if can("reportes"):
    menu.append("📈 Reportes")
if st.session_state.rol_actual == "Admin Supremo":
    menu += ["👤 Usuarios", "🛡️ Auditoría", "⚙️ Configuración"]

menu.append("ℹ️ Ayuda")
opcion = st.sidebar.radio("Navegación", menu)

st.sidebar.markdown("---")
st.sidebar.caption(f"Sesión: {datetime.now():%d-%m-%Y %H:%M}")

if st.sidebar.button("🚪  Cerrar sesión", use_container_width=True):
    audit("LOGOUT", "Cierre de sesión")
    for key in ["autenticado", "usuario_actual", "rol_actual", "usuario_login"]:
        st.session_state.pop(key, None)
    st.session_state.autenticado = False
    st.rerun()


def page_title(title, subtitle=""):
    st.markdown(f'<div class="title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="subtitle">{subtitle}</div>', unsafe_allow_html=True)


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
    tot_lic = int(query_df("SELECT COUNT(*) n FROM licencias WHERE estado='Aprobada' AND date(fecha_desde)<=date('now') AND date(fecha_hasta)>=date('now')").iloc[0, 0])
    tot_cov = int(query_df("SELECT COUNT(*) n FROM movimientos WHERE date(fecha_inicio)<=date('now') AND date(fecha_fin)>=date('now')").iloc[0, 0])
    tot_inc = int(query_df("SELECT COUNT(*) n FROM incidencias WHERE estado<>'Cerrada'").iloc[0, 0])
    tot_vac = int(query_df("SELECT COUNT(*) n FROM solicitudes WHERE estado IN ('Aprobada','Pre Aprobada','Pendiente') AND date(fecha_desde)<=date('now') AND date(fecha_hasta)>=date('now')").iloc[0, 0])

    metrics = [
        ("🏪 Sucursales", tot_suc),
        ("👥 Colaboradores activos", tot_col),
        ("🏥 Licencias activas", tot_lic),
        ("🔄 Coberturas activas", tot_cov),
        ("🏖️ Ausencias vigentes", tot_vac),
        ("🚨 Incidencias abiertas", tot_inc),
    ]

    cols = st.columns(6)
    for col, (label, val) in zip(cols, metrics):
        with col:
            st.markdown(
                f'<div class="card"><div class="metric-label">{label}</div>'
                f'<div class="metric-value">{val}</div><div class="metric-note">Actualizado al ingresar</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section">🚨 Alertas críticas</div>', unsafe_allow_html=True)

    alertas = []
    qf = query_df("SELECT codigo,nombre,director_tecnico,dt_complementario FROM sucursales")
    if not qf.empty:
        for _, r in qf.iterrows():
            q1 = str(r["director_tecnico"] or "").strip()
            q2 = str(r["dt_complementario"] or "").strip()
            if q1 in ("", "Sin QF Titular", "nan") and q2 in ("", "Sin DT 2", "nan"):
                alertas.append({
                    "Prioridad": "CRÍTICA",
                    "Tipo": "Sucursal sin QF",
                    "Sucursal": r["nombre"],
                    "Detalle": "Sin QF titular y sin DT complementario informado",
                })

    if not alertas:
        st.success("🟢 No se detectan alertas críticas con la información cargada.")
    else:
        st.dataframe(pd.DataFrame(alertas), use_container_width=True)

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
               c.cargo AS Cargo, s.nombre AS Sucursal,
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
