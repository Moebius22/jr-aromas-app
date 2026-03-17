import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import os

# 1. Configuración de la página (¡Debe ser la primera instrucción de Streamlit!)
st.set_page_config(
    page_title="JR Aromas de Autor - Gestión",
    page_icon="🌿", # Podés cambiar esto por la URL del logo si querés que aparezca en la pestaña del navegador
    layout="wide"
)

# 2. Estilo visual (CSS) - Incluye ajustes para el logo y títulos
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* Contenedor del Logo y Título */
    .header-container {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }
    .brand-title {
        font-size: 3rem;
        margin-left: 20px;
        color: #2e7d32; /* Color verde para la marca */
        font-weight: bold;
    }
    .brand-subtitle {
        font-size: 1.5rem;
        color: #6c757d;
        margin-left: 20px;
        margin-top: -10px; /* Ajuste para acercar al título */
    }

    /* Estilos para Métricas y Botones */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; }
    .btn-venta > div > button { background-color: #d32f2f !important; color: white !important; }
    .btn-guardar > div > button { background-color: #2e7d32 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Sección de Encabezado con Logo y Título
# Intentamos cargar el logo.png desde la raíz del repositorio
logo_path = "logo.png"

# Creamos columnas para el logo y el texto del título
col_logo, col_titulo = st.columns([1, 4]) # Ajustá los pesos [1, 4] según el tamaño de tu logo

with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, width=150) # Ajustá el 'width' para que se vea bien
    else:
        # Si no encuentra el logo, muestra un marcador de posición o texto
        st.warning("⚠️ logo.png no encontrado en la raíz del repositorio.")
        st.subheader("JR Aromas") # Fallback si no hay logo

with col_titulo:
    # Usamos HTML personalizado para mayor control del estilo del título
    st.markdown('<div class="brand-title">JR Aromas de Autor</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-subtitle">Sistema de Gestión Integrado</div>', unsafe_allow_html=True)

st.markdown("---") # Línea divisoria

# 4. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    return conn.read(worksheet=sheet_name, ttl=0)

try:
    # Cargamos los datos
    df_stock = load_data("Stock")
    df_ventas = load_data("Ventas")
    
    # 5. Pestañas de la App
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📦 Stock Actual", 
        "🛒 Nueva Venta", 
        "➕ Cargar Producto Nuevo", 
        "📜 Historial de Ventas", 
        "📊 Resumen"
    ])

    # --- PESTAÑA 1: VER STOCK ---
    with tab1:
        st.write("### Inventario en tiempo real")
        busqueda = st.text_input("🔍 Buscar aroma o categoría...", placeholder="Ej: Textil, Vainilla")
        if busqueda:
            mask = df_stock.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
            df_display = df_stock[mask]
        else:
            df_display = df_stock
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- PESTAÑA 2: REGISTRAR VENTA ---
    with tab2:
        st.write("### Registrar Venta y Descontar Stock")
        with st.form("form_venta"):
            producto_sel = st.selectbox("Elegí el producto vendido", df_stock['Producto'].tolist())
            cant_vender = st.number_input("Cantidad", min_value=1, value=1)
            
            st.markdown('<div class="btn-venta">', unsafe_allow_html=True)
            submit_venta = st.form_submit_button("📉 Confirmar Venta")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if submit_venta:
                idx = df_stock[df_stock['Producto'] == producto_sel].index[0]
                stock_actual = df_stock.at[idx, 'Cantidad']
                precio_unit = df_stock.at[idx, 'Precio']
                
                if stock_actual >= cant_vender:
                    # A. Restar del Stock
                    df_stock.at[idx, 'Cantidad'] = stock_actual - cant_vender
                    conn.update(worksheet="Stock", data=df_stock)
                    
                    # B. Anotar en Historial de Ventas
                    nueva_venta = pd.DataFrame([{
                        "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Producto": producto_sel,
                        "Cantidad": cant_vender,
                        "Precio_Unitario": precio_unit,
                        "Total": cant_vender * precio_unit
                    }])
                    df_ventas_final = pd.concat([df_ventas.dropna(how='all', axis=1), nueva_venta], ignore_index=True)
                    conn.update(worksheet="Ventas", data=df_ventas_final)
                    
                    st.success(f"Venta de {producto_sel} ({cant_vender} un.) registrada.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"Stock insuficiente. Solo quedan {stock_actual} unidades.")

    # --- PESTAÑA 3: CARGAR PRODUCTO NUEVO ---
    with tab3:
        st.write("### Alta de Mercadería")
        with st.form("form_nuevo_prod"):
            c1, c2 = st.columns(2)
            with c1:
                nuevo_n = st.text_input("Nombre del Aroma/Producto")
                nuevo_c = st.selectbox("Categoría", ["Textil", "Difusor", "Auto", "Esencia", "Otros"])
            with c2:
                nuevo_f = st.text_input("Notas Olfativas")
                nuevo_q = st.number_input("Cantidad inicial", min_value=1, value=1)
                nuevo_p = st.number_input("Precio de venta", min_value=0.0, value=0.0)
            
            st.markdown('<div class="btn-guardar">', unsafe_allow_html=True)
            submit_nuevo = st.form_submit_button("💾 Guardar en Stock")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if submit_nuevo:
                if nuevo_n:
                    nueva_fila = pd.DataFrame([{
                        "ID": len(df_stock) + 1,
                        "Producto": nuevo_n,
                        "Categoría": nuevo_c,
                        "Fragancia": nuevo_f,
                        "Cantidad": nuevo_q,
                        "Precio": nuevo_p
                    }])
                    df_stock_final = pd.concat([df_stock, nueva_fila], ignore_index=True)
                    conn.update(worksheet="Stock", data=df_stock_final)
                    st.success(f"'{nuevo_n}' agregado al inventario.")
                    st.rerun()
                else:
                    st.warning("El nombre del producto es obligatorio.")

    # --- PESTAÑA 4: HISTORIAL ---
    with tab4:
        st.write("### Histórico de Ventas Realizadas")
        # Mostramos las ventas más recientes primero
        st.dataframe(df_ventas.sort_index(ascending=False), use_container_width=True, hide_index=True)

    # --- PESTAÑA 5: RESUMEN ---
    with tab5:
        st.write("### Balance General")
        c_m1, c_m2, c_m3 = st.columns(3)
        
        recaudado = df_ventas['Total'].sum() if not df_ventas.empty else 0
        vendidas = df_ventas['Cantidad'].sum() if not df_ventas.empty else 0
        stock_total = df_stock['Cantidad'].sum()
        
        c_m1.metric("Unidades Vendidas", f"{int(vendidas)}")
        c_m2.metric("Recaudación Total", f"$ {recaudado:,.2f}")
        c_m3.metric("Stock Restante (Unidades)", f"{int(stock_total)}")

except Exception as e:
    st.error("⚠️ Error de conexión o configuración.")
    st.info("Asegurate de que las pestañas en el Excel se llamen exactamente 'Stock' y 'Ventas' y que el robot tenga permisos de Editor.")
    st.write("Detalle técnico:", e)
