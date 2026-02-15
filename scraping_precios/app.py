import streamlit as st

# ----------------------------
# Config
# ----------------------------
st.set_page_config(
    page_title="Scraping de Precios",
    page_icon="📊",
    layout="wide",
)

# ----------------------------
# Estilos (CSS simple)
# ----------------------------
st.markdown(
    """
    <style>
      /* Ajustes generales */
      .block-container { padding-top: 2.2rem; padding-bottom: 2.2rem; }
      /* Hero */
      .hero {
        padding: 24px 22px;
        border-radius: 18px;
        border: 1px solid rgba(49, 51, 63, 0.12);
        background: linear-gradient(135deg, rgba(0,0,0,0.02), rgba(0,0,0,0.00));
      }
      .hero-title {
        font-size: 40px;
        font-weight: 800;
        line-height: 1.15;
        margin: 0;
      }
      .hero-sub {
        margin-top: 8px;
        font-size: 15.5px;
        opacity: 0.8;
      }

      /* Cards */
      .card {
        border-radius: 18px;
        border: 1px solid rgba(49, 51, 63, 0.12);
        padding: 18px 18px 14px 18px;
        transition: transform 120ms ease, box-shadow 120ms ease;
        background: rgba(255,255,255,0.02);
        min-height: 168px;
      }
      .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.06);
      }
      .card-kicker {
        font-size: 12px;
        letter-spacing: .08em;
        text-transform: uppercase;
        opacity: 0.7;
        margin-bottom: 10px;
      }
      .card-title {
        font-size: 20px;
        font-weight: 800;
        margin: 0;
      }
      .card-desc {
        margin-top: 8px;
        font-size: 14px;
        opacity: 0.85;
      }

      /* Badges */
      .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid rgba(49, 51, 63, 0.12);
        font-size: 12px;
        margin-right: 6px;
        opacity: .9;
      }

      /* Footer */
      .footer {
        margin-top: 22px;
        padding-top: 14px;
        border-top: 1px solid rgba(49, 51, 63, 0.12);
        font-size: 13px;
        opacity: 0.75;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.title("📌 Navegación")
    st.caption("Accedé rápido a cada módulo.")
    st.page_link("app.py", label="🏠 Inicio", icon="🏠")
    st.page_link("pages/1_Relevamiento.py", label="📅 Relevamiento Diario", icon="📅")
    st.page_link("pages/2_Dinamicas.py", label="🔁 Dinámicas", icon="🔁")
    st.page_link("pages/3_Mercado.py", label="📈 Mercado", icon="📈")
    st.divider()
    st.caption("Estado")
    st.success("App lista ✅")

# ----------------------------
# Hero
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

st.write("")
colA, colB, colC = st.columns(3, gap="large")

# ----------------------------
# Cards
# ----------------------------
with colA:
    st.markdown(
        """
        <div class="card">
          <div class="card-kicker">OPERACIÓN</div>
          <p class="card-title">📅 Relevamiento Diario</p>
          <div class="card-desc">
            Ejecutá el relevamiento, revisá precios por cadena y exportá resultados.
          </div>
          <div style="margin-top:12px;">
            <span class="badge">Ejecución</span>
            <span class="badge">Tabla</span>
            <span class="badge">Export</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.page_link("pages/1_Relevamiento.py", label="➡️ Abrir Relevamiento", icon="📅", use_container_width=True)

with colB:
    st.markdown(
        """
        <div class="card">
          <div class="card-kicker">ANÁLISIS</div>
          <p class="card-title">🔁 Dinámicas</p>
          <div class="card-desc">
            Explorá variaciones, tendencias, dispersión y comparativos.
          </div>
          <div style="margin-top:12px;">
            <span class="badge">Tendencias</span>
            <span class="badge">Variación</span>
            <span class="badge">Insights</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.page_link("pages/2_Dinamicas.py", label="➡️ Abrir Dinámicas", icon="🔁", use_container_width=True)

with colC:
    st.markdown(
        """
        <div class="card">
          <div class="card-kicker">VISTA GLOBAL</div>
          <p class="card-title">📈 Mercado</p>
          <div class="card-desc">
            Consolidado por EAN/categoría y comparaciones de mercado.
          </div>
          <div style="margin-top:12px;">
            <span class="badge">EAN</span>
            <span class="badge">Categorías</span>
            <span class="badge">Benchmark</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    st.page_link("pages/3_Mercado.py", label="➡️ Abrir Mercado", icon="📈", use_container_width=True)

# ----------------------------
# Quick actions / info
# ----------------------------
st.write("")
c1, c2 = st.columns([1.2, 1], gap="large")

with c1:
    st.subheader("🚀 Acceso rápido")
    st.write("Elegí un flujo y seguí el orden recomendado:")
    st.markdown(
        """
        1) **Relevamiento Diario** → obtener precios  
        2) **Dinámicas** → analizar variaciones  
        3) **Mercado** → comparar y consolidar  
        """
    )

with c2:
    st.subheader("⚙️ Configuración")
    st.info(
        "Tip: mantené el scraping fuera del import. "
        "Ejecutalo con botones para evitar reruns inesperados."
    )

st.markdown(
    """
    <div class="footer">
      © Scraping de Precios · Streamlit multipage · Homepage
    </div>
    """,
    unsafe_allow_html=True,
)
