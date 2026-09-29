import hashlib
import secrets
import textwrap
from datetime import datetime, timedelta

import streamlit as st
from config.colors import (
    FOND_PAGE, TEXTE_MUET, TEXTE_PRINCIPAL, TEXTE_SECONDAIRE, VERT, VERT_FONCE,
)
from database.connexion import obtenir_connexion
from fonctions.utilisateurs import (
    obtenir_utilisateur_par_email,
    reinitialiser_mot_de_passe,
)


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
# STYLE (identique aux autres pages d'authentification)
# ==========================================

def _appliquer_style():
    st.markdown(
        textwrap.dedent(
            f"""
            <style>
            .stApp {{ background-color: {FOND_PAGE}; }}
            .login-badge {{
                width: 64px; height: 64px; border-radius: 50%;
                background: {VERT}; display: flex; align-items: center;
                justify-content: center; font-size: 28px;
                margin: 10px auto 18px auto;
            }}
            .login-title {{
                text-align: center; color: {TEXTE_PRINCIPAL};
                font-size: 24px; font-weight: 700; margin-bottom: 4px;
            }}
            .login-subtitle {{
                text-align: center; color: {TEXTE_SECONDAIRE};
                font-size: 14px; margin-bottom: 28px;
            }}
            .login-footer {{
                text-align: center; color: {TEXTE_MUET};
                margin-top: 36px; font-size: 12px;
            }}
            .stButton > button[kind="primary"] {{
                background-color: {VERT}; border-color: {VERT};
            }}
            .stButton > button[kind="primary"]:hover {{
                background-color: {VERT_FONCE}; border-color: {VERT_FONCE};
            }}
            @media (max-width: 640px) {{
                .login-badge {{ width: 48px; height: 48px; font-size: 22px; }}
                .login-title {{ font-size: 19px; }}
                .login-subtitle {{ font-size: 12px; }}
            }}
            </style>
            """
        ),
        unsafe_allow_html=True
    )


# ==========================================
# ÉTAPE 1 : DEMANDER UN CODE
# ==========================================

def _etape_demande():

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
            "📩 Envoyer le code de récupération",
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
                        "Un code de récupération a été généré, valable "
                        "30 minutes."
                    )
                    st.info(
                        "🚧 Mode développement : l'envoi d'e-mail n'est pas "
                        "encore connecté. En attendant, voici votre code "
                        "(normalement envoyé par e-mail) :"
                    )
                    st.code(token, language=None)
                else:
                    # Message volontairement générique, pour ne pas révéler
                    # si un compte existe avec cet e-mail
                    st.success(
                        "Si cette adresse correspond à un compte, un code "
                        "de récupération a été généré."
                    )

        if st.button(
            "J'ai déjà un code", use_container_width=True, type="secondary"
        ):
            st.session_state.etape_recuperation = "code"
            st.rerun()

        if st.button(
            "← Retour à la connexion", use_container_width=True, type="tertiary"
        ):
            st.session_state.page_auth = "connexion"
            st.rerun()


# ==========================================
# ÉTAPE 2 : SAISIR LE CODE + NOUVEAU MOT DE PASSE
# ==========================================

def _etape_reinitialisation():

    st.markdown('<div class="login-badge">🔐</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="login-title">Nouveau mot de passe</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="login-subtitle">'
        'Entrez le code reçu et choisissez un nouveau mot de passe'
        '</div>',
        unsafe_allow_html=True
    )

    with st.container(border=True):

        email = st.text_input(
            "Adresse e-mail",
            value=st.session_state.get("email_recuperation", ""),
            placeholder="exemple@gmail.com",
            key="reinit_email"
        )
        code = st.text_input(
            "Code de récupération",
            value=st.session_state.get("token_recuperation", ""),
            placeholder="Collez le code reçu par e-mail",
            key="reinit_code"
        )
        nouveau_mdp = st.text_input(
            "Nouveau mot de passe",
            type="password",
            placeholder="Minimum 8 caractères",
            key="reinit_mdp"
        )
        confirmation = st.text_input(
            "Confirmer le nouveau mot de passe",
            type="password",
            placeholder="Répétez le mot de passe",
            key="reinit_confirmation"
        )

        if st.button(
            "✅ Réinitialiser le mot de passe",
            use_container_width=True,
            type="primary"
        ):
            if not email.strip() or not code.strip() or not nouveau_mdp:
                st.warning("Veuillez remplir tous les champs.")
            elif nouveau_mdp != confirmation:
                st.error("Les mots de passe ne correspondent pas.")
            else:
                succes, message = reinitialiser_mot_de_passe(
                    email, code.strip(), nouveau_mdp
                )

                if succes:
                    st.session_state.pop("token_recuperation", None)
                    st.session_state.pop("email_recuperation", None)
                    st.session_state.pop("etape_recuperation", None)
                    st.success(f"{message} Vous pouvez maintenant vous connecter.")
                    if st.button("🔐 Aller à la connexion", use_container_width=True):
                        st.session_state.page_auth = "connexion"
                        st.rerun()
                else:
                    st.error(message)

        if st.button(
            "← Demander un nouveau code", use_container_width=True, type="tertiary"
        ):
            st.session_state.etape_recuperation = "demande"
            st.rerun()


# ==========================================
# AFFICHER LA PAGE
# ==========================================

def afficher_page_recuperation():

    _appliquer_style()

    _, colonne_centrale, _ = st.columns([1, 1.2, 1])

    with colonne_centrale:

        st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)

        if st.session_state.get("etape_recuperation") == "code":
            _etape_reinitialisation()
        else:
            _etape_demande()

        st.markdown(
            '<div class="login-footer">'
            'ComorIA Business AI • © 2026 • Tous droits réservés'
            '</div>',
            unsafe_allow_html=True
        )
