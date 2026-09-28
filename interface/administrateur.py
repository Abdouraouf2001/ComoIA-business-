import textwrap

import streamlit as st
from config.colors import FOND_CARTE, VERT, VERT_FONCE
from fonctions.utilisateurs import (
    compter_utilisateurs_par_role,
    creer_utilisateur,
    lister_utilisateurs,
    modifier_role_utilisateur,
    supprimer_utilisateur,
)


def afficher_page_administrateur():

    # ==========================================
    # PROTECTION ADMINISTRATEUR
    # ==========================================

    if st.session_state.get("role") != "administrateur":
        st.error("⛔ Accès réservé aux administrateurs.")
        return

    # ==========================================
    # STYLE
    # ==========================================

    st.markdown(
        textwrap.dedent(
            f"""
            <style>
            .admin-header {{
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 25px;
                background: linear-gradient(135deg, {VERT}, {VERT_FONCE});
                color: {FOND_CARTE};
            }}
            .admin-title {{ font-size: 24px; font-weight: 700; }}
            .admin-subtitle {{ font-size: 14px; opacity: 0.9; }}
            </style>
            """
        ),
        unsafe_allow_html=True
    )

    # ==========================================
    # EN-TÊTE
    # ==========================================

    st.markdown(
        '<div class="admin-header">'
        '<div class="admin-title">🛡️ Administration</div>'
        '<div class="admin-subtitle">Gestion de ComorIA Business</div>'
        '</div>',
        unsafe_allow_html=True
    )

    # ==========================================
    # MESSAGE
    # ==========================================

    if "message_admin" in st.session_state:
        st.success(st.session_state.pop("message_admin"))

    # ==========================================
    # STATISTIQUES UTILISATEURS
    # ==========================================

    statistiques = compter_utilisateurs_par_role()
    total_commercants = statistiques.get("commercant", 0)
    total_admins = statistiques.get("administrateur", 0)
    total_utilisateurs = total_commercants + total_admins

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 Utilisateurs", total_utilisateurs)
    with col2:
        st.metric("🏪 Commerçants", total_commercants)
    with col3:
        st.metric("🛡️ Administrateurs", total_admins)

    st.divider()

    # ==========================================
    # AJOUTER UN COMMERÇANT
    # ==========================================

    with st.expander("➕ Ajouter un commerçant"):

        nom = st.text_input("Nom", key="admin_nouveau_nom")
        email = st.text_input("Adresse e-mail", key="admin_nouvel_email")
        mot_de_passe = st.text_input(
            "Mot de passe", type="password", key="admin_nouveau_mdp"
        )
        confirmation = st.text_input(
            "Confirmer le mot de passe", type="password",
            key="admin_confirmation_mdp"
        )

        if st.button("➕ Créer le compte commerçant", use_container_width=True):

            if not nom.strip():
                st.error("Veuillez saisir le nom.")
            elif not email.strip():
                st.error("Veuillez saisir l'adresse e-mail.")
            elif not mot_de_passe:
                st.error("Veuillez saisir un mot de passe.")
            elif len(mot_de_passe) < 8:
                # Aligné sur le minimum exigé à l'inscription publique
                st.error("Le mot de passe doit contenir au moins 8 caractères.")
            elif mot_de_passe != confirmation:
                st.error("Les deux mots de passe ne correspondent pas.")
            else:
                succes, message = creer_utilisateur(
                    nom=nom, email=email,
                    mot_de_passe=mot_de_passe, role="commercant"
                )
                if succes:
                    st.session_state["message_admin"] = (
                        f"Commerçant « {nom.strip()} » créé avec succès."
                    )
                    st.rerun()
                else:
                    st.error(message)

    st.divider()

    # ==========================================
    # LISTE DES UTILISATEURS
    # ==========================================

    st.subheader("👥 Gestion des utilisateurs")

    utilisateurs = lister_utilisateurs()

    if not utilisateurs:
        st.info("Aucun utilisateur enregistré.")
        return

    for utilisateur in utilisateurs:

        utilisateur_id = utilisateur["id"]
        # Clé correcte : "utilisateur_id" (pas "user_id", qui n'existe pas
        # dans la session — c'était le bug empêchant ces protections
        # de fonctionner).
        est_moi = utilisateur_id == st.session_state.get("utilisateur_id")

        st.markdown("---")

        col_info, col_role, col_action = st.columns([3, 2, 1])

        with col_info:
            st.markdown(f"**👤 {utilisateur['nom']}**")
            st.caption(f"📧 {utilisateur['email']}")
            st.caption(f"🔐 Connexion : {utilisateur['provider']}")
            st.caption(f"📅 Créé le : {utilisateur['date_creation']}")

        with col_role:
            roles = ["commercant", "administrateur"]
            role_actuel = utilisateur["role"]

            nouveau_role = st.selectbox(
                "Rôle",
                roles,
                index=roles.index(role_actuel) if role_actuel in roles else 0,
                key=f"role_{utilisateur_id}",
                disabled=est_moi,
                label_visibility="collapsed"
            )

            if nouveau_role != role_actuel and not est_moi:
                modifier_role_utilisateur(utilisateur_id, nouveau_role)
                st.session_state["message_admin"] = (
                    f"Rôle de « {utilisateur['nom']} » modifié."
                )
                st.rerun()

        with col_action:
            if est_moi:
                st.button(
                    "🛡️",
                    key=f"admin_protection_{utilisateur_id}",
                    help="Vous ne pouvez pas supprimer votre propre compte.",
                    disabled=True
                )
            elif st.button(
                "🗑️",
                key=f"suppr_user_{utilisateur_id}",
                help="Supprimer cet utilisateur"
            ):
                st.session_state["utilisateur_a_supprimer"] = utilisateur_id
                st.rerun()

        # ======================================
        # CONFIRMATION DE SUPPRESSION
        # ======================================

        if st.session_state.get("utilisateur_a_supprimer") == utilisateur_id:

            st.warning(
                f"⚠️ Voulez-vous vraiment supprimer "
                f"l'utilisateur « {utilisateur['nom']} » ?"
            )

            col_confirmer, col_annuler = st.columns(2)

            with col_confirmer:
                if st.button(
                    "✅ Confirmer la suppression",
                    key=f"confirmer_suppr_{utilisateur_id}",
                    use_container_width=True
                ):
                    supprimer_utilisateur(utilisateur_id)
                    st.session_state.pop("utilisateur_a_supprimer", None)
                    st.session_state["message_admin"] = (
                        f"Utilisateur « {utilisateur['nom']} » supprimé."
                    )
                    st.rerun()

            with col_annuler:
                if st.button(
                    "❌ Annuler",
                    key=f"annuler_suppr_{utilisateur_id}",
                    use_container_width=True
                ):
                    st.session_state.pop("utilisateur_a_supprimer", None)
                    st.rerun()


