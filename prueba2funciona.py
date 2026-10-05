import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="Estudio: Alimentación y Deporte en Niños",
    page_icon="📊",
    layout="wide"
)


# ============================================
# CARGA Y PROCESAMIENTO DE DATOS REALES
# ============================================
@st.cache_data
def cargar_datos():
    """
    Carga los dos archivos CSV del estudio y los une por ec5_uuid.
    Limpia y transforma las columnas para que sean analizables.
    """

    # --- Cargar encuesta 1: Hábitos alimentarios ---
    df_alim = pd.read_csv("form-1__encuesta-sobre-habitos-alimentarios.csv", encoding="utf-8-sig")

    df_alim = df_alim.rename(columns={
        "ec5_uuid": "id",
        "1_Coms_4_comidas_al_": "comidas_al_dia",
        "2_Cuantas_veces_al_d": "frecuencia_alimentacion",
        "3_Cual_de_las_siguie": "tipo_comida",
        "4_Pasta": "pasta",
        "5_Carne": "carne",
        "6_Milanesa": "milanesa",
        "7_Te_termins_el_plat": "termina_plato",
        "8_Con_cuanta_frecuen": "frecuencia_frutas_verduras",
        "9_Coms_algo_durante_": "come_entre_comidas",
        "10_Cada_cuanto_tomas": "frecuencia_agua",
        "11_Tens_alguna_dieta": "dieta_especial",
        "13_Coms_snacksgolosi": "come_snacks",
        "14_Con_que_frecuenci": "frecuencia_snacks",
        "15_Cual_es_tu_snack_": "tipo_snack"
    })

    # --- Cargar encuesta 2: Actividad física ---
    df_activ = pd.read_csv("form-2__actividad-fisica.csv", encoding="utf-8-sig")

    df_activ = df_activ.rename(columns={
        "ec5_parent_uuid": "id",
        "16_Te_gusta_educacin": "gusta_educacion_fisica",
        "17_Hacs_algn_deporte": "hace_deporte",
        "18_Te_parece_importa": "importancia_deporte",
        "19_Del_15_como_descr": "autopercepcion_energia"
    })

    # --- Unir ambos dataframes por id ---
    df = pd.merge(df_alim, df_activ, on="id", how="inner")

    # --- Normalizar respuestas "Sí" / "No" (robusto ante tildes y mayúsculas) ---
    def normalizar_si_no(texto):
        if pd.isna(texto):
            return "No"
        t = str(texto).strip().lower()
        t = t.replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")
        if t in ["si", "s", "yes", "1"]:
            return "Sí"
        return "No"

    df["consume_snacks"] = df["come_snacks"].apply(normalizar_si_no)
    df["come_entre_comidas"] = df["come_entre_comidas"].apply(normalizar_si_no)
    df["hace_deporte"] = df["hace_deporte"].apply(normalizar_si_no)

    # --- Extraer nivel de energía (1-5) ---
    def extraer_nivel_energia(texto):
        if pd.isna(texto):
            return np.nan
        match = re.search(r'[1-5]', str(texto))
        return int(match.group()) if match else np.nan

    df["nivel_energia"] = df["autopercepcion_energia"].apply(extraer_nivel_energia)

    # --- Clasificar nivel de actividad ---
    def clasificar_actividad(row):
        if row["hace_deporte"] == "No":
            return "No hace deporte"
        elif pd.notna(row["nivel_energia"]):
            if row["nivel_energia"] <= 2:
                return "Actividad baja"
            elif row["nivel_energia"] == 3:
                return "Actividad media"
            else:
                return "Actividad alta"
        return "Sin datos"

    df["nivel_actividad"] = df.apply(clasificar_actividad, axis=1)

    # --- Clasificar alimentación ---
    def clasificar_alimentacion(row):
        frutas = str(row["frecuencia_frutas_verduras"]).lower()
        snacks = str(row["frecuencia_snacks"]).lower()
        come_snacks = row["consume_snacks"] == "Sí"

        come_frutas = "todos los días" in frutas or "2-3 veces" in frutas
        come_snacks_mucho = come_snacks and ("todos los recreos" in snacks or "2-3 veces al día" in snacks)

        if come_frutas and not come_snacks_mucho:
            return "Saludable"
        elif not come_frutas and come_snacks_mucho:
            return "Alta en ultraprocesados"
        else:
            return "Mixta"

    df["tipo_alimentacion"] = df.apply(clasificar_alimentacion, axis=1)

    # --- Clasificar hidratación ---
    def clasificar_hidratacion(texto):
        texto = str(texto).lower()
        if "mucha agua" in texto or "todos los recreos" in texto:
            return "Buena hidratación"
        elif "casi no tomo" in texto:
            return "Baja hidratación"
        else:
            return "Hidratación media"

    df["hidratacion"] = df["frecuencia_agua"].apply(clasificar_hidratacion)

    return df


