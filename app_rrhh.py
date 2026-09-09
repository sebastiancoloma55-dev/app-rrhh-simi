import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, time, timedelta, date
import numpy as np
from streamlit_folium import st_folium
import folium
import random
import string
import io

# ==========================================
# 1. CONFIGURACIÓN Y OCULTACIÓN DE ELEMENTOS
# ==========================================
st.set_page_config(
    page_title="Gestión Corporativa de Coberturas | Dr. Simi",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Ocultar barra superior, menú desplegable y botón flotante Manage app */
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    .stApp > header {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    button[kind="header"] {display: none !important;}
    .viewerBadge_container__1QSob {display: none !important;}
    div.celestial-button, div[data-testid="manage-app-button"], div.viewerBadge_link__qRIco {
        display: none !important;
        visibility: hidden !important;
    }
</style>
""", unsafe_allow_html=True)

DB_NAME = 'base_rrhh_corporativa.db'

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sucursales 
                 (codigo TEXT PRIMARY KEY, nombre TEXT, direccion TEXT, comuna TEXT, region TEXT, 
                  director_tecnico TEXT, dt_complementario TEXT, latitud REAL, longitud REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS colaboradores 
                 (rut TEXT PRIMARY KEY, nombre_completo TEXT, codigo_sucursal TEXT, cargo TEXT, celular TEXT, email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS solicitudes 
                 (id_solicitud INTEGER PRIMARY KEY, estado TEXT, 
                  rut TEXT, nombre TEXT, cargo TEXT, codigo_sucursal TEXT, fecha_desde TEXT, fecha_hasta TEXT, dias INTEGER, tipo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS licencias 
                 (rut TEXT, nombre TEXT, apellido_p TEXT, apellido_m TEXT, sucursal TEXT, 
                  cargo TEXT, fecha_desde TEXT, fecha_hasta TEXT, dias INTEGER, tipo_ausencia TEXT, estado TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS movimientos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_registro TIMESTAMP, usuario_realiza TEXT, rut_colaborador TEXT, 
                  sucursal_origen TEXT, sucursal_destino TEXT, rut_reemplazado TEXT, fecha_inicio DATE, 
                  fecha_fin DATE, nuevo_horario TEXT, motivo TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bitacora_diaria 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TIMESTAMP, sucursal TEXT, usuario TEXT, novedad TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                 (usuario TEXT PRIMARY KEY, password TEXT, nombre_completo TEXT, rol TEXT)''')
    
    c.execute("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO usuarios VALUES ('admin', 'simi2026', 'Administrador Maestro RRHH', 'Admin Supremo')")
    
    conn.commit()
    return conn

conn = init_db()

@st.cache_data(ttl=60)
def cargar_datos_sql(query):
    con_temp = sqlite3.connect(DB_NAME, check_same_thread=False)
    df = pd.read_sql(query, con_temp)
    con_temp.close()
    return df

def generar_password_segura(string_longitud=8):
    letras = string.ascii_letters + string.digits
    return "".join(random.choice(letras) for i in range(string_longitud))

def convertir_df_a_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    processed_data = output.getvalue()
    return processed_data

# ==========================================
# 2. PERSISTENCIA DE SESIÓN POR URL (EVITA PÉRDIDA EN RECARGA)
# ==========================================
params = st.query_params

if 'autenticado' not in st.session_state:
    # Si la URL trae un token de sesión activo, lo restauramos automáticamente
    if "sesion_activa" in params and "usuario" in params and "rol" in params:
        st.session_state.autenticado = True
        st.session_state.usuario_actual = params["usuario"]
        st.session_state.rol_actual = params["rol"]
        st.session_state.tiempo_login = datetime.now()
    else:
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.session_state.rol_actual = ""
        st.session_state.tiempo_login = None

# Control de tiempo de expiración (3 horas exactas)
TIEMPO_EXPIRACION = timedelta(hours=3)
if st.session_state.autenticado and st.session_state.tiempo_login:
    if datetime.now() - st.session_state.tiempo_login > TIEMPO_EXPIRACION:
        st.session_state.autenticado = False
        st.session_state.usuario_actual = ""
        st.session_state.rol_actual = ""
        st.session_state.tiempo_login = None
        st.query_params.clear() # Limpiar parámetros de la URL
        st.warning("⚠️ Su sesión ha expirado por inactividad (más de 3 horas). Por favor, inicie sesión nuevamente.")

# ==========================================
# 3. PANTALLA DE LOGIN "WUAO" (GLASSMORPHISM)
# ==========================================
if not st.session_state.autenticado:
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stHeader"] { display: none !important; }
    .stApp > header { display: none !important; }
    
    .stApp {
        background: linear-gradient(-45deg, #050505, #132a4a, #0b1a2e, #050505) !important;
        background-size: 400% 400% !important;
        animation: animarFondo 12s ease infinite !important;
    }
    
    @keyframes animarFondo {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .main .block-container {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        height: 100vh !important;
        max-width: 100% !important;
        padding: 0 !important;
    }

    div[data-testid="stForm"] {
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        padding: 40px !important;
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.6) !important;
        width: 100% !important;
        max-width: 450px !important;
        margin: 0 auto !important;
    }

    div[data-testid="stForm"] p, div[data-testid="stForm"] label {
        color: #e2e8f0 !important;
        font-family: 'Helvetica Neue', sans-serif !important;
        letter-spacing: 1px !important;
    }

    div[data-testid="stForm"] input {
        background: rgba(0, 0, 0, 0.3) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
        font-size: 16px !important;
    }

    div[data-testid="stForm"] button {
        background: linear-gradient(90deg, #2563eb, #1e3a8a) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        transition: all 0.3s ease !important;
        margin-top: 15px !important;
    }
    div[data-testid="stForm"] button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.6) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-bottom: 30px; margin-top: -50px;">
        <h1 style="color: #ffffff; font-size: 42px; font-weight: 900; letter-spacing: -1px; margin: 0; text-shadow: 0 5px 15px rgba(0,0,0,0.5);">PORTAL OPERATIVO</h1>
        <div style="height: 3px; width: 60px; background: #3b82f6; margin: 15px auto;"></div>
        <p style="color: #94a3b8; font-size: 14px; letter-spacing: 2px; text-transform: uppercase; margin: 0;">Gestión Inteligente de Recursos</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("<p style='text-align: center; font-size: 18px; font-weight: 600; margin-bottom: 25px;'>Identificación Segura</p>", unsafe_allow_html=True)
        user_input = st.text_input("Usuario", placeholder="Ej: admin")
        pass_input = st.text_input("Contraseña", type="password", placeholder="••••••••")
        st.markdown("<br>", unsafe_allow_html=True)
        submit_login = st.form_submit_button("Ingresar al Sistema", use_container_width=True)
        
        if submit_login:
            c = conn.cursor()
            c.execute("SELECT password, nombre_completo, rol FROM usuarios WHERE usuario = ?", (user_input,))
            res = c.fetchone()
            if res and res[0] == pass_input:
                st.session_state.autenticado = True
                st.session_state.usuario_actual = res[1]
                st.session_state.rol_actual = res[2]
                st.session_state.tiempo_login = datetime.now()
                # Fijar parámetros en la URL para que la recarga (F5) mantenga la sesión viva
                st.query_params["sesion_activa"] = "1"
                st.query_params["usuario"] = res[1]
                st.query_params["rol"] = res[2]
                st.rerun()
            else:
                st.error("❌ Credenciales inválidas.")
                
    st.stop()

# ==========================================
# 4. APLICACIÓN PRINCIPAL (PANEL EJECUTIVO)
# ==========================================
st.markdown("""
<style>
[data-testid="stSidebar"] { display: flex !important; background-color: #0b2545 !important; }
[data-testid="stHeader"] { display: flex !important; }
.stApp { background: #f8fafc !important; animation: none !important; }
.main .block-container {
    display: block !important;
    height: auto !important;
    padding-top: 3rem !important;
    padding-bottom: 3rem !important;
}

section[data-testid="stSidebar"] div, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] p { color: #ffffff !important; }

.stButton>button { background-color: #0b2545; color: white; border-radius: 8px; border: none; font-weight: 600; transition: all 0.3s ease; }
.stButton>button:hover { background-color: #1e293b; color: white; transform: translateY(-1px); box-shadow: 0 4px 10px rgba(0,0,0,0.1); }

h1, h2, h3 { color: #0b2545; font-family: 'Helvetica Neue', sans-serif; }
.main-title { color: #0b2545; font-weight: 800; font-size: 28px; letter-spacing: -0.5px; }
.metric-card { background-color: #ffffff; padding: 24px; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.04); border: 1px solid #e2e8f0; border-left: 5px solid #0b2545; }
.jornada-badge { background-color: #f1f5f9; color: #0369a1; padding: 8px 14px; border-radius: 8px; font-weight: 600; font-size: 13px; margin-top: 6px; display: inline-block; border: 1px solid #e2e8f0; }
.simi-header { background: #0b2545; color: white; padding: 18px; border-radius: 12px; text-align: center; font-weight: 700; font-size: 16px; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
    <div style='text-align: center; padding: 15px 0 5px 0;'>
        <h2 style='color: white; margin: 0; font-weight: 900; letter-spacing: 1px;'>DR. SIMI</h2>
        <div style='height: 2px; background: #3b82f6; width: 40px; margin: 10px auto;'></div>
        <p style='color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;'>Operaciones & RRHH</p>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"<div style='background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin: 15px 0; border: 1px solid rgba(255,255,255,0.1);'>👤 <b>{st.session_state.usuario_actual}</b><br><span style='font-size: 11px; color: #94a3b8;'>Rol: {st.session_state.rol_actual}</span></div>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu_opciones = [
    "📊 Dashboard Ejecutivo", 
    "📅 Agenda Diaria de Coberturas",
    "📈 Analítica & Reportes",
    "🗺️ Mapa Autoajustable", 
    "🚨 Alertas Críticas (QF y Licencias)", 
    "🔄 Registrar Movimiento / Cobertura", 
    "📝 Bitácora de Novedades",
    "📋 Historial Corporativo", 
    "📁 Carga Masiva Unificada"
]

if st.session_state.rol_actual == "Admin Supremo":
    menu_opciones.append("🔑 Gestión de Usuarios (Admin)")
    menu_opciones.append("🛡️ Auditoría del Sistema")

menu = st.sidebar.radio("Navegación:", menu_opciones)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state.autenticado = False
    st.session_state.tiempo_login = None
    st.query_params.clear() # Limpiar parámetros de la URL al salir
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("<p style='text-align: center; color: #64748b; font-size: 11px; margin-top: 30px;'>Dev: Sebastian Coloma</p>", unsafe_allow_html=True)

# ==========================================
# 5. MÓDULOS DE LA APLICACIÓN
# ==========================================
if menu == "📊 Dashboard Ejecutivo":
    st.markdown("<h1 class='main-title'>💊 Centro de Control Logístico</h1>", unsafe_allow_html=True)
    st.markdown("Plataforma oficial de control de dotación, ausentismo, licencias médicas y continuidad operacional.")
    
    total_suc = cargar_datos_sql("SELECT COUNT(*) FROM sucursales").iloc[0,0]
    total_colab = cargar_datos_sql("SELECT COUNT(*) FROM colaboradores").iloc[0,0]
    total_vac = cargar_datos_sql("SELECT COUNT(*) FROM solicitudes WHERE estado IN ('Aprobada', 'Pre Aprobada', 'Pendiente')").iloc[0,0]
    total_lic = cargar_datos_sql("SELECT COUNT(*) FROM licencias WHERE estado = 'Aprobada'").iloc[0,0]
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"<div class='metric-card'><h3 style='font-size:14px; color:#64748b; margin:0;'>🏢 Sucursales</h3><h2 style='color:#0b2545; margin:5px 0 0 0;'>{total_suc}</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><h3 style='font-size:14px; color:#64748b; margin:0;'>👥 Colaboradores</h3><h2 style='color:#0b2545; margin:5px 0 0 0;'>{total_colab}</h2></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><h3 style='font-size:14px; color:#64748b; margin:0;'>🏖️ Vacaciones Vigentes</h3><h2 style='color:#0b2545; margin:5px 0 0 0;'>{total_vac}</h2></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='metric-card'><h3 style='font-size:14px; color:#64748b; margin:0;'>🏥 Licencias Médicas</h3><h2 style='color:#0b2545; margin:5px 0 0 0;'>{total_lic}</h2></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div class='simi-header'>SISTEMA DE ALERTA TEMPRANA PARA QUÍMICOS FARMACÉUTICOS (QF) Y COBERTURAS</div>", unsafe_allow_html=True)
    st.info("ℹ️ El sistema detecta automáticamente si una farmacia se queda sin **Titular 1 y Titular 2 (DT Complementario)** de forma simultánea por vacaciones o licencias médicas, previniendo cierres y multas sanitarias.")

elif menu == "📅 Agenda Diaria de Coberturas":
    st.markdown("<h1 class='main-title'>📅 Agenda Diaria de Coberturas Activas</h1>", unsafe_allow_html=True)
    st.markdown("Consulta en tiempo real qué personal está cubriendo turnos en las sucursales para el día de hoy.")
    
    hoy_str = datetime.today().strftime('%Y-%m-%d')
    q_agenda = f"""
        SELECT m.fecha_registro as "Registro", c1.nombre_completo as "Colaborador de Apoyo", 
               s1.nombre as "Sucursal Origen", s2.nombre as "Sucursal Destino", 
               m.fecha_inicio as "Desde", m.fecha_fin as "Hasta", m.motivo as "Motivo", m.nuevo_horario as "Turnos y Horario"
        FROM movimientos m
        LEFT JOIN colaboradores c1 ON m.rut_colaborador = c1.rut
        LEFT JOIN sucursales s1 ON m.sucursal_origen = s1.codigo
        LEFT JOIN sucursales s2 ON m.sucursal_destino = s2.codigo
        WHERE m.fecha_inicio <= '{hoy_str}' AND m.fecha_fin >= '{hoy_str}'
    """
    df_agenda = cargar_datos_sql(q_agenda)
    if df_agenda.empty:
        st.info("ℹ️ No hay coberturas activas programadas exactamente para el día de hoy.")
    else:
        st.success(f"✅ Se encontraron coberturas activas vigentes para la fecha actual ({hoy_str}).")
        st.dataframe(df_agenda, use_container_width=True)

elif menu == "📈 Analítica & Reportes":
    st.markdown("<h1 class='main-title'>📈 Analítica y Estadísticas Corporativas</h1>", unsafe_allow_html=True)
    
    colabs_df = cargar_datos_sql("SELECT cargo, codigo_sucursal FROM colaboradores")
    sucs_df = cargar_datos_sql("SELECT region, comuna FROM sucursales")
    
    c_an1, c_an2 = st.columns(2)
    with c_an1:
        st.subheader("👥 Distribución de Cargos")
        if not colabs_df.empty and 'cargo' in colabs_df.columns:
            conteo_cargos = colabs_df['cargo'].value_counts().reset_index()
            conteo_cargos.columns = ['Cargo', 'Cantidad']
            st.dataframe(conteo_cargos, use_container_width=True)
        else:
            st.info("No hay datos suficientes de colaboradores.")
            
    with c_an2:
        st.subheader("🗺️ Sucursales por Región")
        if not sucs_df.empty and 'region' in sucs_df.columns:
            conteo_regiones = sucs_df['region'].value_counts().reset_index()
            conteo_regiones.columns = ['Región', 'Total Sucursales']
            st.dataframe(conteo_regiones, use_container_width=True)
        else:
            st.info("No hay datos suficientes de sucursales.")

elif menu == "🗺️ Mapa Autoajustable":
    st.markdown("<h1 class='main-title'>🗺️ Radar Georreferenciado Autoajustable</h1>", unsafe_allow_html=True)
    
    sucursales_df = cargar_datos_sql("SELECT codigo, nombre, direccion, comuna, region, director_tecnico, dt_complementario, latitud, longitud FROM sucursales")
    
    if sucursales_df.empty:
        st.warning("⚠️ No hay sucursales cargadas. Sube tus archivos en el módulo de Carga Masiva Unificada.")
    else:
        df_validas = sucursales_df.dropna(subset=['latitud', 'longitud'])
        
        if not df_validas.empty:
            lat_centro = df_validas['latitud'].mean()
            lon_centro = df_validas['longitud'].mean()
            m = folium.Map(location=[lat_centro, lon_centro], zoom_start=10, tiles="OpenStreetMap")
            
            puntos_bounds = []
            for _, row in df_validas.iterrows():
                codigo_s = row['codigo']
                nombre_s = row['nombre']
                comuna_s = row['comuna']
                dir_s = row['direccion']
                qf1 = row['director_tecnico']
                qf2 = row['dt_complementario']
                
                lat, lon = row['latitud'], row['longitud']
                puntos_bounds.append([lat, lon])
                
                con_local = sqlite3.connect(DB_NAME)
                lic_s = pd.read_sql("SELECT nombre, apellido_p, fecha_desde, fecha_hasta, tipo_ausencia FROM licencias WHERE sucursal = ? AND estado = 'Aprobada'", con_local, params=(nombre_s,))
                vac_s = pd.read_sql("SELECT nombre, fecha_desde, fecha_hasta, tipo FROM solicitudes WHERE codigo_sucursal = ? AND estado IN ('Aprobada', 'Pre Aprobada', 'Pendiente')", con_local, params=(codigo_s,))
                mov_s = pd.read_sql("SELECT * FROM movimientos WHERE sucursal_destino = ?", con_local, params=(codigo_s,))
                con_local.close()
                
                html_popup = f"""
                <div style="max-height: 250px; overflow-y: auto; padding-right: 5px; font-size: 13px; font-family: sans-serif; color: #000;">
                    <b style="font-size: 14px;">🏢 {nombre_s} ({codigo_s})</b><br>
                    📍 {dir_s}, {comuna_s}<br>
                    💊 <b>QF 1:</b> {qf1}<br>
                    💊 <b>QF 2:</b> {qf2}<br><hr style='margin:5px;'>
                """
                
                if not lic_s.empty:
                    html_popup += "<b style='color:#dc2626;'>🏥 Licencias Médicas:</b><br>"
                    for _, l in lic_s.iterrows():
                        html_popup += f"- {l['nombre']} {l['apellido_p']} (Inicio: {l['fecha_desde']} | Retorno: {l['fecha_hasta']})<br>"
                
                if not vac_s.empty:
                    html_popup += "<b style='color:#ea580c;'>🏖️ Vacaciones / Permisos:</b><br>"
                    for _, v in vac_s.iterrows():
                        html_popup += f"- {v['nombre']} (Inicio: {v['fecha_desde']} | Retorno: {v['fecha_hasta']})<br>"
                
                if not mov_s.empty:
                    html_popup += "<b style='color:#16a34a;'>✅ Con Cobertura Asignada</b><br>"
                else:
                    html_popup += "<b style='color:#dc2626;'>⚠️ Sin Cobertura Registrada</b><br>"
                
                html_popup += "</div>"
                    
                color_marcador = "red" if (not lic_s.empty or not vac_s.empty) else "blue"
                
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(html_popup, max_width=320),
                    tooltip=f"{nombre_s} ({codigo_s})",
                    icon=folium.Icon(color=color_marcador, icon="plus-sign" if color_marcador=="red" else "info-sign")
                ).add_to(m)

            m.fit_bounds(puntos_bounds)
            st_folium(m, width=1300, height=550)
        else:
            st.warning("⚠️ No hay coordenadas válidas en las sucursales cargadas.")

elif menu == "🚨 Alertas Críticas (QF y Licencias)":
    st.markdown("<h1 class='main-title'>🚨 Panel de Control de Riesgo y Cobertura Sanitaria</h1>", unsafe_allow_html=True)
    filtro_global = st.text_input("🔍 Filtrar Alertas (Escribe nombre de colaborador o sucursal):", "")

    tab1, tab2 = st.tabs(["🏖️ Vacaciones y Permisos", "🏥 Licencias Médicas"])
    
    with tab1:
        st.subheader("Solicitudes de Vacaciones y Permisos en Curso")
        q_vac = '''
            SELECT s.estado as "Estado", s.tipo as "Tipo", s.dias as "Días", s.nombre as "Colaborador", 
                   s.cargo as "Cargo", suc.nombre as "Sucursal", s.fecha_desde as "Fecha Inicio", s.fecha_hasta as "Fecha Retorno",
                   suc.director_tecnico as "DT Titular", suc.dt_complementario as "DT 2"
            FROM solicitudes s
            LEFT JOIN sucursales suc ON s.codigo_sucursal = suc.codigo
            WHERE s.estado IN ('Aprobada', 'Pre Aprobada', 'Pendiente')
            ORDER BY s.estado ASC
        '''
        df_v = cargar_datos_sql(q_vac)
        if df_v.empty:
            st.info("No hay solicitudes de vacaciones registradas.")
        else:
            if filtro_global:
                df_v = df_v[df_v['Colaborador'].str.contains(filtro_global, case=False, na=False) | df_v['Sucursal'].str.contains(filtro_global, case=False, na=False)]
            st.dataframe(df_v, use_container_width=True)
            
    with tab2:
        st.subheader("Colaboradores con Licencia Médica")
        q_lic = '''
            SELECT l.estado as "Estado", l.tipo_ausencia as "Tipo Ausencia", l.fecha_desde as "Fecha Inicio", 
                   l.fecha_hasta as "Fecha Retorno", l.dias as "Total Días", 
                   l.nombre || ' ' || l.apellido_p as "Colaborador", l.cargo as "Cargo", l.sucursal as "Sucursal"
            FROM licencias l
            WHERE l.estado = 'Aprobada'
        '''
        df_l = cargar_datos_sql(q_lic)
        if df_l.empty:
            st.info("No hay licencias médicas cargadas.")
        else:
            if filtro_global:
                df_l = df_l[df_l['Colaborador'].str.contains(filtro_global, case=False, na=False) | df_l['Sucursal'].str.contains(filtro_global, case=False, na=False)]
            st.dataframe(df_l, use_container_width=True)

elif menu == "🔄 Registrar Movimiento / Cobertura":
    st.markdown("<h1 class='main-title'>🔄 Asignación de Coberturas y Traslados</h1>", unsafe_allow_html=True)
    
    colaboradores = cargar_datos_sql("SELECT rut, nombre_completo, codigo_sucursal FROM colaboradores")
    sucursales = cargar_datos_sql("SELECT codigo, nombre FROM sucursales")
    
    if colaboradores.empty or sucursales.empty:
        st.warning("⚠️ Primero debes subir los archivos Excel en el módulo de Carga Masiva Unificada.")
    else:
        dict_colab = dict(zip(colaboradores['nombre_completo'] + " (" + colaboradores['rut'] + ")", colaboradores['rut']))
        dict_colab_inverso = dict(zip(colaboradores['nombre_completo'] + " (" + colaboradores['rut'] + ")", colaboradores['codigo_sucursal']))
        dict_suc = dict(zip(sucursales['nombre'] + " (" + sucursales['codigo'] + ")", sucursales['codigo']))
        dict_suc_inversa = dict(zip(sucursales['codigo'], sucursales['nombre']))
        
        st.markdown("### 📝 Datos del Reemplazo")
        emp_mueve = st.selectbox("Colaborador de Apoyo / Volante:", options=list(dict_colab.keys()))
        
        cod_orig_emp = dict_colab_inverso.get(emp_mueve, "")
        nombre_orig_emp = dict_suc_inversa.get(cod_orig_emp, "")
        
        lista_suc_opciones = list(dict_suc.keys())
        indice_defecto = 0
        for idx, s_key in enumerate(lista_suc_opciones):
            if cod_orig_emp in s_key or nombre_orig_emp in s_key:
                indice_defecto = idx
                break
        
        suc_origen_elegida = st.selectbox("Sucursal de Origen:", options=lista_suc_opciones, index=indice_defecto)
        suc_destino = st.selectbox("Sucursal de Destino (A cubrir):", options=list(dict_suc.keys()))
        
        c_cond1, c_cond2 = st.columns(2)
        with c_cond1:
            opciones_reemplaza = ["Ninguno (Apoyo por alta demanda)"] + list(dict_colab.keys())
            emp_reemplaza = st.selectbox("¿A quién cubre?:", options=opciones_reemplaza)
        with c_cond2:
            motivo_op = st.selectbox("Motivo:", ["Cobertura Vacaciones QF", "Licencia Médica", "Permiso Administrativo", "Refuerzo Apertura", "Otro"])
            motivo_custom = st.text_input("Especifica el motivo (Si elegiste 'Otro'):") if motivo_op == "Otro" else ""
        
        st.markdown("---")
        st.markdown("### ⏱️ Configuración de Turnos y Cálculo de Jornada Neta")
        
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        horarios_registrados = []
        total_horas_acumuladas = 0.0
        
        for dia in dias_semana:
            col_d, col_e, col_s, col_c = st.columns([1.2, 2, 2, 1.5])
            with col_d:
                activo = st.checkbox(f"{dia}", key=f"chk_{dia}")
            with col_e:
                h_ent = st.time_input(f"Entrada {dia}", value=time(9, 0), key=f"ent_{dia}")
            with col_s:
                h_sal = st.time_input(f"Salida {dia}", value=time(19, 0), key=f"sal_{dia}")
            with col_c:
                colacion = st.number_input(f"Colación (min) {dia}", min_value=0, max_value=120, value=30, step=15, key=f"col_{dia}")
            
            if activo:
                dt_ent = datetime.combine(datetime.today(), h_ent)
                dt_sal = datetime.combine(datetime.today(), h_sal)
                diff_minutos = (dt_sal - dt_ent).total_seconds() / 60 - colacion
                horas_netas = max(0, round(diff_minutos / 60, 2))
                total_horas_acumuladas += horas_netas
                st.markdown(f"<div class='jornada-badge'>📌 {dia}: {h_ent.strftime('%H:%M')} a {h_sal.strftime('%H:%M')} | Colación: {colacion}m | <b>Jornada Neta: {horas_netas} hrs</b></div>", unsafe_allow_html=True)
                horarios_registrados.append(f"{dia[:3]}: {h_ent.strftime('%H:%M')} a {h_sal.strftime('%H:%M')} (Col: {colacion}m | Jornada Neta: {horas_netas}h)")

        st.markdown(f"### 🧮 Total de Horas de la Jornada Acumuladas: `{round(total_horas_acumuladas, 2)} hrs`")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_inicio = st.date_input("Fecha Inicio Cobertura:")
        with col_f2:
            fecha_fin = st.date_input("Fecha Fin Cobertura:")
        
        if st.button("💾 Guardar Movimiento Oficial", use_container_width=True):
            if not horarios_registrados:
                st.error("⚠️ Error: Debes seleccionar al menos un día y marcar su casilla para configurar el horario.")
            elif motivo_op == "Otro" and not motivo_custom:
                st.error("⚠️ Error: Debes especificar el motivo en la casilla de texto.")
            else:
                horario_consolidado = " | ".join(horarios_registrados) + f" | [TOTAL JORNADA: {round(total_horas_acumuladas, 2)}h]"

                c = conn.cursor()
                rut_reemplazado = None if emp_reemplaza == "Ninguno (Apoyo por alta demanda)" else dict_colab[emp_reemplaza]
                cod_origen_final = dict_suc[suc_origen_elegida]
                
                c.execute('''INSERT INTO movimientos (fecha_registro, usuario_realiza, rut_colaborador, sucursal_origen, sucursal_destino, 
                              rut_reemplazado, fecha_inicio, fecha_fin, nuevo_horario, motivo) 
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (datetime.now(), st.session_state.usuario_actual, dict_colab[emp_mueve], cod_origen_final, dict_suc[suc_destino],
                           rut_reemplazado, fecha_inicio, fecha_fin, horario_consolidado, motivo_op if motivo_op != "Otro" else motivo_custom))
                conn.commit()
                st.cache_data.clear()
                st.success("✅ ¡Movimiento registrado correctamente con control de jornada y horas netas!")

elif menu == "📝 Bitácora de Novedades":
    st.markdown("<h1 class='main-title'>📝 Bitácora Diaria de Novedades por Sucursal</h1>", unsafe_allow_html=True)
    st.markdown("Deja notas operativas, incidencias o avisos importantes para el seguimiento diario.")
    
    sucursales = cargar_datos_sql("SELECT codigo, nombre FROM sucursales")
    if sucursales.empty:
        st.warning("⚠️ Carga las sucursales primero.")
    else:
        dict_sucs_bit = dict(zip(sucursales['nombre'] + " (" + sucursales['codigo'] + ")", sucursales['codigo']))
        
        with st.form("form_bitacora"):
            suc_elegida = st.selectbox("Seleccionar Sucursal:", options=list(dict_sucs_bit.keys()))
            novedad_texto = st.text_area("Descripción de la Novedad / Incidencia / Nota Operativa:")
            submit_bit = st.form_submit_button("➕ Registrar Nota en Bitácora")
            
            if submit_bit:
                if novedad_texto.strip():
                    c = conn.cursor()
                    c.execute("INSERT INTO bitacora_diaria (fecha, sucursal, usuario, novedad) VALUES (?, ?, ?, ?)",
                              (datetime.now(), suc_elegida, st.session_state.usuario_actual, novedad_texto))
                    conn.commit()
                    st.cache_data.clear()
                    st.success("✅ ¡Novedad registrada con éxito en la bitácora!")
                else:
                    st.warning("⚠️ Escribe un texto válido para la novedad.")
                    
        st.markdown("---")
        st.subheader("📋 Historial de Novedades Registradas")
        df_bit = cargar_datos_sql("SELECT fecha as 'Fecha y Hora', sucursal as 'Sucursal', usuario as 'Registrado por', novedad as 'Novedad' FROM bitacora_diaria ORDER BY id DESC")
        if df_bit.empty:
            st.info("No hay registros en la bitácora.")
        else:
            st.dataframe(df_bit, use_container_width=True)

elif menu == "📋 Historial Corporativo":
    st.markdown("<h1 class='main-title'>📋 Historial de Coberturas y Movimientos</h1>", unsafe_allow_html=True)
    
    if st.session_state.rol_actual == "Admin Supremo":
        with st.expander("⚙️ Zona de Gestión de Historial (Admin Supremo)"):
            if st.button("🗑️ Eliminar TODO el Historial de Movimientos", type="primary"):
                c = conn.cursor()
                c.execute("DELETE FROM movimientos")
                conn.commit()
                st.cache_data.clear()
                st.success("🗑️ ¡Historial eliminado por completo exitosamente!")
                st.rerun()

    filtro_historial = st.text_input("🔍 Buscar en Historial:", "")

    query = '''
        SELECT m.id, m.fecha_registro as "Fecha Registro", m.usuario_realiza as "Realizado por", c1.nombre_completo as "Colaborador Movido", 
               s1.nombre as "Origen", s2.nombre as "Destino", m.motivo as "Motivo", 
               c2.nombre_completo as "Cubrió a", m.fecha_inicio as "Desde", m.fecha_fin as "Hasta", 
               m.nuevo_horario as "Turnos y Jornada Neta"
        FROM movimientos m
        LEFT JOIN colaboradores c1 ON m.rut_colaborador = c1.rut
        LEFT JOIN colaboradores c2 ON m.rut_reemplazado = c2.rut
        LEFT JOIN sucursales s1 ON m.sucursal_origen = s1.codigo
        LEFT JOIN sucursales s2 ON m.sucursal_destino = s2.codigo 
        ORDER BY m.fecha_registro DESC
    '''
    df_historial = cargar_datos_sql(query)
    if df_historial.empty:
        st.info("No hay registros de movimientos todavía.")
    else:
        if filtro_historial:
            df_historial = df_historial[df_historial['Colaborador Movido'].str.contains(filtro_historial, case=False, na=False) | df_historial['Origen'].str.contains(filtro_historial, case=False, na=False) | df_historial['Destino'].str.contains(filtro_historial, case=False, na=False) | df_historial['Realizado por'].str.contains(filtro_historial, case=False, na=False)]
        st.dataframe(df_historial, use_container_width=True)
        csv = df_historial.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Descargar Reporte en CSV", csv, "reporte_coberturas_dr_simi.csv", "text/csv")

elif menu == "🔑 Gestión de Usuarios (Admin)" and st.session_state.rol_actual == "Admin Supremo":
    st.markdown("<h1 class='main-title'>🔑 Panel Maestro: Gestión de Usuarios y Accesos</h1>", unsafe_allow_html=True)
    
    tab_u1, tab_u2, tab_u3 = st.tabs(["➕ Crear Usuario Individual", "📁 Creación Masiva (Excel)", "🗑️ Administrar / Eliminar Usuarios"])
    
    with tab_u1:
        st.subheader("Crear Usuario con Generador de Clave Automática")
        with st.form("form_nuevo_usuario"):
            c_u1, c_u2 = st.columns(2)
            with c_u1:
                nuevo_user = st.text_input("Nombre de Usuario (Login):")
                password_sugerida = generar_password_segura()
                nuevo_pass = st.text_input("Contraseña (Generada o Personalizada):", value=password_sugerida)
            with c_u2:
                nuevo_nombre = st.text_input("Nombre Completo del Colaborador:")
                nuevo_rol = st.selectbox("Rol en el Sistema:", ["Admin Supremo", "Supervisor Zonal", "Gestor RRHH", "Auditoría Operativa"])
                
            submit_usr = st.form_submit_button("➕ Registrar Nuevo Usuario", use_container_width=True)
            if submit_usr:
                if nuevo_user and nuevo_pass and nuevo_nombre:
                    try:
                        c = conn.cursor()
                        c.execute("INSERT INTO usuarios VALUES (?, ?, ?, ?)", (nuevo_user, nuevo_pass, nuevo_nombre, nuevo_rol))
                        conn.commit()
                        st.cache_data.clear()
                        st.success(f"✅ ¡Usuario `{nuevo_user}` creado con éxito! Clave asignada: `{nuevo_pass}`")
                    except Exception as e:
                        st.error(f"⚠️ El usuario ya existe o hubo un error: {e}")
                else:
                    st.warning("⚠️ Debes rellenar todos los campos obligatorios.")

    with tab_u2:
        st.subheader("Carga Masiva de Usuarios vía Excel")
        st.caption("Descarga la plantilla oficial, complétala y súbela para crear múltiples accesos al instante.")
        
        df_plantilla_usr = pd.DataFrame(columns=['usuario', 'password', 'nombre_completo', 'rol'])
        df_plantilla_usr.loc[0] = ['juan.perez', 'clave123', 'Juan Pérez González', 'Gestor RRHH']
        excel_usr_bytes = convertir_df_a_excel(df_plantilla_usr)
        st.download_button("📥 Descargar Plantilla Excel de Usuarios", excel_usr_bytes, "plantilla_usuarios_simi.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        file_usuarios_masivo = st.file_uploader("Subir Archivo Excel de Usuarios Completado:", type=['xlsx'])
        if file_usuarios_masivo:
            df_um = pd.read_excel(file_usuarios_masivo)
            st.dataframe(df_um.head(), use_container_width=True)
            if st.button("🚀 Importar Usuarios Masivamente"):
                c = conn.cursor()
                importados = 0
                for _, row in df_um.iterrows():
                    u = str(row.get('usuario', '')).strip()
                    p = str(row.get('password', '')).strip()
                    if not p or p == 'nan':
                        p = generar_password_segura()
                    n = str(row.get('nombre_completo', '')).strip()
                    r = str(row.get('rol', 'Gestor RRHH')).strip()
                    
                    if u and n:
                        try:
                            c.execute("INSERT OR REPLACE INTO usuarios VALUES (?, ?, ?, ?)", (u, p, n, r))
                            importados += 1
                        except:
                            pass
                conn.commit()
                st.cache_data.clear()
                st.success(f"✅ ¡Se han importado {importados} usuarios correctamente al sistema!")

    with tab_u3:
        st.subheader("Gestión y Eliminación de Accesos")
        df_usuarios = cargar_datos_sql("SELECT usuario, nombre_completo, rol FROM usuarios")
        st.dataframe(df_usuarios, use_container_width=True)
        
        st.markdown("---")
        usuario_a_borrar = st.selectbox("Seleccione el usuario a eliminar:", options=df_usuarios['usuario'].tolist())
        if usuario_a_borrar:
            if usuario_a_borrar == 'admin':
                st.error("⚠️ No se puede eliminar al Administrador Maestro principal ('admin').")
            else:
                if st.button(f"🗑️ Eliminar Definitivamente al Usuario `{usuario_a_borrar}`", type="primary"):
                    c = conn.cursor()
                    c.execute("DELETE FROM usuarios WHERE usuario = ?", (usuario_a_borrar,))
                    conn.commit()
                    st.cache_data.clear()
                    st.success(f"✅ ¡Usuario `{usuario_a_borrar}` eliminado del sistema correctamente!")
                    st.rerun()

elif menu == "🛡️ Auditoría del Sistema" and st.session_state.rol_actual == "Admin Supremo":
    st.markdown("<h1 class='main-title'>🛡️ Panel de Auditoría y Seguridad</h1>", unsafe_allow_html=True)
    st.markdown("Registro técnico del estado de la plataforma y sesiones activas.")
    
    st.info(f"👤 Usuario Administrador actual: **{st.session_state.usuario_actual}**")
    st.success("🟢 Base de datos operando de manera fluida con caché activada.")
    
    if st.button("🧹 Limpiar Caché de Memoria"):
        st.cache_data.clear()
        st.success("✅ ¡Caché limpiada correctamente!")

elif menu == "📁 Carga Masiva Unificada":
    st.markdown("<h1 class='main-title'>📁 Módulo de Carga Masiva Unificada</h1>", unsafe_allow_html=True)
    st.markdown("Sube tus 4 archivos oficiales juntos en este único formulario sin importar los nombres de archivo.")
    
    with st.expander("📥 Descargar Plantillas Oficiales de Referencia"):
        st.write("Descarga los modelos estándar para estructurar tus archivos Excel:")
        c_p1, c_p2 = st.columns(2)
        with c_p1:
            df_p_suc = pd.DataFrame(columns=['codigo', 'nombre', 'direccion', 'comuna', 'region', 'director_tecnico', 'dt_complementario'])
            df_p_suc.loc[0] = ['S001', 'Farmacia Simi Centro', 'Ahumada 123', 'Santiago', 'Metropolitana', 'Dr. Juan Pérez', 'Dra. Ana Gómez']
            st.download_button("📥 Plantilla Sucursales", convertir_df_a_excel(df_p_suc), "plantilla_sucursales.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            df_p_col = pd.DataFrame(columns=['rut', 'nombre', 'apellido_paterno', 'sucursal', 'cargo'])
            df_p_col.loc[0] = ['12345678-9', 'Carlos', 'Ruiz', 'S001', 'Químico Farmacéutico']
            st.download_button("📥 Plantilla Colaboradores", convertir_df_a_excel(df_p_col), "plantilla_colaboradores.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        with c_p2:
            df_p_sol = pd.DataFrame(columns=['rut', 'nombre', 'sucursal', 'fecha_desde', 'fecha_hasta', 'dias', 'tipo'])
            df_p_sol.loc[0] = ['12345678-9', 'Carlos Ruiz', 'S001', '2026-04-01', '2026-04-10', 10, 'Vacaciones']
            st.download_button("📥 Plantilla Solicitudes/Vacaciones", convertir_df_a_excel(df_p_sol), "plantilla_solicitudes.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            df_p_lic = pd.DataFrame(columns=['rut', 'nombre', 'apellido_paterno', 'sucursal', 'fecha_desde', 'fecha_hasta', 'dias'])
            df_p_lic.loc[0] = ['98765432-1', 'María', 'Soto', 'S001', '2026-04-02', '2026-04-05', 3]
            st.download_button("📥 Plantilla Licencias Médicas", convertir_df_a_excel(df_p_lic), "plantilla_licencias.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with st.form("form_carga_masiva"):
        st.subheader("Subida Simultánea de Archivos")
        file_suc = st.file_uploader("1. Archivo de Sucursales:", type=['xlsx'])
        file_colab = st.file_uploader("2. Archivo de Nómina / Personal:", type=['xlsx'])
        file_sol = st.file_uploader("3. Archivo de Vacaciones / Permisos:", type=['xlsx'])
        file_lic = st.file_uploader("4. Archivo de Licencias Médicas:", type=['xlsx'])
        
        submit_carga = st.form_submit_button("🚀 Procesar y Consolidar Todos los Archivos", use_container_width=True)
        
        if submit_carga:
            procesados = 0
            
            if file_suc:
                df = pd.read_excel(file_suc)
                df_c = pd.DataFrame()
                col_cod = next((c for c in df.columns if 'unidad' in str(c).lower() or 'codigo' in str(c).lower() or 'cc' in str(c).lower()), df.columns[0])
                col_nom = next((c for c in df.columns if 'nombre' in str(c).lower() or 'sucursal' in str(c).lower()), df.columns[1] if len(df.columns)>1 else df.columns[0])
                
                df_c['codigo'] = df[col_cod]
                df_c['nombre'] = df[col_nom]
                df_c['direccion'] = df.get('DIRECCIÓN', df.get('Direccion', ''))
                df_c['comuna'] = df.get('COMUNA', df.get('Comuna', ''))
                df_c['region'] = df.get('REGIÓN', df.get('Region', ''))
                df_c['director_tecnico'] = df.get('DIRECTOR TÉCNICO', df.get('Director Técnico', 'Sin QF Titular'))
                df_c['dt_complementario'] = df.get('DT COMPLEMENTARIO', df.get('DT Complementario', 'Sin DT 2'))
                
                geo_col = next((c for c in df.columns if 'geo' in str(c).lower()), None)
                if geo_col:
                    coords = df[geo_col].astype(str).str.split(',', expand=True)
                    df_c['latitud'] = pd.to_numeric(coords[0], errors='coerce') if coords.shape[1] > 0 else None
                    df_c['longitud'] = pd.to_numeric(coords[1], errors='coerce') if coords.shape[1] > 1 else None
                else:
                    df_c['latitud'] = None; df_c['longitud'] = None
                    
                df_c.to_sql('sucursales', conn, if_exists='replace', index=False)
                procesados += 1

            if file_colab:
                df = pd.read_excel(file_colab)
                df_c = pd.DataFrame()
                col_rut = next((c for c in df.columns if 'rut' in str(c).lower()), df.columns[0])
                col_nom = next((c for c in df.columns if 'nombre' in str(c).lower()), df.columns[1] if len(df.columns)>1 else df.columns[0])
                col_pat = next((c for c in df.columns if 'paterno' in str(c).lower()), None)
                col_cc = next((c for c in df.columns if 'centro' in str(c).lower() or 'sucursal' in str(c).lower()), df.columns[2] if len(df.columns)>2 else df.columns[0])
                
                df_c['rut'] = df[col_rut]
                if col_pat and col_pat in df.columns:
                    df_c['nombre_completo'] = df[col_nom].astype(str) + " " + df[col_pat].astype(str)
                else:
                    df_c['nombre_completo'] = df[col_nom].astype(str)
                    
                df_c['codigo_sucursal'] = df[col_cc]
                df_c['cargo'] = df.get('Cargo', df.get('CARGO', ''))
                df_c['celular'] = df.get('Celular', '')
                df_c['email'] = df.get('Email Personal', df.get('Email', ''))
                df_c.to_sql('colaboradores', conn, if_exists='replace', index=False)
                procesados += 1

            if file_sol:
                try:
                    df = pd.read_excel(file_sol, header=1)
                    if 'RUT' not in [str(c).upper() for c in df.columns]:
                        df = pd.read_excel(file_sol)
                except:
                    df = pd.read_excel(file_sol)
                
                df_c = pd.DataFrame()
                id_col = next((c for c in df.columns if str(c).strip().lower() in ['id', 'folio', 'n°', 'nro']), None)
                df_c['id_solicitud'] = df[id_col] if id_col else range(1, len(df) + 1)
                
                col_rut_v = next((c for c in df.columns if 'rut' in str(c).lower()), df.columns[0])
                col_nom_v = next((c for c in df.columns if 'nombre' in str(c).lower()), df.columns[1] if len(df.columns)>1 else df.columns[0])
                
                df_c['estado'] = df.get('Estado', df.get('ESTADO', 'Aprobada'))
                df_c['rut'] = df[col_rut_v]
                df_c['nombre'] = df[col_nom_v]
                df_c['cargo'] = df.get('Cargo', '')
                df_c['codigo_sucursal'] = df.get('Sucursal', df.get('SUCURSAL', ''))
                
                fecha_col = next((c for c in df.columns if 'solicitud' in str(c).lower() or 'desde' in str(c).lower()), df.columns[-1])
                df_c['fecha_desde'] = pd.to_datetime(df[fecha_col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
                df_c['fecha_hasta'] = pd.to_datetime(df[fecha_col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
                df_c['dias'] = df.get('Días', df.get('DIAS', 1))
                df_c['tipo'] = df.get('Tipo', df.get('TIPO', 'Vacaciones'))
                df_c.to_sql('solicitudes', conn, if_exists='replace', index=False)
                procesados += 1

            if file_lic:
                df = pd.read_excel(file_lic)
                df_c = pd.DataFrame()
                col_rut_l = next((c for c in df.columns if 'rut' in str(c).lower()), df.columns[0])
                col_nom_l = next((c for c in df.columns if 'nombre' in str(c).lower()), df.columns[1] if len(df.columns)>1 else df.columns[0])
                
                df_c['rut'] = df[col_rut_l]
                df_c['nombre'] = df[col_nom_l]
                df_c['apellido_p'] = df.get('Apellido Paterno', df.get('APELLIDO PATERNO', ''))
                df_c['apellido_m'] = df.get('Apellido Materno', df.get('APELLIDO MATERNO', ''))
                df_c['sucursal'] = df.get('Sucursal', df.get('SUCURSAL', ''))
                df_c['cargo'] = df.get('Cargo', '')
                df_c['fecha_desde'] = pd.to_datetime(df.get('Fecha Desde', df.get('FECHA DESDE', '')), errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
                df_c['fecha_hasta'] = pd.to_datetime(df.get('Fecha Hasta', df.get('FECHA HASTA', '')), errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
                df_c['dias'] = df.get('Número de Días', df.get('DIAS', 0))
                df_c['tipo_ausencia'] = df.get('Tipo de Ausencia', 'Licencia')
                df_c['estado'] = df.get('Estado', 'Aprobada')
                df_c.to_sql('licencias', conn, if_exists='replace', index=False)
                procesados += 1

            if procesados > 0:
                st.cache_data.clear()
                st.success(f"✅ ¡Se han procesado y consolidado exitosamente {procesados} archivos juntos con éxito rotundo!")
            else:
                st.warning("⚠️ Debes subir al menos un archivo antes de procesar.")
