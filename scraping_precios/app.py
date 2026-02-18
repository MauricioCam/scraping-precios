
import streamlit as st
from datetime import datetime

# ----------------------------
# Config
# ----------------------------
st.set_page_config(
    page_title="Scraping de Precios",
    page_icon="📊",
    layout="wide",
)

# ----------------------------
# Estado simple (KPIs)
# ----------------------------
APP_VERSION = "v1.2 (Estilos mejorados)"

def _fmt_dt(dt):
    if not dt:
        return "—"
    try:
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(dt)

last_run_at = st.session_state.get("last_run_at", None)
last_run_ok = st.session_state.get("last_run_ok", True)
skus_count = st.session_state.get("skus_count", "—")

# ----------------------------
# Estilos (CSS) Optimizado y Mejorado
# ----------------------------
st.markdown(
    """
    <style>
      /* Layout adjustments */
      .block-container { padding-top: 1.8rem; padding-bottom: 2.2rem; }
      [data-testid="stSidebarNav"] { display: none; }

      /* --- NUEVO: Estilos para los contenedores nativos con borde --- */
      /*
         Apuntamos al wrapper interno que Streamlit usa cuando pones border=True.
         Usamos !important para asegurar que sobrescriba los estilos por defecto de Streamlit.
      */
      [data-testid="stVerticalBlockBorderWrapper"] {
          border-radius: 24px !important; /* Bordes mucho más curvos */
          border: 1px solid rgba(0, 0, 0, 0.08) !important; /* Borde sutil */
          /* Sombreado suave para dar profundidad */
          box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06) !important;
          background-color: #ffffff; /* Fondo blanco limpio */
          transition: all 0.3s ease; /* Transición suave para el hover */
          padding: 10px !important; /* Un poco más de aire interno */
      }

      /* Opcional: Efecto hover para que interactúe al pasar el mouse */
      [data-testid="stVerticalBlockBorderWrapper"]:hover {
          box-shadow: 0 10px 24px rgba(0, 0, 0, 0.1) !important;
          transform: translateY(-3px); /* Pequeña elevación */
          border-color: rgba(0, 0, 0, 0.15) !important;
      }


      /* Hero Style */
      .hero {
        padding: 22px 22px;
        border-radius: 18px;
        # border: 1px solid rgba(49, 51, 63, 0.12);
        background: linear-gradient(135deg, rgba(0,0,0,0.04), rgba(0,0,0,0.01));
        margin-bottom: 30px;
      }
      .hero-title {
        font-size: clamp(28px, 3vw, 38px);
        font-weight: 850;
        line-height: 1.12;
        margin: 0;
        color: #31333F;
      }
      .hero-sub {
        margin-top: 8px;
        font-size: 16px;
        opacity: 0.85;
        color: #31333F;
      }

      /* Estilos de tipografía interna de las Cards */
      .card-kicker {
        font-size: 12px;
        letter-spacing: .08em;
        text-transform: uppercase;
        font-weight: 700;
        margin-bottom: 8px;
        color: #FF4B4B; /* Color acento de Streamlit */
      }
      .card-title {
        font-size: 22px;
        font-weight: 800;
        margin: 0;
        color: #31333F;
      }
      .card-desc {
        margin-top: 8px;
        font-size: 15px;
        color: #555;
        margin-bottom: 20px; /* Espacio para el botón nativo */
        min-height: 45px; /* Alineación visual */
        line-height: 1.4;
      }

      /* Footer */
      .footer {
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid rgba(49, 51, 63, 0.12);
        font-size: 13px;
        opacity: 0.75;
        text-align: center;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Sidebar (Navegación nativa)
# ----------------------------
with st.sidebar:
    st.title("📌 Navegación")
    st.caption("Seleccioná un módulo")

    st.page_link("app.py", label="🏠 Inicio")
    st.page_link("pages/1_Relevamiento.py", label="📅 Relevamiento Diario")
    st.page_link("pages/2_Dinamicas.py", label="🔁 Dinámicas")
    st.page_link("pages/3_Mercado.py", label="📈 Mercado")

    st.divider()

    st.subheader("Estado")
    if last_run_ok:
        st.success("App lista ✅")
    else:
        st.error("Atención: última corrida con errores ⚠️")

    st.caption(f"Versión: {APP_VERSION}")
    st.caption(f"Última corrida: {_fmt_dt(last_run_at)}")

# ----------------------------
# Hero Section
# ----------------------------
st.markdown(
    """
    <div class="hero">
      <p class="hero-title">📊 Scraping de Precios</p>
      <p class="hero-sub">
        Panel unificado para relevamiento diario, análisis de dinámicas y vista de mercado.
        Elegí un módulo para comenzar.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Cards (Usando st.container con estilos personalizados)
# ----------------------------
# Aumenté un poco el gap para que las sombras no se solapen
colA, colB, colC = st.columns(3, gap="large")

# --- Card 1: Relevamiento ---
with colA:
    # Usamos border=True, y el CSS lo personaliza
    with st.container(border=True):
        st.markdown(
            """
            <div class="card-kicker">OPERACIÓN</div>
            <p class="card-title">📅 Relevamiento Diario</p>
            <div class="card-desc">
                Ejecutá el relevamiento, revisá precios por cadena y exportá resultados.
            </div>
            """,
            unsafe_allow_html=True
        )
        # Use_container_width hace que el botón se expanda
        st.page_link("pages/1_Relevamiento.py", label="Abrir Relevamiento", icon="➡️", use_container_width=True)

# --- Card 2: Dinámicas ---
with colB:
    with st.container(border=True):
        st.markdown(
            """
            <div class="card-kicker">ANÁLISIS</div>
            <p class="card-title">🔁 Dinámicas</p>
            <div class="card-desc">
                Explorá variaciones, tendencias, dispersión y comparativos de precios.
            </div>
            """,
            unsafe_allow_html=True
        )
        st.page_link("pages/2_Dinamicas.py", label="Abrir Dinámicas", icon="➡️", use_container_width=True)

# --- Card 3: Mercado ---
with colC:
    with st.container(border=True):
        st.markdown(
            """
            <div class="card-kicker">VISTA GLOBAL</div>
            <p class="card-title">📈 Mercado</p>
            <div class="card-desc">
                Consolidado por EAN/categoría y comparaciones de mercado.
            </div>
            """,
            unsafe_allow_html=True
        )
        st.page_link("pages/3_Mercado.py", label="Abrir Mercado", icon="➡️", use_container_width=True)

# ----------------------------
# Guía + Config
# ----------------------------
st.write("")
st.divider()
left, right = st.columns([1.5, 1], gap="large") # Ajusté proporciones

with left:
    st.subheader("🚀 Acceso rápido")
    st.write("Elegí un flujo y seguí el orden recomendado:")
    st.info(
        """
        1. **Relevamiento Diario** → obtener precios
        2. **Dinámicas** → analizar variaciones
        3. **Mercado** → comparar y consolidar
        """
    )

with right:
    st.subheader("⚙️ Configuración")
    with st.container(border=True):
         st.write("Configuraciones globales del scraper.")
         st.toggle("Modo debug", value=False)
         st.button("Limpiar caché", use_container_width=True)


# ----------------------------
# Footer
# ----------------------------
st.markdown(
    """
    <div class="footer">
      Feedback y oportunidades de mejora son bienvenidas · © Scraping de Precios
    </div>
    """,
    unsafe_allow_html=True,
)
