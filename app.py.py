import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Configuración institucional
st.set_page_config(page_title="Tracker 5000 Balas", page_icon="📊", layout="wide")

st.title("📊 Proyecto 5000 Balas | Centro de Operaciones")
st.markdown("---")

tab1, tab2 = st.tabs(["📈 Dashboard Analítico", "⚙️ Inyección Histórica"])

with tab1:
    st.header("Rendimiento del Bankroll")
    st.info("Dashboard pendiente de sincronización de lectura en la próxima fase.")

with tab2:
    st.header("Módulo de Migración de Track Record")
    st.write("Sube el archivo de contabilidad actual para inyectarlo en tu base de datos central.")
    
    archivo_subido = st.file_uploader("Arrastra aquí tu Excel histórico", type=["xlsx"])
    
    if archivo_subido is not None:
        # 1. Lectura del dataset
        df_registro = pd.read_excel(archivo_subido, sheet_name='Registro', skiprows=3)
        df_registro = df_registro.dropna(subset=['Fecha'])
        
        # 2. Motor de categorización de mercados
        def infer_deporte(row):
            texto = str(row['Mercado']).lower() + " " + str(row['Selección']).lower() + " " + str(row['Evento']).lower()
            if any(word in texto for word in ['corner', 'córner', 'goles', 'tarjeta', 'empate', '1x2', 'dnb']):
                return 'Fútbol'
            elif any(word in texto for word in ['juego', 'set', 'tie break', 'atp', 'wta']):
                return 'Tenis'
            elif any(word in texto for word in ['cuarto', 'rebotes', 'asistencias', 'puntos', 'nba']):
                return 'Baloncesto'
            elif 'esports' in texto or 'cs:go' in texto or 'lol' in texto:
                return 'eSports'
            else:
                return 'Fútbol'
                
        df_registro['Deporte_Inferred'] = df_registro.apply(infer_deporte, axis=1)
        
        # 3. Transformación matemática y estructuración
        df_new = pd.DataFrame()
        df_new['Fecha_Hora'] = pd.to_datetime(df_registro['Fecha']).dt.strftime('%Y-%m-%d %H:%M:%S')
        df_new['Deporte'] = df_registro['Deporte_Inferred']
        df_new['Evento'] = df_registro['Evento']
        df_new['Mercado_Pick'] = df_registro['Mercado'].astype(str) + " - " + df_registro['Selección'].astype(str)
        df_new['Cuota_Cerrada'] = df_registro['Cuota']
        df_new['Stake_Teorico'] = ""  
        df_new['Inversion_Euros'] = df_registro['Stake (€)']
        df_new['Broker_Definitivo'] = df_registro['Casa']
        df_new['EV_Porcentaje'] = ((df_registro['EV+ por apuesta (€)'] / df_registro['Stake (€)']) * 100).round(2)
        df_new['Estado_Resolucion'] = df_registro['Resultado']
        df_new['Beneficio_Neto'] = df_registro['Beneficio (€)']
        
        # Limpieza de valores nulos para la API de Google
        df_new = df_new.fillna("")
        
        st.success(f"¡Matriz procesada! Total de operaciones de valor encontradas: {len(df_new)}")
        st.dataframe(df_new.head(10))
        
        # 4. Motor de volcado a la nube
        if st.button("Inyectar en Google Sheets"):
            with st.spinner("Estableciendo conexión encriptada con Google Cloud..."):
                try:
                    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
                    creds = ServiceAccountCredentials.from_json_keyfile_name('credenciales.json', scope)
                    client = gspread.authorize(creds)
                    
                    # Asegúrate de que el nombre coincide EXACTAMENTE con el de tu documento
                    sheet = client.open('Base de Datos - Proyecto 5000 Balas').sheet1
                    
                    datos_volcado = df_new.values.tolist()
                    sheet.append_rows(datos_volcado)
                    
                    st.success("✅ ¡Volcado completado con éxito! El track record está asegurado en la nube.")
                except Exception as e:
                    st.error(f"Error de protocolo en la conexión: {e}")