
import textwrap

import streamlit as st
from fonctions.utilisateurs import creer_utilisateur


def afficher_page_inscription():

    st.markdown(
        textwrap.dedent(
            """
            <style>
            .stApp {
                background-color: #F5F7F7;
            }
            .login-badge {
                width: 64px;
                height: 64px;
                border-radius: 50%;
                background: #00843D;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 28px;
                margin: 10px auto 18px auto;
            }
            .login-title {
                text-align: center;
                color: #111827;
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 4px;
            }
            .login-subtitle {
                text-align: center;
                color: #6B7280;
                font-size: 14px;
                margin-bottom: 28px;
            }
            .login-section {
                text-align: center;
                color: #374151;
                font-size: 15px;
                font-weight: 600;
                margin: 6px 0 18px 0;
            }
            .login-divider {
                display: flex;
                align-items: center;
                text-align: center;
                color: #9CA3AF;
                font-size: 12px;
                margin: 18px 0;
            }
            .login-divider::before,
            .login-divider::after {
                content: "";
                flex: 1;
                border-bottom: 1px solid #E5E7EB;
            }
            .login-divider:not(:empty)::before { margin-right: 12px; }
            .login-divider:not(:empty)::after { margin-left: 12px; }
            .login-footer {
                text-align: center;
                color: #9CA3AF;
                margin-top: 36px;
                font-size: 12px;
            }
            .stButton > button[kind="primary"] {
                background-color: #00843D;
                border-color: #00843D;
            }
            .stButton > button[kind="primary"]:hover {
                background-color: #006B32;
                border-color: #006B32;
            }
            @media (max-width: 640px) {
                .login-badge { width: 48px; height: 48px; font-size: 22px; }
                .login-title { font-size: 19px; }
                .login-subtitle { font-size: 12px; }
            }
            </style>
            """
        ),
        unsafe_allow_html=True
    )

    _, colonne_centrale, _ = st.columns([1, 1.2, 1])

    with colonne_centrale:

        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="login-badge">🇰🇲</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="login-title">ComorIA Business</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="login-subtitle">Créez votre compte professionnel</div>',
            unsafe_allow_html=True
        )

        with st.container(border=True):

            st.markdown(
                '<div class="login-section">Créer un compte</div>',
                unsafe_allow_html=True
            )

            nom = st.text_input(
                "Nom ou nom de l'entreprise",
                placeholder="Exemple : Boutique Guilbert",
                key="inscription_nom"
            )
            email = st.text_input(
                "Adresse e-mail",
                placeholder="exemple@gmail.com",
                key="inscription_email"
            )
            mot_de_passe = st.text_input(
                "Mot de passe",
                type="password",
                placeholder="Minimum 8 caractères",
                key="inscription_mot_de_passe"
            )
            confirmation = st.text_input(
                "Confirmer le mot de passe",
                type="password",
                placeholder="Répétez votre mot de passe",
                key="inscription_confirmation"
            )

            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

            if st.button(
                "Créer mon compte",
                use_container_width=True,
                type="primary"
            ):
                nom_nettoye = nom.strip()
                email_nettoye = email.strip().lower()

                if not nom_nettoye or not email_nettoye or not mot_de_passe:
                    st.warning("Veuillez remplir tous les champs.")
                elif "@" not in email_nettoye or "." not in email_nettoye:
                    st.error("Veuillez saisir une adresse e-mail valide.")
                elif len(mot_de_passe) < 8:
                    st.warning(
                        "Le mot de passe doit contenir au moins 8 caractères."
                    )
                elif mot_de_passe != confirmation:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    succes, message = creer_utilisateur(
                        nom_nettoye, email_nettoye, mot_de_passe
                    )
                    if succes:
                        st.success(message)
                        st.info(
                            "Votre compte a été créé — cliquez sur "
                            "« J'ai déjà un compte » ci-dessous pour "
                            "vous connecter."
                        )
                    else:
                        st.error(message)

            st.markdown('<div class="login-divider">OU</div>', unsafe_allow_html=True)

            if st.button("🔵 S'inscrire avec Google", use_container_width=True):
                st.info(
                    "L'inscription avec Google sera activée "
                    "après la configuration Google OAuth."
                )

            if st.button(
                "J'ai déjà un compte",
                use_container_width=True,
                type="tertiary"
            ):
                st.session_state.page_auth = "connexion"
                st.rerun()

        st.markdown(
            '<div class="login-footer">'
            'ComorIA Business AI • © 2026 • Tous droits réservés'
            '</div>',
            unsafe_allow_html=True
        )
