import streamlit as st

from services.authentification import creer_utilisateur


def afficher_page_inscription():

    st.markdown(
        """
        <style>

        .register-title {
            text-align: center;
            color: #00843D;
            font-size: 38px;
            font-weight: bold;
            margin-top: 30px;
        }

        .register-subtitle {
            text-align: center;
            color: #666666;
            font-size: 17px;
            margin-bottom: 30px;
        }

        .register-footer {
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
        <div class="register-title">
            🇰🇲 ComorIA Business
        </div>

        <div class="register-subtitle">
            Créez votre compte professionnel
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================
    # FORMULAIRE
    # =========================

    st.subheader("📝 Créer un compte")

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

    # =========================
    # CREATION DU COMPTE
    # =========================

    if st.button(
        "📝 Créer mon compte",
        use_container_width=True
    ):

        nom = nom.strip()
        email = email.strip().lower()

        if not nom or not email or not mot_de_passe:

            st.warning(
                "Veuillez remplir tous les champs."
            )

        elif "@" not in email or "." not in email:

            st.error(
                "Veuillez saisir une adresse e-mail valide."
            )

        elif len(mot_de_passe) < 8:

            st.warning(
                "Le mot de passe doit contenir "
                "au moins 8 caractères."
            )

        elif mot_de_passe != confirmation:

            st.error(
                "Les mots de passe ne correspondent pas."
            )

        else:

            succes, message = creer_utilisateur(
                nom,
                email,
                mot_de_passe
            )

            if succes:

                st.success(message)

                st.info(
                    "Votre compte a été créé. "
                    "Vous pouvez maintenant vous connecter."
                )

                if st.button(
                    "🔐 Aller à la connexion"
                ):

                    st.session_state.page_auth = "connexion"

                    st.rerun()

            else:

                st.error(message)

    # =========================
    # GOOGLE
    # =========================

    st.markdown(
        "<div style='text-align:center; margin:20px 0;'>OU</div>",
        unsafe_allow_html=True
    )

    if st.button(
        "🔵 S'inscrire avec Google",
        use_container_width=True
    ):

        st.info(
            "L'inscription avec Google sera activée "
            "après la configuration Google OAuth."
        )

    # =========================
    # RETOUR CONNEXION
    # =========================

    st.markdown("")

    if st.button(
        "← J'ai déjà un compte",
        use_container_width=True
    ):

        st.session_state.page_auth = "connexion"

        st.rerun()

    # =========================
    # FOOTER
    # =========================

    st.markdown(
        """
        <div class="register-footer">

        🇰🇲 <strong>ComorIA Business AI</strong><br>

        L'IA au service des entreprises comoriennes<br><br>

        © 2026 ComorIA • Tous droits réservés

        </div>
        """,
        unsafe_allow_html=True
    )
