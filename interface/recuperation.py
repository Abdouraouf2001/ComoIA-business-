import hashlib
import secrets
import textwrap
from datetime import datetime, timedelta

import streamlit as st
from database.connexion import obtenir_connexion
from fonctions.utilisateurs import obtenir_utilisateur_par_email


# ==========================================
# CREER UN TOKEN DE RECUPERATION
# ==========================================

def creer_token_recuperation(email):

    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expiration = datetime.now() + timedelta(minutes=30)

    connexion = obtenir_connexion()

    try:
        # Supprimer les anciens tokens pour cette adresse
        connexion.execute(
            "DELETE FROM tokens_recuperation WHERE email = ?",
            (email,)
        )
        connexion.execute(
            """
            INSERT INTO tokens_recuperation (email, token_hash, expiration)
            VALUES (?, ?, ?)
            """,
            (email, token_hash, expiration.isoformat())
        )
        connexion.commit()
        return token

    finally:
        connexion.close()


# ==========================================
# AFFICHER LA PAGE
# ==========================================

def afficher_page_recuperation():

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
        st.markdown('<div class="login-badge">🔑</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="login-title">Mot de passe oublié</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            '<div class="login-subtitle">'
            'Saisissez votre e-mail pour récupérer votre compte'
            '</div>',
            unsafe_allow_html=True
        )

        with st.container(border=True):

            email = st.text_input(
                "Adresse e-mail",
                placeholder="exemple@gmail.com",
                key="recuperation_email"
            )

            if st.button(
                "📩 Envoyer le lien de récupération",
                use_container_width=True,
                type="primary"
            ):
                email = email.strip().lower()

                if not email:
                    st.warning("Veuillez saisir votre adresse e-mail.")
                elif "@" not in email or "." not in email:
                    st.error("Veuillez saisir une adresse e-mail valide.")
                else:
                    utilisateur = obtenir_utilisateur_par_email(email)

                    if utilisateur:
                        token = creer_token_recuperation(email)
                        st.session_state.token_recuperation = token
                        st.session_state.email_recuperation = email

                        st.success(
                            "Un lien de récupération va être envoyé "
                            "à votre adresse e-mail."
                        )
                        st.info(
                            "🚧 Mode développement : l'envoi d'e-mail "
                            "n'est pas encore connecté."
                        )
                    else:
                        # Message volontairement générique, pour ne pas
                        # révéler si un compte existe avec cet e-mail
                        st.success(
                            "Si cette adresse correspond à un compte, "
                            "un lien de récupération sera envoyé."
                        )

            if st.button(
                "← Retour à la connexion",
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

