import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(
    page_title="JR Aromas de Autor - Gestión",
    page_icon="🌿",
    layout="wide"
)

# 2. Estilo visual (CSS)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
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

st.title("🌿 JR Aromas de Autor")

# 3. Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    return conn.read(worksheet=sheet_name, ttl=0)

try:
    # Cargamos el stock inicial
    df_stock = load_data("Stock")
    
    # 4. Pestañas de la App
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
        busqueda = st.text_input("🔍 Buscar aroma...", placeholder="Ej: Coco")
        if busqueda:
            mask = df_stock.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
            df_display = df_stock[mask]
        else:
            df_display = df_stock
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    # --- PESTAÑA 2: REGISTRAR VENTA ---
    with tab2:
        st.write("### Registrar Salida por Venta")
        with st.form("form_venta"):
            producto_sel = st.selectbox("Elegí el producto vendido", df_stock['Producto'].tolist())
            cant_vender = st.number_input("Cantidad", min_value=1, value=1)
            
            st.markdown('<div class="btn-venta">', unsafe_allow_html=True)
            submit_venta = st.form_submit_button("📉 Confirmar Venta y Descontar")
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
                    df_ventas = load_data("Ventas")
                    nueva_venta = pd.DataFrame([{
                        "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Producto": producto_sel,
                        "Cantidad": cant_vender,
                        "Precio_Unitario": precio_unit,
                        "Total": cant_vender * precio_unit
                    }])
                    df_ventas_final = pd.concat([df_ventas.dropna(how='all', axis=1), nueva_venta], ignore_index=True)
                    conn.update(worksheet="Ventas", data=df_ventas_final)
                    
                    st.success(f"Venta de {producto_sel} registrada con éxito.")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"Stock insuficiente. Solo quedan {stock_actual} unidades.")

    # --- PESTAÑA 3: CARGAR PRODUCTO NUEVO ---
    with tab3:
        st.write("### Alta de Mercadería")
        st.info("Usá esto para agregar aromas que no están en la lista o reponer stock inicial.")
        with st.form("form_nuevo_prod"):
            c1, c2 = st.columns(2)
            with c1:
                nuevo_n = st.text_input("Nombre del Aroma")
                nuevo_c = st.selectbox("Categoría", ["Textil", "Difusor", "Auto", "Esencia", "Otros"])
            with c2:
                nuevo_f = st.text_input("Notas Olfativas")
                nuevo_q = st.number_input("Cantidad que ingresa", min_value=1, value=1)
                nuevo_p = st.number_input("Precio de venta sugerido", min_value=0.0, value=0.0)
            
            st.markdown('<div class="btn-guardar">', unsafe_allow_html=True)
            submit_nuevo = st.form_submit_button("💾 Guardar en Stock")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if submit_nuevo:
                if nuevo_n:
                    # Si el producto ya existe, podrías sumarlo, pero para no complicar creamos fila nueva
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
                    st.success(f"{nuevo_n} agregado al inventario.")
                    st.rerun()
                else:
                    st.warning("Poné un nombre al menos.")

    # --- PESTAÑA 4: HISTORIAL ---
    with tab4:
        st.write("### Registro Histórico de Ventas")
        df_hist = load_data("Ventas")
        st.dataframe(df_hist.sort_index(ascending=False), use_container_width=True, hide_index=True)

    # --- PESTAÑA 5: RESUMEN ---
    with tab5:
        st.write("### Balance del Negocio")
        df_hist_res = load_data("Ventas")
        c_m1, c_m2, c_m3 = st.columns(3)
        
        recaudado = df_hist_res['Total'].sum() if not df_hist_res.empty else 0
        vendidas = df_hist_res['Cantidad'].sum() if not df_hist_res.empty else 0
        stock_total = df_stock['Cantidad'].sum()
        
        c_m1.metric("Total Vendido", f"{int(vendidas)} un.")
        c_m2.metric("Plata en Caja (Ventas)", f"$ {recaudado:,.2f}")
        c_m3.metric("Stock Restante", f"{int(stock_total)} un.")

except Exception as e:
    st.error("Error al conectar. Chequeá que las pestañas en el Excel se llamen 'Stock' y 'Ventas'.")
    st.write(e)
