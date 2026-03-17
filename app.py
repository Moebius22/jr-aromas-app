import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.title("Prueba de Conexión JR Aromas")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Intentamos leer la hoja Stock
    df = conn.read(worksheet="Stock", ttl=0)
    st.success("¡Conexión exitosa!")
    st.write("Aquí están tus datos:")
    st.dataframe(df)
except Exception as e:
    st.error("Error de permisos o configuración")
    st.write("Detalle del error:", e)
    st.info("Asegurate de que la pestaña de Excel se llame exactamente: Stock")
