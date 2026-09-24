import streamlit as st
import secrets
import hashlib
from datetime import datetime, timedelta

from database.connexion import obtenir_connexion
from services.authentification import obtenir_utilisateur_par_email


# ==========================================
# CREER UN TOKEN DE RECUPERATION
# ==========================================

def creer_token_recuperation(email):

    token = secrets.token_urlsafe(32)

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    expiration = datetime.now() + timedelta(minutes=30)

    connexion = obtenir_connexion()
    curseur = connexion.cursor()

    try:

        # Supprimer les anciens tokens
        curseur.execute(
            """
            DELETE FROM tokens_recuperation
            WHERE email = ?
            """,
            (email,)
        )

        curseur.execute(
            """
            INSERT INTO tokens_recuperation
            (
                email,
                token_hash,
                expiration
            )

            VALUES (?, ?, ?)
            """,
            (
                email,
                token_hash,
                expiration.isoformat()
            )
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
        """
        <style>

        .recovery-title {
            text-align: center;
            color: #00843D;
            font-size: 38px;
            font-weight: bold;
            margin-top: 30px;
        }

        .recovery-subtitle {
            text-align: center;
            color: #666666;
            font-size: 17px;
            margin-bottom: 30px;
        }

        .recovery-footer {
            text-align: center;
            color: #777777;
            margin-top: 40px;
            font-size: 14px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

    # =========================
    # EN-TÊTE
    # =========================

    st.markdown(
        """
        <div class="recovery-title">
            🔑 Mot de passe oublié
        </div>

        <div class="recovery-subtitle">
            Nous allons vous aider à récupérer votre compte.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("📧 Récupérer votre compte")

    st.write(
        """
        Saisissez l'adresse e-mail associée à votre
        compte ComorIA Business.
        """
    )

    email = st.text_input(
        "Adresse e-mail",
        placeholder="exemple@gmail.com",
        key="recuperation_email"
    )

    if st.button(
        "📩 Envoyer le lien de récupération",
        use_container_width=True
    ):

        email = email.strip().lower()

        if not email:

            st.warning(
                "Veuillez saisir votre adresse e-mail."
            )

        elif "@" not in email or "." not in email:

            st.error(
                "Veuillez saisir une adresse e-mail valide."
            )

        else:

            utilisateur = obtenir_utilisateur_par_email(
                email
            )

            if utilisateur:

                token = creer_token_recuperation(
                    email
                )

                st.session_state.token_recuperation = token
                st.session_state.email_recuperation = email

                st.success(
                    "Un lien de récupération va être envoyé "
                    "à votre adresse e-mail."
                )

                # Temporaire pour nos tests locaux
                st.info(
                    "Mode développement : le système de "
                    "récupération sera connecté à l'envoi "
                    "d'e-mails dans l'étape suivante."
                )

            else:

                # Message volontairement générique
                # pour éviter de révéler si un compte existe
                st.success(
                    "Si cette adresse correspond à un compte, "
                    "un lien de récupération sera envoyé."
                )

    # =========================
    # RETOUR
    # =========================

    st.markdown("")

    if st.button(
        "← Retour à la connexion",
        use_container_width=True
    ):

        st.session_state.page_auth = "connexion"

        st.rerun()

    # =========================
    # FOOTER
    # =========================

    st.markdown(
        """
        <div class="recovery-footer">

        🇰🇲 <strong>ComorIA Business AI</strong><br>

        L'IA au service des entreprises comoriennes<br><br>

        © 2026 ComorIA • Tous droits réservés

        </div>
        """,
        unsafe_allow_html=True
    )


