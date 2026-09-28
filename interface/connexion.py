import textwrap

import streamlit as st
from config.colors import (
    BORDURE, FOND_PAGE, OMBRE_CARTE, TEXTE_MUET, TEXTE_PRINCIPAL,
    TEXTE_SECONDAIRE, VERT, VERT_FONCE,
)
from fonctions.utilisateurs import verifier_connexion


def afficher_page_connexion():

    st.markdown(
        textwrap.dedent(
            f"""
            <style>
            .stApp {{
                background-color: {FOND_PAGE};
            }}
            .login-badge {{
                width: 64px;
                height: 64px;
                border-radius: 50%;
                background: {VERT};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 28px;
                margin: 10px auto 18px auto;
            }}
            .login-title {{
                text-align: center;
                color: {TEXTE_PRINCIPAL};
                font-size: 26px;
                font-weight: 700;
                margin-bottom: 4px;
            }}
            .login-subtitle {{
                text-align: center;
                color: {TEXTE_SECONDAIRE};
                font-size: 14px;
                margin-bottom: 28px;
            }}
            .login-section {{
                text-align: center;
                color: {TEXTE_PRINCIPAL};
                font-size: 15px;
                font-weight: 600;
                margin: 6px 0 18px 0;
            }}
            .login-divider {{
                display: flex;
                align-items: center;
                text-align: center;
                color: {TEXTE_MUET};
                font-size: 12px;
                margin: 18px 0;
            }}
            .login-divider::before,
            .login-divider::after {{
                content: "";
                flex: 1;
                border-bottom: 1px solid {BORDURE};
            }}
            .login-divider:not(:empty)::before {{
                margin-right: 12px;
            }}
            .login-divider:not(:empty)::after {{
                margin-left: 12px;
            }}
            .login-footer {{
                text-align: center;
                color: {TEXTE_MUET};
                margin-top: 36px;
                font-size: 12px;
            }}
            div[data-testid="stVerticalBlockBorderWrapper"] {{
                box-shadow: 0 4px 24px {OMBRE_CARTE};
            }}
            .stButton > button[kind="primary"] {{
                background-color: {VERT};
                border-color: {VERT};
            }}
            .stButton > button[kind="primary"]:hover {{
                background-color: {VERT_FONCE};
                border-color: {VERT_FONCE};
            }}

            @media (max-width: 640px) {{
                .login-badge {{ width: 48px; height: 48px; font-size: 22px; }}
                .login-title {{ font-size: 21px; }}
                .login-subtitle {{ font-size: 12px; }}
            }}
            </style>
            """
        ),
        unsafe_allow_html=True
    )

    # ==========================================
    # MISE EN PAGE CENTRÉE
    # ==========================================

    _, colonne_centrale, _ = st.columns([1, 1.2, 1])

    with colonne_centrale:

        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="login-badge">🇰🇲</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="login-title">ComorIA Business</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="login-subtitle">'
            "L'intelligence artificielle au service des entreprises comoriennes"
            '</div>',
            unsafe_allow_html=True
        )

        with st.container(border=True):

            st.markdown(
                '<div class="login-section">Se connecter</div>',
                unsafe_allow_html=True
            )

            email = st.text_input(
                "Adresse e-mail",
                placeholder="exemple@gmail.com",
                key="connexion_email"
            )

            mot_de_passe = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="Votre mot de passe",
                key="connexion_mot_de_passe"
            )

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            connecter = st.button(
                "Se connecter",
                use_container_width=True,
                type="primary"
            )

            if connecter:
                if not email.strip() or not mot_de_passe:
                    st.warning("Veuillez remplir tous les champs.")
                else:
                    utilisateur = verifier_connexion(email, mot_de_passe)

                    if utilisateur:
                        st.session_state.connecte = True
                        st.session_state.utilisateur_id = utilisateur["id"]
                        st.session_state.email_utilisateur = utilisateur["email"]
                        st.session_state.nom_utilisateur = utilisateur["nom"]
                        st.session_state.role = utilisateur["role"]
                        st.rerun()
                    else:
                        st.error("Adresse e-mail ou mot de passe incorrect.")

            if st.button(
                "Mot de passe oublié ?",
                use_container_width=True,
                type="tertiary"
            ):
                st.session_state.page_auth = "recuperation"
                st.rerun()

            st.markdown('<div class="login-divider">OU</div>', unsafe_allow_html=True)

            if st.button("🔵 Continuer avec Google", use_container_width=True):
                st.info(
                    "La connexion Google sera activée "
                    "après la configuration OAuth."
                )

            if st.button(
                "Créer un compte",
                use_container_width=True,
                type="secondary"
            ):
                st.session_state.page_auth = "inscription"
                st.rerun()

        st.markdown(
            '<div class="login-footer">'
            '🇰🇲 ComorIA Business AI • © 2026 • Tous droits réservés'
            '</div>',
            unsafe_allow_html=True
        )