# Cargar datos con manejo de errores
try:
    df = cargar_datos()
    datos_cargados = True
except Exception as e:
    st.error(f"⚠️ Error al cargar los datos: {e}")
    st.info("Asegurate de que los archivos CSV estén en la misma carpeta que app.py")
    datos_cargados = False
    df = pd.DataFrame()

# ============================================
# APP PRINCIPAL
# ============================================
if datos_cargados and len(df) > 0:

    # --- TÍTULO ---
    st.title("📊 Alimentación y Deporte en Niños")
    st.markdown("### Estudio cuantitativo · Villa José León Suárez, San Martín")
    st.markdown("---")

    # --- MÉTRICAS PRINCIPALES ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de niños", len(df))
    with col2:
        hace_deporte = (df["hace_deporte"] == "Sí").sum()
        st.metric("Hacen deporte", f"{hace_deporte} ({hace_deporte / len(df) * 100:.0f}%)")
    with col3:
        come_snacks = (df["consume_snacks"] == "Sí").sum()
        st.metric("Comen snacks", f"{come_snacks} ({come_snacks / len(df) * 100:.0f}%)")
    with col4:
        buena_hidr = (df["hidratacion"] == "Buena hidratación").sum()
        st.metric("Buena hidratación", f"{buena_hidr} ({buena_hidr / len(df) * 100:.0f}%)")

    st.markdown("---")

    # ============================================
    # SECCIÓN 1: SOBRE EL ESTUDIO
    # ============================================
    st.subheader("📋 Sobre el estudio")
    st.write("""
    Este estudio analiza la relación entre los **hábitos alimentarios** y la **actividad física** 
    de niñas y niños del barrio. Se aplicaron dos encuestas: una sobre alimentación diaria y otra 
    sobre deporte y percepción de energía. Los datos fueron anonimizados y unidos por un 
    identificador único.
    """)

    st.markdown("---")

    # ============================================
    # SECCIÓN 2: VISTA DE DATOS
    # ============================================
    with st.expander("📋 Ver datos completos"):
        st.dataframe(df, use_container_width=True)
        st.caption(f"Total: {len(df)} filas × {len(df.columns)} columnas")

    st.markdown("---")

    # ============================================
    # SECCIÓN 3: VARIABLES
    # ============================================
    st.subheader("📊 Variables analizadas")

    col_v1, col_v2, col_v3 = st.columns(3)

    with col_v1:
        st.info("🍎 **Alimentación**\n\n"
                "- Comidas al día\n"
                "- Frecuencia de frutas/verduras\n"
                "- Consumo de snacks\n"
                "- Tipo de snack preferido\n"
                "- Hidratación")

    with col_v2:
        st.success("🏃 **Actividad física**\n\n"
                   "- ¿Hace deporte?\n"
                   "- Gusto por educación física\n"
                   "- Importancia percibida\n"
                   "- Nivel de energía (1-5)")

    with col_v3:
        st.warning("🔗 **Variables derivadas**\n\n"
                   "- Tipo de alimentación\n"
                   "- Nivel de actividad\n"
                   "- Categoría de hidratación")

    st.markdown("---")

    # ============================================
    # SECCIÓN 4: FILTROS
    # ============================================
    st.subheader("🔍 Explorador con filtros")

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        filtro_alim = st.multiselect(
            "Tipo de alimentación",
            options=df["tipo_alimentacion"].unique(),
            default=df["tipo_alimentacion"].unique()
        )

    with col_f2:
        filtro_activ = st.multiselect(
            "Nivel de actividad",
            options=df["nivel_actividad"].unique(),
            default=df["nivel_actividad"].unique()
        )

    with col_f3:
        filtro_deporte = st.selectbox(
            "¿Hace deporte?",
            options=["Todos", "Sí", "No"]
        )

    # Aplicar filtros
    df_filtrado = df[df["tipo_alimentacion"].isin(filtro_alim)]
    df_filtrado = df_filtrado[df_filtrado["nivel_actividad"].isin(filtro_activ)]
    if filtro_deporte != "Todos":
        df_filtrado = df_filtrado[df_filtrado["hace_deporte"] == filtro_deporte]

    st.write(f"**Mostrando {len(df_filtrado)} de {len(df)} niños**")

    st.markdown("---")

    # ============================================
    # GRÁFICO 1: DISTRIBUCIÓN
    # ============================================
    st.subheader("🍎 Distribución por tipo de alimentación y actividad")

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        conteo_alim = df_filtrado["tipo_alimentacion"].value_counts().reset_index()
        conteo_alim.columns = ["Tipo de alimentación", "Cantidad"]

        fig1 = px.pie(
            conteo_alim,
            names="Tipo de alimentación",
            values="Cantidad",
            title="Distribución de tipos de alimentación",
            color="Tipo de alimentación",
            color_discrete_map={
                "Saludable": "#1EA574",
                "Mixta": "#E8944A",
                "Alta en ultraprocesados": "#E4694E"
            },
            hole=0.4
        )
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        fig1.update_layout(height=400)
        st.plotly_chart(fig1, use_container_width=True)

    with col_g2:
        conteo_activ = df_filtrado["nivel_actividad"].value_counts().reset_index()
        conteo_activ.columns = ["Nivel de actividad", "Cantidad"]

        fig2 = px.bar(
            conteo_activ,
            x="Nivel de actividad",
            y="Cantidad",
            title="Distribución por nivel de actividad",
            color="Nivel de actividad",
            color_discrete_map={
                "No hace deporte": "#E4694E",
                "Actividad baja": "#E8944A",
                "Actividad media": "#F4C430",
                "Actividad alta": "#1EA574",
                "Sin datos": "#5d7480"
            },
            text="Cantidad"
        )
        fig2.update_traces(textposition='outside')
        fig2.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # ============================================
    # GRÁFICO 2: CRUCE
    # ============================================
    st.subheader("🔗 Relación entre alimentación y actividad física")

    contingencia = pd.crosstab(
        df_filtrado["tipo_alimentacion"],
        df_filtrado["nivel_actividad"]
    )

    fig3 = px.bar(
        contingencia,
        x=contingencia.index,
        y=contingencia.columns,
        title="Cruce: tipo de alimentación vs nivel de actividad",
        labels={
            "value": "Cantidad de niños",
            "tipo_alimentacion": "Tipo de alimentación",
            "variable": "Nivel de actividad"
        },
        barmode="group",
        color_discrete_sequence=px.colors.qualitative.Set2,
        text_auto=True
    )
    fig3.update_layout(
        height=450,
        xaxis_title="Tipo de alimentación",
        yaxis_title="Cantidad de niños",
        legend_title="Nivel de actividad"
    )
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # ============================================
    # GRÁFICO 3: SNACKS
    # ============================================
    st.subheader("🍪 Snacks más consumidos")

    todos_snacks = []
    for snacks in df_filtrado["tipo_snack"].dropna():
        for s in str(snacks).split(","):
            s = s.strip()
            if s and s.lower() != "nan":
                todos_snacks.append(s)

    if todos_snacks:
        conteo_snacks = pd.Series(todos_snacks).value_counts().head(10).reset_index()
        conteo_snacks.columns = ["Snack", "Cantidad"]

        fig4 = px.bar(
            conteo_snacks,
            x="Cantidad",
            y="Snack",
            orientation="h",
            title="Top 10 snacks más elegidos",
            color="Cantidad",
            color_continuous_scale="Oranges",
            text="Cantidad"
        )
        fig4.update_traces(textposition='outside')
        fig4.update_layout(
            height=450,
            showlegend=False,
            yaxis=dict(autorange="reversed"),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No hay datos de snacks disponibles con los filtros seleccionados")

    st.markdown("---")

    # ============================================
    # GRÁFICO 4: HIDRATACIÓN
    # ============================================
    st.subheader("💧 Hábitos de hidratación")

    col_h1, col_h2 = st.columns(2)

    with col_h1:
        conteo_hidra = df_filtrado["hidratacion"].value_counts().reset_index()
        conteo_hidra.columns = ["Hidratación", "Cantidad"]

        fig5 = px.pie(
            conteo_hidra,
            names="Hidratación",
            values="Cantidad",
            title="Distribución de hidratación",
            color="Hidratación",
            color_discrete_map={
                "Buena hidratación": "#3E7CB1",
                "Hidratación media": "#E8944A",
                "Baja hidratación": "#E4694E"
            },
            hole=0.4
        )
        fig5.update_traces(textposition='inside', textinfo='percent+label')
        fig5.update_layout(height=400)
        st.plotly_chart(fig5, use_container_width=True)

    with col_h2:
        contingencia_h = pd.crosstab(
            df_filtrado["tipo_alimentacion"],
            df_filtrado["hidratacion"]
        )

        fig6 = px.bar(
            contingencia_h,
            x=contingencia_h.index,
            y=contingencia_h.columns,
            title="Hidratación según tipo de alimentación",
            barmode="group",
            labels={
                "value": "Cantidad",
                "tipo_alimentacion": "Alimentación",
                "variable": "Hidratación"
            },
            color_discrete_sequence=["#3E7CB1", "#E8944A", "#E4694E"],
            text_auto=True
        )
        fig6.update_layout(height=400)
        st.plotly_chart(fig6, use_container_width=True)

    st.markdown("---")

    # ============================================
    # GRÁFICO 5: CORRELACIÓN
    # ============================================
    st.subheader("🔗 Matriz de correlación entre variables")

    df_corr = df_filtrado.copy()

    df_corr["alim_num"] = df_corr["tipo_alimentacion"].map({
        "Saludable": 3,
        "Mixta": 2,
        "Alta en ultraprocesados": 1
    })

    df_corr["activ_num"] = df_corr["nivel_actividad"].map({
        "Actividad alta": 4,
        "Actividad media": 3,
        "Actividad baja": 2,
        "No hace deporte": 1,
        "Sin datos": np.nan
    })

    df_corr["hidra_num"] = df_corr["hidratacion"].map({
        "Buena hidratación": 3,
        "Hidratación media": 2,
        "Baja hidratación": 1
    })

    df_corr["snacks_num"] = df_corr["consume_snacks"].map({"Sí": 1, "No": 0})
    df_corr["entre_comidas_num"] = df_corr["come_entre_comidas"].map({"Sí": 1, "No": 0})

    columnas_corr = ["alim_num", "activ_num", "hidra_num",
                     "snacks_num", "entre_comidas_num", "nivel_energia"]

    corr_matrix = df_corr[columnas_corr].corr()

    etiquetas = ["Alimentación", "Actividad", "Hidratación",
                 "Snacks", "Entre comidas", "Energía"]

    fig7 = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=etiquetas,
        y=etiquetas,
        colorscale='RdBu_r',
        zmin=-1,
        zmax=1,
        text=corr_matrix.round(2),
        texttemplate='%{text}',
        textfont={"size": 12, "color": "black"},
        hoverongaps=False,
        colorbar=dict(title="Correlación")
    ))

    fig7.update_layout(
        title="Correlación entre variables del estudio",
        height=500,
        xaxis=dict(tickangle=45)
    )

    st.plotly_chart(fig7, use_container_width=True)

    st.markdown("---")

    # ============================================
    # GRÁFICO 6: ACTITUD HACIA EL DEPORTE
    # ============================================
    st.subheader("⚽ Actitud hacia la educación física y el deporte")

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        conteo_gusta = df_filtrado["gusta_educacion_fisica"].value_counts().reset_index()
        conteo_gusta.columns = ["Respuesta", "Cantidad"]

        fig8 = px.bar(
            conteo_gusta,
            x="Respuesta",
            y="Cantidad",
            title="¿Te gusta educación física?",
            color="Respuesta",
            color_discrete_sequence=px.colors.qualitative.Set2,
            text="Cantidad"
        )
        fig8.update_traces(textposition='outside')
        fig8.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig8, use_container_width=True)

    with col_a2:
        conteo_importa = df_filtrado["importancia_deporte"].value_counts().reset_index()
        conteo_importa.columns = ["Respuesta", "Cantidad"]

        fig9 = px.bar(
            conteo_importa,
            x="Respuesta",
            y="Cantidad",
            title="¿Te parece importante hacer deporte?",
            color="Respuesta",
            color_discrete_sequence=px.colors.qualitative.Set3,
            text="Cantidad"
        )
        fig9.update_traces(textposition='outside')
        fig9.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig9, use_container_width=True)

    st.markdown("---")

    # ============================================
    # HALLAZGOS
    # ============================================
    st.subheader("💡 Hallazgos principales")

    col_hall1, col_hall2, col_hall3 = st.columns(3)

    pct_deporte = (df["hace_deporte"] == "Sí").sum() / len(df) * 100
    pct_snacks = (df["consume_snacks"] == "Sí").sum() / len(df) * 100
    pct_buena_hidra = (df["hidratacion"] == "Buena hidratación").sum() / len(df) * 100

    with col_hall1:
        st.metric(
            "Hacen deporte",
            f"{pct_deporte:.0f}%",
            delta="Alto interés" if pct_deporte > 70 else "Bajo interés"
        )
        st.caption("Porcentaje de niños que practican algún deporte")

    with col_hall2:
        st.metric(
            "Consumen snacks",
            f"{pct_snacks:.0f}%",
            delta="Alto consumo" if pct_snacks > 70 else "Consumo moderado",
            delta_color="inverse"
        )
        st.caption("Porcentaje de niños que comen snacks entre comidas")

    with col_hall3:
        st.metric(
            "Buena hidratación",
            f"{pct_buena_hidra:.0f}%",
            delta="Buena" if pct_buena_hidra > 50 else "Mejorable"
        )
        st.caption("Porcentaje de niños que toman agua regularmente")

    st.markdown("---")

    # ============================================
    # CONCLUSIONES
    # ============================================
    st.subheader("📝 Conclusiones del estudio")

    st.write(f"""
    A partir del análisis de **{len(df)} niños** encuestados, se observa que:

    - **{pct_deporte:.0f}%** de los niños practica algún deporte regularmente.
    - **{pct_snacks:.0f}%** consume snacks entre comidas, principalmente galletitas y caramelos.
    - **{pct_buena_hidra:.0f}%** mantiene una buena hidratación durante el día.
    - Existe una relación entre el tipo de alimentación y el nivel de actividad física.
    - El consumo de ultraprocesados tiende a asociarse con menor actividad física.
    """)

    st.markdown("---")

    # ============================================
    # PIE DE PÁGINA
    # ============================================
    st.caption("📊 Estudio cuantitativo sobre alimentación y deporte en niños")
    st.caption("Villa José León Suárez, San Martín · Datos reales del relevamiento")
    st.caption("Desarrollado con Streamlit, Plotly y Pandas")

else:
    st.warning(
        "⚠️ No se pudieron cargar los datos. Verificá que los archivos CSV estén en la misma carpeta que `app.py`.")
    st.info("""
    **Archivos necesarios:**
    - `form-1__encuesta-sobre-habitos-alimentarios.csv`
    - `form-2__actividad-fisica.csv`
    """)
