import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuración visual de la aplicación
st.set_page_config(
    page_title="JR Aromas de Autor - Gestión",
    page_icon="🌿",
    layout="wide"
)

# Estilo personalizado para que se vea "agradable"
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_stdio=True)

st.title("🌿 JR Aromas de Autor")
st.subheader("Sistema de Gestión de Inventario")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para leer datos actualizados
def load_data():
    return conn.read(worksheet="Stock", ttl="0")

try:
    df = load_data()
except Exception as e:
    st.error("Error de conexión. Revisá si compartiste la planilla con el mail del Service Account.")
    st.stop()

# --- INTERFAZ DE USUARIO (TABS) ---
tab1, tab2, tab3 = st.tabs(["📦 Stock Actual", "➕ Carga de Mercadería", "📈 Resumen"])

with tab1:
    st.write("### Listado de Fragancias")
    
    # Buscador dinámico
    busqueda = st.text_input("🔍 Buscar por nombre de aroma o categoría...", placeholder="Ej: Vainilla")
    
    if busqueda:
        df_display = df[df['Producto'].astype(str).str.contains(busqueda, case=False) | 
                        df['Categoría'].astype(str).str.contains(busqueda, case=False)]
    else:
        df_display = df

    # Mostrar la tabla con formato amigable
    st.dataframe(
        df_display, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Cantidad": st.column_config.NumberColumn("Stock", format="%d 📦"),
            "Precio": st.column_config.NumberColumn("Precio", format="$ %.2f"),
        }
    )

with tab2:
    st.write("### Registrar Nuevo Ingreso")
    st.info("Completá los datos para añadir productos a la planilla.")
    
    with st.form("formulario_stock"):
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            nuevo_nombre = st.text_input("Nombre del Aroma")
            nueva_cat = st.selectbox("Categoría", ["Textil", "Difusor", "Auto", "Esencia", "Otros"])
        
        with col_form2:
            nueva_fragancia = st.text_input("Notas Olfativas (Ej: Cítrico)")
            nueva_cant = st.number_input("Cantidad", min_value=1, step=1)
            nuevo_precio = st.number_input("Precio Unitario", min_value=0.0)
            
        submitted = st.form_submit_button("Registrar en Inventario")
        
        if submitted:
            if nuevo_nombre:
                # Aquí creamos la nueva fila
                nueva_fila = pd.DataFrame([{
                    "ID": len(df) + 1,
                    "Producto": nuevo_nombre,
                    "Categoría": nueva_cat,
                    "Fragancia": nueva_fragancia,
                    "Cantidad": nueva_cant,
                    "Precio": nuevo_precio
                }])
                
                # Unimos con el excel actual
                updated_df = pd.concat([df, nueva_fila], ignore_index=True)
                
                # Subimos a Google Sheets
                conn.update(worksheet="Stock", data=updated_df)
                st.success(f"✅ {nuevo_nombre} guardado correctamente!")
                st.balloons()
            else:
                st.warning("Por favor, ingresá al menos el nombre del producto.")

with tab3:
    st.write("### Estado del Inventario")
    
    m1, m2, m3 = st.columns(3)
    
    total_items = df['Cantidad'].sum()
    valor_total = (df['Cantidad'] * df['Precio']).sum()
    alerta_stock = df[df['Cantidad'] < 5].shape[0]
    
    m1.metric("Unidades Totales", f"{total_items} un.")
    m2.metric("Valor del Stock", f"$ {valor_total:,.2f}")
    m3.metric("Stock Crítico (<5)", f"{alerta_stock} aromas", delta="- Alerta", delta_color="inverse")
