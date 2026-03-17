import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os
import base64

# 1. Configuración de la página
st.set_page_config(page_title="Gestión JR Aromas", page_icon="🌿", layout="wide")

# 2. SISTEMA DE SEGURIDAD (Login)
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.markdown('<h2 style="color: #2e7d32; text-align: center;">🔐 Acceso JR Aromas</h2>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        password_input = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if password_input == "JR2026": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")
    return False

if not check_password():
    st.stop()

# 3. Estilo visual (CSS)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="stMetric"] { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #eee; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .btn-venta > div > button { background-color: #d32f2f !important; color: white !important; }
    .btn-consumo > div > button { background-color: #f57c00 !important; color: white !important; }
    .alerta-stock { background-color: #ffebee; color: #c62828; padding: 10px; border-radius: 8px; border-left: 5px solid #c62828; margin-bottom: 5px; font-family: sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 4. Encabezado con Logo
logo_path = "logo.PNG"
col_l, col_t = st.columns([1, 4])
with col_l:
    if os.path.exists(logo_path): 
        st.image(logo_path, width=120)
    else:
        st.warning("⚠️ No se encontró logo.PNG")
with col_t:
    st.markdown('<h1 style="color: #2e7d32; margin-bottom: 0;">JR Aromas de Autor</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666;">Panel de Gestión Integral - Pehuajó</p>', unsafe_allow_html=True)

# 5. Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

def get_html_report(df, titulo):
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    html = f"<html><head><meta charset='UTF-8'><style>body {{ font-family: sans-serif; margin: 40px; }} h1 {{ color: #2e7d32; }} table {{ width: 100%; border-collapse: collapse; }} th {{ background: #2e7d32; color: white; padding: 10px; }} td {{ padding: 8px; border-bottom: 1px solid #ddd; }}</style></head><body><h1>{titulo}</h1><p>Generado: {now}</p>{df.to_html(index=False)}</body></html>"
    return html

def download_link(content, filename, text):
    b64 = base64.b64encode(content.encode('utf-8')).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}" style="text-decoration: none;"><button style="width:100%; background-color:#1976d2; color:white; border:none; padding:10px; border-radius:5px; cursor:pointer;">{text}</button></a>'

try:
    df_stock = conn.read(worksheet="Stock", ttl=0)
    df_ventas = conn.read(worksheet="Ventas", ttl=0)
    df_consumibles = conn.read(worksheet="Consumibles", ttl=0)

    # Limpieza de nombres de columnas para evitar el KeyError
    df_stock.columns = df_stock.columns.str.strip()
    df_consumibles.columns = df_consumibles.columns.str.strip()

    tabs = st.tabs(["📦 Stock Venta", "🧪 Consumibles", "🛒 Nueva Venta", "➕ Cargar/Reponer", "📊 Reportes"])

    with tabs[0]:
        st.write("### Inventario de Productos")
        st.dataframe(df_stock, use_container_width=True, hide_index=True)

    with tabs[1]:
        st.write("### Insumos y Materia Prima")
        st.dataframe(df_consumibles, use_container_width=True, hide_index=True)
        st.divider()
        st.write("#### 📉 Registrar Uso")
        with st.form("uso_insumo"):
            insumo_sel = st.selectbox("Insumo", df_consumibles['Item'].tolist())
            cant_uso = st.number_input("Cantidad utilizada", min_value=0.01, step=0.01)
            if st.form_submit_button("Descontar"):
                idx_c = df_consumibles[df_consumibles['Item'] == insumo_sel].index[0]
                if df_consumibles.at[idx_c, 'Cantidad'] >= cant_uso:
                    df_consumibles.at[idx_c, 'Cantidad'] -= cant_uso
                    conn.update(worksheet="Consumibles", data=df_consumibles)
                    st.success("Actualizado"); st.rerun()
                else: st.error("Sin stock suficiente")

    with tabs[2]:
        with st.form("venta"):
            p = st.selectbox("Producto", df_stock['Producto'].tolist())
            c = st.number_input("Cantidad", min_value=1)
            if st.form_submit_button("Registrar Venta"):
                idx = df_stock[df_stock['Producto'] == p].index[0]
                if df_stock.at[idx, 'Cantidad'] >= c:
                    df_stock.at[idx, 'Cantidad'] -= c
                    conn.update(worksheet="Stock", data=df_stock)
                    nv = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Producto": p, "Cantidad": c, "Precio_Unitario": df_stock.at[idx, 'Precio'], "Total": c * df_stock.at[idx, 'Precio']}])
                    conn.update(worksheet="Ventas", data=pd.concat([df_ventas.dropna(how='all', axis=1), nv], ignore_index=True))
                    st.success("Venta guardada"); st.rerun()
                else: st.error("Sin stock")

    with tabs[3]:
        tipo = st.radio("Tipo", ["Producto Final", "Consumible"], horizontal=True)
        with st.form("carga"):
            if tipo == "Producto Final":
                n = st.text_input("Nombre Aroma"); cat = st.text_input("Categoría")
                q = st.number_input("Cantidad", min_value=1); pr = st.number_input("Precio", min_value=0.0)
                if st.form_submit_button("Guardar"):
                    nf = pd.DataFrame([{"ID": len(df_stock)+1, "Producto": n, "Categoría": cat, "Cantidad": q, "Precio": pr}])
                    conn.update(worksheet="Stock", data=pd.concat([df_stock, nf], ignore_index=True))
                    st.success("Guardado"); st.rerun()
            else:
                n_i = st.text_input("Nombre Insumo"); cat_i = st.text_input("Categoría (ej: Esencia)")
                q_i = st.number_input("Cantidad", min_value=0.01); uni = st.text_input("Unidad")
                if st.form_submit_button("Guardar Insumo"):
                    nf_i = pd.DataFrame([{"ID": len(df_consumibles)+1, "Item": n_i, "Categoría": cat_i, "Cantidad": q_i, "Unidad": uni}])
                    conn.update(worksheet="Consumibles", data=pd.concat([df_consumibles, nf_i], ignore_index=True))
                    st.success("Insumo Cargado"); st.rerun()

    with tabs[4]:
        st.write("### ⚠️ Alertas de Reposición")
        # Alertas Productos
        for _, r in df_stock[df_stock['Cantidad'] < 5].iterrows():
            st.markdown(f'<div class="alerta-stock">📦 PRODUCTO: <b>{r["Producto"]}</b> ({int(r["Cantidad"])} un)</div>', unsafe_allow_html=True)
            
        # Alertas Consumibles con búsqueda flexible de la columna Categoría
        col_cat = [c for c in df_consumibles.columns if 'categor' in c.lower()][0]
        for _, r in df_consumibles.iterrows():
            es_esencia = "esencia" in str(r[col_cat]).lower()
            limite = 0.3 if es_esencia else 5
            if r["Cantidad"] < limite:
                emoji = "🧪" if es_esencia else "🛠️"
                st.markdown(f'<div class="alerta-stock">{emoji} CONSUMIBLE: <b>{r["Item"]}</b> ({r["Cantidad"]} {r["Unidad"]})</div>', unsafe_allow_html=True)

        st.divider()
        st.write("### 📥 Reportes")
        col1, col2 = st.columns(2)
        with col1:
            df_rep = df_stock[["ID", "Producto", "Categoría", "Cantidad"]] if "Categoría" in df_stock.columns else df_stock
            st.markdown(download_link(get_html_report(df_rep, "Stock"), "stock.html", "Bajar Stock"), unsafe_allow_html=True)
        with col2:
            st.markdown(download_link(get_html_report(df_ventas, "Ventas"), "ventas.html", "Bajar Ventas"), unsafe_allow_html=True)

except Exception as e:
    st.error(f"Error técnico: {e}")
