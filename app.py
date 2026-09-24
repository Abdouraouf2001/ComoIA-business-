
import streamlit as st
from database.models import creer_tables
from interface.connexion import afficher_page_connexion
from interface.inscription import afficher_page_inscription
from interface.recuperation import afficher_page_recuperation
from interface.accueil import afficher_page_accueil
from interface.produits import afficher_page_produits
from interface.stock import afficher_page_stock
from interface.ventes import afficher_page_ventes
from interface.depenses import afficher_page_depenses
from interface.clients import afficher_page_clients
from interface.rapports import afficher_page_rapports
from interface.assistant_ia import afficher_page_assistant_ia

# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="ComorIA Business",
    page_icon="🇰🇲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# INITIALISATION BASE DE DONNÉES
# ==========================================
creer_tables()

# ==========================================
# SESSION
# ==========================================
if "connecte" not in st.session_state:
    st.session_state.connecte = False
if "utilisateur_id" not in st.session_state:
    st.session_state.utilisateur_id = None
if "nom_utilisateur" not in st.session_state:
    st.session_state.nom_utilisateur = None
if "email_utilisateur" not in st.session_state:
    st.session_state.email_utilisateur = None
if "role" not in st.session_state:
    st.session_state.role = None
if "page_auth" not in st.session_state:
    st.session_state.page_auth = "connexion"

# ==========================================
# UTILISATEUR NON CONNECTÉ
# ==========================================
if not st.session_state.connecte:
    if st.session_state.page_auth == "connexion":
        afficher_page_connexion()
    elif st.session_state.page_auth == "inscription":
        afficher_page_inscription()
    elif st.session_state.page_auth == "recuperation":
        afficher_page_recuperation()
    st.stop()

# ==========================================
# STYLE APPLICATION
# (utilisé par accueil.py : .hero, .card — et par le footer ci-dessous)
# ==========================================
st.markdown(
    """
<style>
.stApp {
    background-color: #F5F7F7;
}
.hero {
    background: linear-gradient(135deg, #00843D, #006B32);
    padding: 45px 30px;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 30px;
}
.hero h1 {
    color: white;
    font-size: 42px;
    margin-bottom: 10px;
}
.hero p {
    color: white;
    font-size: 20px;
    margin: 0;
}
.card {
    background-color: white;
    padding: 25px;
    border-radius: 15px;
    border: 1px solid #E5E7EB;
    text-align: center;
    height: 100%;
}
.card h3 {
    color: #00843D;
}
.card p {
    color: #333333;
}
.footer {
    text-align: center;
    margin-top: 50px;
    padding: 20px;
    color: #666666;
    border-top: 1px solid #DDDDDD;
}
</style>
""",
    unsafe_allow_html=True
)

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("## ComorIA")
    st.markdown("### Business AI")
    st.divider()

    st.write(f"👤 **{st.session_state.nom_utilisateur}**")
    st.caption(st.session_state.email_utilisateur)
    st.caption(f"Rôle : {st.session_state.role}")
    st.divider()

    menu = st.radio(
        "Menu",
        [
            "🏠 Accueil",
            "📦 Produits",
            "📊 Stock",
            "💰 Ventes",
            "💳 Dépenses",
            "👥 Clients",
            "📈 Rapports",
            "🤖 Assistant IA"
        ]
    )
    st.divider()

    if st.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state.connecte = False
        st.session_state.utilisateur_id = None
        st.session_state.nom_utilisateur = None
        st.session_state.email_utilisateur = None
        st.session_state.role = None
        st.session_state.page_auth = "connexion"
        st.rerun()

# ==========================================
# ROUTAGE DES PAGES
# ==========================================
if menu == "🏠 Accueil":
    afficher_page_accueil()
elif menu == "📦 Produits":
    afficher_page_produits()
elif menu == "📊 Stock":
    afficher_page_stock()
elif menu == "💰 Ventes":
    afficher_page_ventes()
elif menu == "💳 Dépenses":
    afficher_page_depenses()
elif menu == "👥 Clients":
    afficher_page_clients()
elif menu == "📈 Rapports":
    afficher_page_rapports()
elif menu == "🤖 Assistant IA":
    afficher_page_assistant_ia()

# ==========================================
# FOOTER (affiché sur toutes les pages, hors connexion)
# ==========================================
st.markdown(
    '<div class="footer">'
     '<strong>ComorIA Business AI</strong><br>'
    "L'intelligence artificielle au service des entreprises comoriennes<br><br>"
    '© 2026 ComorIA • Tous droits réservés'
    '</div>',
    unsafe_allow_html=True
)
