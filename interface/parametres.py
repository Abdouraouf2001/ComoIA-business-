import streamlit as st
from config.colors import BORDURE, FOND_CARTE, TEXTE_SECONDAIRE, VERT
from fonctions.utilisateurs import modifier_profil_entreprise, obtenir_profil_entreprise


def afficher_page_parametres():

    st.markdown(
        f"""
        <style>
        .parametres-header {{
            background: linear-gradient(135deg, {VERT}, #006B32);
            color: {FOND_CARTE};
            padding: 14px 18px;
            border-radius: 14px;
            margin-bottom: 14px;
        }}
        .parametres-header h2 {{ margin: 0; font-size: 19px; }}
        .parametres-header p {{ margin: 4px 0 0 0; font-size: 12px; opacity: 0.9; }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="parametres-header">'
        '<h2>🏪 Mon entreprise</h2>'
        '<p>Ces informations apparaissent sur vos factures PDF.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    if "message_parametres" in st.session_state:
        st.success(st.session_state.pop("message_parametres"))

    uid = st.session_state.utilisateur_id
    profil = obtenir_profil_entreprise(uid)

    if profil is None:
        st.error("Profil introuvable.")
        return

    with st.form("formulaire_profil_entreprise"):

        nom_entreprise = st.text_input(
            "Nom de la boutique / entreprise",
            value=profil["nom_entreprise"] or "",
            placeholder=f"Laissez vide pour afficher « {profil['nom']} »"
        )
        telephone_entreprise = st.text_input(
            "Téléphone",
            value=profil["telephone_entreprise"] or "",
            placeholder="Exemple : 33 12 34 56"
        )
        adresse_entreprise = st.text_input(
            "Adresse",
            value=profil["adresse_entreprise"] or "",
            placeholder="Exemple : Moroni, Ngazidja"
        )

        enregistrer = st.form_submit_button(
            "💾 Enregistrer", use_container_width=True, type="primary"
        )

    if enregistrer:
        modifier_profil_entreprise(
            uid, nom_entreprise, telephone_entreprise, adresse_entreprise
        )
        st.session_state["message_parametres"] = "✅ Informations enregistrées."
        st.rerun()

    st.caption(
        "💡 Si le nom de la boutique reste vide, vos factures afficheront "
        f"votre nom de compte (« {profil['nom']} »)."
    )
