import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import base64

# 1. Configuración de la página
st.set_page_config(page_title="JR Aromas - Privado", page_icon="🌿", layout="wide")

# 2. SISTEMA DE LOGIN SIMPLE
def check_password():
    """Devuelve True si el usuario ingresó la contraseña correcta."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Pantalla de Login
    st.markdown('<h2 style="color: #2e7d32; text-align: center;">🔐 Acceso Restringido - JR Aromas</h2>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        password_input = st.text_input("JR2026", type="password")
        if st.button("Entrar"):
            # --- CAMBIÁ LA CONTRASEÑA ACÁ ---
            if password_input == "admin123": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    return False

# Si no pasa el login, se detiene acá y no muestra nada más
if not check_password():
    st.stop()

# --- SI LLEGA ACÁ, LA CONTRASEÑA ES CORRECTA Y MUESTRA LA APP ---
# 2. Estilo visual (CSS)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] {
        background-color: #ffffff; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #eee;
    }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .btn-venta > div > button { background-color: #d32f2f !important; color: white !important; }
    .btn-reporte > div > button { background-color: #1976d2 !important; color: white !important; }
    .alerta-stock {
        background-color: #ffebee; color: #c62828; padding: 10px;
        border-radius: 8px; border-left: 5px solid #c62828; margin-bottom: 10px; font-family: sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Encabezado con Logo
logo_path = "logo.PNG"
col_l, col_t = st.columns([1, 4])
with col_l:
    if os.path.exists(logo_path): st.image(logo_path, width=120)
with col_t:
    st.markdown('<h1 style="color: #2e7d32; margin-bottom: 0;">JR Aromas de Autor</h1>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 1.2rem; color: #666;">Gestión de Inventario y Reportes</p>', unsafe_allow_html=True)

# 4. Conexión y Funciones de Reporte
conn = st.connection("gsheets", type=GSheetsConnection)

def get_html_report(df, titulo):
    """Genera un string HTML con estilo moderno para el reporte."""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #333; }}
            h1 {{ color: #2e7d32; border-bottom: 2px solid #2e7d32; padding-bottom: 10px; }}
            .info {{ margin-bottom: 20px; color: #666; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background-color: #2e7d32; color: white; padding: 12px; text-align: left; }}
            td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .footer {{ margin-top: 30px; font-size: 0.8rem; text-align: center; color: #999; }}
        </style>
    </head>
    <body>
        <h1>{titulo}</h1>
        <p class="info">Generado el: {now} | JR Aromas de Autor</p>
        {df.to_html(index=False)}
        <div class="footer">Sistema de Gestión Interna - JR Aromas</div>
    </body>
    </html>
    """
    return html

def download_link(content, filename, text):
    """Crea un enlace de descarga para el archivo HTML."""
    b64 = base64.b64encode(content.encode('utf-8')).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}" style="text-decoration: none;"><button style="width:100%; background-color:#1976d2; color:white; border:none; padding:10px; border-radius:5px; cursor:pointer;">{text}</button></a>'

try:
    df_stock = conn.read(worksheet="Stock", ttl=0)
    df_ventas = conn.read(worksheet="Ventas", ttl=0)

    tabs = st.tabs(["📦 Stock", "🛒 Venta", "➕ Cargar", "📜 Historial", "📊 Reportes y Alertas"])

    with tabs[0]:
        st.write("### Inventario Actual")
        st.dataframe(df_stock, use_container_width=True, hide_index=True)

    with tabs[1]:
        st.write("### Registrar Venta")
        with st.form("v"):
            p = st.selectbox("Producto", df_stock['Producto'].tolist())
            c = st.number_input("Cantidad", min_value=1)
            if st.form_submit_button("Registrar Venta"):
                idx = df_stock[df_stock['Producto'] == p].index[0]
                if df_stock.at[idx, 'Cantidad'] >= c:
                    df_stock.at[idx, 'Cantidad'] -= c
                    conn.update(worksheet="Stock", data=df_stock)
                    nv = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Producto": p, "Cantidad": c, "Precio_Unitario": df_stock.at[idx, 'Precio'], "Total": c * df_stock.at[idx, 'Precio']}])
                    conn.update(worksheet="Ventas", data=pd.concat([df_ventas.dropna(how='all', axis=1), nv], ignore_index=True))
                    st.success("Venta realizada"); st.rerun()

    with tabs[2]:
        st.write("### Alta de Producto")
        with st.form("n"):
            n = st.text_input("Nombre"); cat = st.selectbox("Cat", ["Textil", "Difusor", "Auto", "Otros"])
            q = st.number_input("Stock", min_value=1); pr = st.number_input("Precio", min_value=0.0)
            if st.form_submit_button("Guardar"):
                nf = pd.DataFrame([{"ID": len(df_stock)+1, "Producto": n, "Categoría": cat, "Cantidad": q, "Precio": pr}])
                conn.update(worksheet="Stock", data=pd.concat([df_stock, nf], ignore_index=True))
                st.success("Guardado"); st.rerun()

    with tabs[3]:
        st.write("### Historial de Ventas")
        st.dataframe(df_ventas.sort_index(ascending=False), use_container_width=True, hide_index=True)

    # --- PESTAÑA DE REPORTES Y ALERTAS FILTRADA ---
    with tabs[4]:
        st.write("### ⚠️ Alertas de Reposición")
        bajo_stock = df_stock[df_stock['Cantidad'] < 5]
        if not bajo_stock.empty:
            for _, row in bajo_stock.iterrows():
                st.markdown(f'<div class="alerta-stock">🚨 <b>{row["Producto"]}</b> tiene solo {int(row["Cantidad"])} unidades.</div>', unsafe_allow_html=True)
        else:
            st.success("✅ Todo el stock está en niveles óptimos.")

        st.divider()
        st.write("### 📥 Descargar Reportes")
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("Reporte de Stock a la Fecha")
            # --- FILTRO DE COLUMNAS SOLICITADO ---
            columnas_reporte = ["ID", "Producto", "Categoría", "Cantidad"]
            # Verificamos que las columnas existan para evitar errores
            columnas_validas = [col for col in columnas_reporte if col in df_stock.columns]
            df_reporte_stock = df_stock[columnas_validas]
            
            reporte_s = get_html_report(df_reporte_stock, "Reporte de Inventario Físico")
            st.markdown(download_link(reporte_s, f"stock_{datetime.now().strftime('%d_%m_%Y')}.html", "Descargar Reporte Stock"), unsafe_allow_html=True)
            
        with col2:
            st.info("Reporte de Ventas")
            reporte_v = get_html_report(df_ventas, "Historial de Ventas")
            st.markdown(download_link(reporte_v, f"ventas_{datetime.now().strftime('%d_%m_%Y')}.html", "Descargar Reporte Ventas"), unsafe_allow_html=True)

except Exception as e:
    st.error("Error técnico"); st.write(e)
