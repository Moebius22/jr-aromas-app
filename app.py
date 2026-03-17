import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración visual
st.set_page_config(page_title="JR Aromas de Autor - Gestión", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 JR Aromas de Autor")
st.subheader("Sistema de Gestión de Inventario")

# Conexión
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Intentamos leer la hoja "Stock"
    df = conn.read(worksheet="Stock", ttl="0")
    
    # Interfaz de pestañas
    tab1, tab2, tab3 = st.tabs(["📦 Stock Actual", "➕ Carga de Mercadería", "📈 Resumen"])

    with tab1:
        st.write("### Listado de Fragancias")
        busqueda = st.text_input("🔍 Buscar aroma...", placeholder="Ej: Vainilla")
        if busqueda:
            df_display = df[df['Producto'].astype(str).str.contains(busqueda, case=False)]
        else:
            df_display = df
        st.dataframe(df_display, use_container_width=True, hide_index=True)

    with tab2:
        st.write("### Registrar Nuevo Ingreso")
        with st.form("formulario_stock"):
            col1, col2 = st.columns(2)
            with col1:
                nuevo_nombre = st.text_input("Nombre del Aroma")
                nueva_cat = st.selectbox("Categoría", ["Textil", "Difusor", "Auto", "Esencia", "Otros"])
            with col2:
                nueva_fragancia = st.text_input("Notas Olfativas")
                nueva_cant = st.number_input("Cantidad", min_value=1, value=1)
                nuevo_precio = st.number_input("Precio", min_value=0.0, value=0.0)
            
            if st.form_submit_button("Guardar"):
                if nuevo_nombre:
                    nueva_fila = pd.DataFrame([{"ID": len(df)+1, "Producto": nuevo_nombre, "Categoría": nueva_cat, "Fragancia": nueva_fragancia, "Cantidad": nueva_cant, "Precio": nuevo_precio}])
                    updated_df = pd.concat([df, nueva_fila], ignore_index=True)
                    conn.update(worksheet="Stock", data=updated_df)
                    st.success("Guardado!")
                    st.rerun()

    with tab3:
        m1, m2 = st.columns(2)
        m1.metric("Unidades Totales", int(df['Cantidad'].sum()))
        m2.metric("Valor Total", f"$ { (df['Cantidad'] * df['Precio']).sum() :,.2f}")

except Exception as e:
    st.error("⚠️ No se pudo conectar con la planilla.")
    st.info("Asegurate de que la pestaña de Google Sheets se llame exactamente 'Stock' y que el mail del robot sea Editor.")
    st.write("Detalle técnico del error:", e)
