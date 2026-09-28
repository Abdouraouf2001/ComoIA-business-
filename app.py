import streamlit as st
from streamlit_option_menu import option_menu
from config.colors import BORDURE, FOND_CARTE, FOND_PAGE, TEXTE_SECONDAIRE, VERT
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
from interface.facturation import afficher_page_facturation
from interface.rapports import afficher_page_rapports
from interface.assistant_ia import afficher_page_assistant_ia
from interface.previsions import afficher_page_previsions
from interface.administrateur import afficher_page_administrateur

# ==========================================
# CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="ComorIA Business",
    page_icon="🇰🇲",
    layout="wide",
    initial_sidebar_state="collapsed"
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
# ==========================================
st.markdown(
    f"""
<style>
.stApp {{
    background-color: {FOND_PAGE};
}}
.footer {{
    text-align: center;
    margin-top: 50px;
    padding: 20px;
    color: {TEXTE_SECONDAIRE};
    border-top: 1px solid {BORDURE};
}}
</style>
""",
    unsafe_allow_html=True
)

# ==========================================
# BARRE DU HAUT : infos utilisateur + déconnexion
# ==========================================
col_info, col_bouton = st.columns([5, 1])
with col_info:
    st.caption(
        f"👤 **{st.session_state.nom_utilisateur}** • "
        f"{st.session_state.email_utilisateur} • "
        f"Rôle : {st.session_state.role}"
    )
with col_bouton:
    if st.button("🚪 Déconnexion", use_container_width=True):
        st.session_state.connecte = False
        st.session_state.utilisateur_id = None
        st.session_state.nom_utilisateur = None
        st.session_state.email_utilisateur = None
        st.session_state.role = None
        st.session_state.page_auth = "connexion"
        st.rerun()

# ==========================================
# MENU HORIZONTAL (Administration visible aux admins uniquement)
# ==========================================
options_menu = [
    "Accueil",
    "Produits",
    "Stock",
    "Ventes",
    "Facturation",
    "Dépenses",
    "Clients",
    "Rapports",
    "Assistant IA",
    "Prévisions IA",
]
icones_menu = [
    "house",
    "box-seam",
    "bar-chart",
    "cash-coin",
    "receipt",
    "credit-card",
    "people",
    "graph-up",
    "robot",
    "graph-up-arrow",
]

if st.session_state.role == "administrateur":
    options_menu.append("Administration")
    icones_menu.append("shield-lock")

menu = option_menu(
    menu_title=None,
    options=options_menu,
    icons=icones_menu,
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": FOND_CARTE},
        "icon": {"font-size": "16px"},
        "nav-link": {
            "font-size": "13px",
            "text-align": "center",
            "margin": "0px",
            "padding": "10px 8px",
        },
        "nav-link-selected": {"background-color": VERT},
    },
)

# ==========================================
# ROUTAGE DES PAGES
# ==========================================
if menu == "Accueil":
    afficher_page_accueil()
elif menu == "Produits":
    afficher_page_produits()
elif menu == "Stock":
    afficher_page_stock()
elif menu == "Ventes":
    afficher_page_ventes()
elif menu == "Facturation":
    afficher_page_facturation()
elif menu == "Dépenses":
    afficher_page_depenses()
elif menu == "Clients":
    afficher_page_clients()
elif menu == "Rapports":
    afficher_page_rapports()
elif menu == "Assistant IA":
    afficher_page_assistant_ia()
elif menu == "Prévisions IA":
    afficher_page_previsions()
elif menu == "Administration":
    afficher_page_administrateur()

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