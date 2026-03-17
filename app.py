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
        background-color: #2e7d32;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌿 JR Aromas de Autor")
st.subheader("Panel de Control de Inventario")

# 3. Conexión a los datos
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # ttl=0 para que siempre traiga datos frescos de la planilla
    return conn.read(worksheet="Stock", ttl=0)

try:
    df = load_data()
    
    # 4. Pestañas principales
    tab1, tab2, tab3 = st.tabs(["📦 Ver Stock", "➕ Cargar Producto", "📊 Resumen"])

    with tab1:
        st.write("### Inventario Actual")
        busqueda = st.text_input("🔍 Buscar aroma o producto...", placeholder="Ej: Vainilla, Textil...")
        
        if busqueda:
            # Buscamos en todas las columnas para que sea fácil encontrarlo
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
        st.write("### Agregar Nueva Mercadería")
        st.info("Completá los campos para sumar stock a la planilla de Google.")
        
        with st.form("nuevo_registro"):
            c1, c2 = st.columns(2)
            with c1:
                p_nombre = st.text_input("Nombre del Aroma / Producto")
                p_cat = st.selectbox("Categoría", ["Textil", "Difusor", "Auto", "Esencia", "Jabón", "Otros"])
            with c2:
                p_frag = st.text_input("Notas (Ej: Dulce, Amaderado)")
                p_cant = st.number_input("Cantidad inicial", min_value=1, value=1)
                p_precio = st.number_input("Precio de venta", min_value=0.0, value=0.0)
            
            boton_guardar = st.form_submit_button("💾 Guardar en Inventario")
            
            if boton_guardar:
                if p_nombre:
                    # Creamos el nuevo registro
                    nueva_fila = pd.DataFrame([{
                        "ID": len(df) + 1,
                        "Producto": p_nombre,
                        "Categoría": p_cat,
                        "Fragancia": p_frag,
                        "Cantidad": p_cant,
                        "Precio": p_precio
                    }])
                    
                    # Combinamos y subimos
                    df_final = pd.concat([df, nueva_fila], ignore_index=True)
                    conn.update(worksheet="Stock", data=df_final)
                    
                    st.success(f"✅ ¡{p_nombre} agregado con éxito!")
                    st.balloons()
                    st.rerun()
                else:
                    st.warning("El nombre del producto es obligatorio.")

    with tab3:
        st.write("### Estadísticas Rápidas")
        col_m1, col_m2, col_m3 = st.columns(3)
        
        # Cálculos de stock
        total_unidades = int(df['Cantidad'].sum())
        valor_inventario = (df['Cantidad'] * df['Precio']).sum()
        productos_bajos = df[df['Cantidad'] < 5].shape[0]
        
        col_m1.metric("Unidades en Stock", f"{total_unidades} un.")
        col_m2.metric("Valor Total Stock", f"$ {valor_inventario:,.2f}")
        col_m3.metric("Aromas a Reponer", f"{productos_bajos}", delta="Bajo Stock", delta_color="inverse")

except Exception as e:
    st.error("Hubo un problema al cargar los datos.")
    st.write(e)
