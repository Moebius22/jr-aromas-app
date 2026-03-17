import pandas as pd
from datetime import datetime
import os
import base64

# 1. Configuración de la página
st.set_page_config(page_title="Gestión JR Aromas", page_icon="🌿", layout="wide")

# 2. SISTEMA DE SEGURIDAD
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
            if password_input == "admin123": # <--- CAMBIÁ TU CONTRASEÑA ACÁ
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Incorrecta")
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
    .alerta-stock { background-color: #ffebee; color: #c62828; padding: 10px; border-radius: 8px; border-left: 5px solid #c62828; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 4. Encabezado con Logo
logo_path = "logo.PNG"
col_l, col_t = st.columns([1, 4])
with col_l:
    if os.path.exists(logo_path): st.image(logo_path, width=120)
with col_t:
    st.markdown('<h1 style="color: #2e7d32; margin-bottom: 0;">JR Aromas de Autor</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666;">Panel de Gestión Integral</p>', unsafe_allow_html=True)

# 5. Conexión y Carga de Datos
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df_stock = conn.read(worksheet="Stock", ttl=0)
    df_ventas = conn.read(worksheet="Ventas", ttl=0)
    df_consumibles = conn.read(worksheet="Consumibles", ttl=0)

    tabs = st.tabs(["📦 Stock Venta", "🧪 Consumibles", "🛒 Nueva Venta", "➕ Cargar/Reponer", "📊 Reportes"])

    # --- PESTAÑA 1: STOCK PRODUCTOS ---
    with tabs[0]:
        st.write("### Inventario de Productos Terminados")
        st.dataframe(df_stock, use_container_width=True, hide_index=True)

    # --- PESTAÑA 2: CONSUMIBLES (NUEVA) ---
    with tabs[1]:
        st.write("### Insumos y Materia Prima")
        st.dataframe(df_consumibles, use_container_width=True, hide_index=True)
        
        st.divider()
        st.write("#### 📉 Registrar Uso de Consumible")
        with st.form("uso_insumo"):
            insumo_sel = st.selectbox("Seleccionar Insumo", df_consumibles['Item'].tolist())
            cant_uso = st.number_input("Cantidad utilizada", min_value=1)
            st.markdown('<div class="btn-consumo">', unsafe_allow_html=True)
            if st.form_submit_button("Descontar Insumo"):
                idx_c = df_consumibles[df_consumibles['Item'] == insumo_sel].index[0]
                if df_consumibles.at[idx_c, 'Cantidad'] >= cant_uso:
                    df_consumibles.at[idx_c, 'Cantidad'] -= cant_uso
                    conn.update(worksheet="Consumibles", data=df_consumibles)
                    st.success(f"Se descontaron {cant_uso} de {insumo_sel}"); st.rerun()
                else: st.error("No hay suficiente insumo")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- PESTAÑA 3: NUEVA VENTA ---
    with tabs[2]:
        with st.form("venta"):
            p = st.selectbox("Producto", df_stock['Producto'].tolist())
            c = st.number_input("Cantidad", min_value=1)
            st.markdown('<div class="btn-venta">', unsafe_allow_html=True)
            if st.form_submit_button("Registrar Venta"):
                idx = df_stock[df_stock['Producto'] == p].index[0]
                if df_stock.at[idx, 'Cantidad'] >= c:
                    df_stock.at[idx, 'Cantidad'] -= c
                    conn.update(worksheet="Stock", data=df_stock)
                    nv = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Producto": p, "Cantidad": c, "Precio_Unitario": df_stock.at[idx, 'Precio'], "Total": c * df_stock.at[idx, 'Precio']}])
                    conn.update(worksheet="Ventas", data=pd.concat([df_ventas.dropna(how='all', axis=1), nv], ignore_index=True))
                    st.success("Venta Guardada"); st.rerun()
                else: st.error("Sin stock")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- PESTAÑA 4: CARGAR/REPONER ---
    with tabs[3]:
        tipo_carga = st.radio("¿Qué vas a cargar?", ["Producto de Venta", "Consumible/Insumo"], horizontal=True)
        with st.form("carga"):
            if tipo_carga == "Producto de Venta":
                n = st.text_input("Nombre Aroma"); cat = st.text_input("Categoría")
                q = st.number_input("Cantidad", min_value=1); pr = st.number_input("Precio", min_value=0.0)
                if st.form_submit_button("Guardar Producto"):
                    nf = pd.DataFrame([{"ID": len(df_stock)+1, "Producto": n, "Categoría": cat, "Cantidad": q, "Precio": pr}])
                    conn.update(worksheet="Stock", data=pd.concat([df_stock, nf], ignore_index=True))
                    st.success("Producto Cargado"); st.rerun()
            else:
                n_i = st.text_input("Nombre del Insumo"); cat_i = st.text_input("Categoría Insumo")
                q_i = st.number_input("Cantidad", min_value=1); uni = st.text_input("Unidad (ej: Litros, Unidades)")
                if st.form_submit_button("Guardar Insumo"):
                    nf_i = pd.DataFrame([{"ID": len(df_consumibles)+1, "Item": n_i, "Categoría": cat_i, "Cantidad": q_i, "Unidad": uni}])
                    conn.update(worksheet="Consumibles", data=pd.concat([df_consumibles, nf_i], ignore_index=True))
                    st.success("Insumo Cargado"); st.rerun()

    # --- PESTAÑA 5: REPORTES Y ALERTAS ---
    with tabs[4]:
        st.write("### ⚠️ Alertas de Reposición (< 5 unidades)")
        bajo_p = df_stock[df_stock['Cantidad'] < 5]
        bajo_i = df_consumibles[df_consumibles['Cantidad'] < 5]
        
        for _, r in bajo_p.iterrows(): st.markdown(f'<div class="alerta-stock">📦 PRODUCTO: <b>{r["Producto"]}</b> ({int(r["Cantidad"])} un)</div>', unsafe_allow_html=True)
        for _, r in bajo_i.iterrows(): st.markdown(f'<div class="alerta-stock">🧪 INSUMO: <b>{r["Item"]}</b> ({int(r["Cantidad"])} {r["Unidad"]})</div>', unsafe_allow_html=True)

        st.divider()
        st.write("### 📈 Resumen Financiero")
        col1, col2 = st.columns(2)
        total_v = df_ventas['Total'].sum() if not df_ventas.empty else 0
        col1.metric("Ventas Totales", f"$ {total_v:,.2f}")
        col2.metric("Items en Stock", f"{int(df_stock['Cantidad'].sum())}")

except Exception as e:
    st.error("Error técnico: Asegurate de tener las hojas 'Stock', 'Ventas' y 'Consumibles' creadas."); st.write(e)
