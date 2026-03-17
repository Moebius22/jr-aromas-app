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

# 2. Estilo visual
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
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 JR Aromas de Autor")

# 3. Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    return conn.read(worksheet=sheet_name, ttl=0)

try:
    df_stock = load_data("Stock")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Stock Actual", "🛒 Nueva Venta", "📜 Historial de Ventas", "📊 Resumen"])

    with tab1:
        st.write("### Inventario")
        st.dataframe(df_stock, use_container_width=True, hide_index=True)

    with tab2:
        st.write("### Registrar Venta")
        with st.form("form_venta"):
            producto_sel = st.selectbox("Producto", df_stock['Producto'].tolist())
            cant_vender = st.number_input("Cantidad", min_value=1, value=1)
            
            st.markdown('<div class="btn-venta">', unsafe_allow_html=True)
            submit_venta = st.form_submit_button("Registrar y Descontar")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if submit_venta:
                idx = df_stock[df_stock['Producto'] == producto_sel].index[0]
                stock_actual = df_stock.at[idx, 'Cantidad']
                precio_unit = df_stock.at[idx, 'Precio']
                
                if stock_actual >= cant_vender:
                    # 1. Actualizar Stock
                    df_stock.at[idx, 'Cantidad'] = stock_actual - cant_vender
                    conn.update(worksheet="Stock", data=df_stock)
                    
                    # 2. Registrar en hoja Ventas
                    df_ventas = load_data("Ventas")
                    nueva_venta = pd.DataFrame([{
                        "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Producto": producto_sel,
                        "Cantidad": cant_vender,
                        "Precio_Unitario": precio_unit,
                        "Total": cant_vender * precio_unit
                    }])
                    
                    # Limpiamos posibles columnas vacías antes de unir
                    df_ventas = df_ventas.dropna(how='all', axis=1)
                    df_ventas_final = pd.concat([df_ventas, nueva_venta], ignore_index=True)
                    conn.update(worksheet="Ventas", data=df_ventas_final)
                    
                    st.success("Venta guardada y stock actualizado")
                    st.rerun()
                else:
                    st.error("No hay suficiente stock")

    with tab3:
        st.write("### Registro de Ventas Realizadas")
        df_historial = load_data("Ventas")
        st.dataframe(df_historial, use_container_width=True, hide_index=True)

    with tab4:
        st.write("### Balance")
        col1, col2 = st.columns(2)
        df_historial = load_data("Ventas")
        
        total_recaudado = df_historial['Total'].sum() if not df_historial.empty else 0
        cant_total_ventas = df_historial['Cantidad'].sum() if not df_historial.empty else 0
        
        col1.metric("Ventas Totales (Unidades)", f"{int(cant_total_ventas)} un.")
        col2.metric("Recaudación Total", f"$ {total_recaudado:,.2f}")

except Exception as e:
    st.error("Error técnico. Revisá que existan las hojas 'Stock' y 'Ventas' en tu Excel.")
    st.write(e)
