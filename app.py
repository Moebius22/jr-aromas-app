¡Excelente idea! Para que la app sea realmente útil, vamos a agregar una cuarta pestaña llamada "🛒 Registrar Venta".

En esta sección, tu viejo podrá seleccionar el aroma de una lista desplegable, poner cuántos vendió, y la app se encargará de restar esa cantidad del Google Sheets automáticamente.

Aquí tenés el código completo de app.py. Solo tenés que borrar todo lo que tenés en GitHub y pegar esto:

app.py (Versión con Botón de Venta)
Python
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

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
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
    .btn-venta > div > button {
        background-color: #d32f2f !important;
        color: white !important;
    }
    .btn-guardar > div > button {
        background-color: #2e7d32 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 JR Aromas de Autor")
st.subheader("Sistema de Gestión de Inventario y Ventas")

# 3. Conexión a los datos
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    return conn.read(worksheet="Stock", ttl=0)

try:
    df = load_data()
    
    # 4. Pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["📦 Stock Actual", "🛒 Registrar Venta", "➕ Cargar Producto", "📊 Resumen"])

    with tab1:
        st.write("### Inventario en tiempo real")
        busqueda = st.text_input("🔍 Filtro rápido (nombre o categoría)...", placeholder="Ej: Vainilla")
        
        if busqueda:
            mask = df.astype(str).apply(lambda x: x.str.contains(busqueda, case=False)).any(axis=1)
            df_display = df[mask]
        else:
            df_display = df

        st.dataframe(
            df_display, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Cantidad": st.column_config.NumberColumn("Stock", format="%d u."),
                "Precio": st.column_config.NumberColumn("Precio Unit.", format="$ %.2f"),
            }
        )

    with tab2:
        st.write("### Nueva Venta")
        st.info("Seleccioná el producto para descontar del stock.")
        
        with st.form("formulario_venta"):
            # Creamos una lista de nombres para el buscador
            opciones_productos = df['Producto'].tolist()
            producto_vendido = st.selectbox("Seleccionar Aroma/Producto", opciones_productos)
            cantidad_vendida = st.number_input("Cantidad vendida", min_value=1, value=1, step=1)
            
            st.markdown('<div class="btn-venta">', unsafe_allow_html=True)
            boton_venta = st.form_submit_button("📉 Registrar Salida (Venta)")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if boton_venta:
                # Buscamos el producto en el dataframe
                idx = df[df['Producto'] == producto_vendido].index[0]
                stock_actual = df.at[idx, 'Cantidad']
                
                if stock_actual >= cantidad_vendida:
                    # Restamos el stock
                    df.at[idx, 'Cantidad'] = stock_actual - cantidad_vendida
                    
                    # Subimos los cambios a Google Sheets
                    conn.update(worksheet="Stock", data=df)
                    st.success(f"✅ Venta registrada: {cantidad_vendida} unidad(es) de {producto_vendido}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ No hay stock suficiente. Stock actual: {stock_actual}")

    with tab3:
        st.write("### Agregar Nuevo Producto")
        with st.form("nuevo_registro"):
            c1, c2 = st.columns(2)
            with c1:
                p_nombre = st.text_input("Nombre del Aroma")
                p_cat = st.selectbox("Categoría", ["Textil", "Difusor", "Auto", "Esencia", "Otros"])
            with c2:
                p_frag = st.text_input("Notas Olfativas")
                p_cant = st.number_input("Stock inicial", min_value=1, value=1)
                p_precio = st.number_input("Precio de venta", min_value=0.0, value=0.0)
            
            st.markdown('<div class="btn-guardar">', unsafe_allow_html=True)
            boton_guardar = st.form_submit_button("💾 Guardar Nuevo")
            st.markdown('</div>', unsafe_allow_html=True)
            
            if boton_guardar:
                if p_nombre:
                    nueva_fila = pd.DataFrame([{
                        "ID": len(df) + 1,
                        "Producto": p_nombre, "Categoría": p_cat,
                        "Fragancia": p_frag, "Cantidad": p_cant, "Precio": p_precio
                    }])
                    df_final = pd.concat([df, nueva_fila], ignore_index=True)
                    conn.update(worksheet="Stock", data=df_final)
                    st.success("¡Producto guardado!")
                    st.rerun()

    with tab4:
        st.write("### Estadísticas")
        col_m1, col_m2, col_m3 = st.columns(3)
        total_unidades = int(df['Cantidad'].sum())
        valor_inventario = (df['Cantidad'] * df['Precio']).sum()
        productos_bajos = df[df['Cantidad'] < 5].shape[0]
        
        col_m1.metric("Unidades Totales", f"{total_unidades}")
        col_m2.metric("Valor del Stock", f"$ {valor_inventario:,.2f}")
        col_m3.metric("Bajo Stock (<5)", f"{productos_bajos}")

except Exception as e:
    st.error("Error de conexión.")
    st.write(e)
