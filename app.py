import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuración de la página
st.set_page_config(page_title="JR Aromas de Autor - Gestión", layout="wide")

st.title("🌿 JR Aromas de Autor")
st.subheader("Panel de Control de Inventario")

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Lectura de datos
df = conn.read(worksheet="Stock", ttl="0")

# --- INTERFAZ PRINCIPAL ---
tab1, tab2, tab3 = st.tabs(["📦 Inventario Actual", "➕ Cargar Stock", "📊 Reportes"])

with tab1:
    st.write("### Stock disponible en local")
    # Mostramos el inventario con un buscador
    busqueda = st.text_input("Buscar aroma o producto...")
    
    if busqueda:
        df_filtrado = df[df['Producto'].str.contains(busqueda, case=False)]
        st.dataframe(df_filtrado, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

with tab2:
    st.write("### Registrar Entrada de Mercadería")
    with st.form("nuevo_producto"):
        nombre = st.text_input("Nombre del Aroma/Producto")
        cat = st.selectbox("Categoría", ["Textil", "Difusor", "Auto", "Esencia"])
        cant = st.number_input("Cantidad que ingresa", min_value=1, step=1)
        precio = st.number_input("Precio de venta", min_value=0.0)
        
        btn_guardar = st.form_submit_state("Guardar en Inventario")
        
        if btn_guardar:
            st.info("Aquí programaremos la lógica para actualizar el Excel automáticamente.")

with tab3:
    st.write("### Estado del Negocio")
    col1, col2 = st.columns(2)
    total_productos = len(df)
    stock_bajo = df[df['Cantidad'] < 5].shape[0]
    
    col1.metric("Variedades de Aromas", total_productos)
    col2.metric("Alertas de Stock Bajo", stock_bajo, delta_color="inverse")
