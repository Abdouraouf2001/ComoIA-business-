from contextlib import closing

import streamlit as st
from fonctions.utilisateurs import (
    compter_utilisateurs_par_role,
    lister_utilisateurs,
    modifier_role_utilisateur,
    supprimer_utilisateur,
    creer_utilisateur,
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
        """
        <style>
        .admin-header {
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 25px;
            background: linear-gradient(135deg, #00843D, #006B32);
            color: white;
        }

        .admin-title {
            font-size: 30px;
            font-weight: 700;
        }

        .admin-subtitle {
            font-size: 15px;
            opacity: 0.9;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ==========================================
    # EN-TÊTE
    # ==========================================

    st.markdown(
        """
        <div class="admin-header">
            <div class="admin-title">🛡️ Administration</div>
            <div class="admin-subtitle">
                Gestion de Comoria Business
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ==========================================
    # MESSAGE
    # ==========================================

    if "message_admin" in st.session_state:
        st.success(st.session_state["message_admin"])
        del st.session_state["message_admin"]

    # ==========================================
    # STATISTIQUES UTILISATEURS
    # ==========================================

    statistiques = compter_utilisateurs_par_role()

    total_commercants = statistiques.get("commercant", 0)
    total_admins = statistiques.get("administrateur", 0)
    total_utilisateurs = total_commercants + total_admins

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "👥 Utilisateurs",
            total_utilisateurs
        )

    with col2:
        st.metric(
            "🏪 Commerçants",
            total_commercants
        )

    with col3:
        st.metric(
            "🛡️ Administrateurs",
            total_admins
        )

    st.divider()

    # ==========================================
    # AJOUTER UN COMMERÇANT
    # ==========================================

    with st.expander("➕ Ajouter un commerçant"):

        nom = st.text_input(
            "Nom",
            key="admin_nouveau_nom"
        )

        email = st.text_input(
            "Adresse e-mail",
            key="admin_nouvel_email"
        )

        mot_de_passe = st.text_input(
            "Mot de passe",
            type="password",
            key="admin_nouveau_mdp"
        )

        confirmation = st.text_input(
            "Confirmer le mot de passe",
            type="password",
            key="admin_confirmation_mdp"
        )

        if st.button(
            "➕ Créer le compte commerçant",
            use_container_width=True
        ):

            if not nom.strip():
                st.error("Veuillez saisir le nom.")

            elif not email.strip():
                st.error("Veuillez saisir l'adresse e-mail.")

            elif not mot_de_passe:
                st.error("Veuillez saisir un mot de passe.")

            elif len(mot_de_passe) < 6:
                st.error(
                    "Le mot de passe doit contenir au moins 6 caractères."
                )

            elif mot_de_passe != confirmation:
                st.error(
                    "Les deux mots de passe ne correspondent pas."
                )

            else:

                succes, message = creer_utilisateur(
                    nom=nom,
                    email=email,
                    mot_de_passe=mot_de_passe,
                    role="commercant"
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

    # ==========================================
    # UTILISATEURS
    # ==========================================

    for utilisateur in utilisateurs:

        utilisateur_id = utilisateur["id"]

        st.markdown("---")

        col_info, col_role, col_action = st.columns(
            [3, 2, 1]
        )

        # --------------------------------------
        # INFORMATIONS
        # --------------------------------------

        with col_info:

            st.markdown(
                f"**👤 {utilisateur['nom']}**"
            )

            st.caption(
                f"📧 {utilisateur['email']}"
            )

            st.caption(
                f"🔐 Connexion : {utilisateur['provider']}"
            )

            st.caption(
                f"📅 Créé le : {utilisateur['date_creation']}"
            )

        # --------------------------------------
        # ROLE
        # --------------------------------------

        with col_role:

            roles = [
                "commercant",
                "administrateur"
            ]

            role_actuel = utilisateur["role"]

            nouveau_role = st.selectbox(
                "Rôle",
                roles,
                index=(
                    roles.index(role_actuel)
                    if role_actuel in roles
                    else 0
                ),
                key=f"role_{utilisateur_id}",
                disabled=(
                    utilisateur["id"]
                    == st.session_state.get("user_id")
                )
            )

            if nouveau_role != role_actuel:

                modifier_role_utilisateur(
                    utilisateur_id,
                    nouveau_role
                )

                st.session_state["message_admin"] = (
                    f"Rôle de « {utilisateur['nom']} » modifié."
                )

                st.rerun()

        # --------------------------------------
        # SUPPRESSION
        # --------------------------------------

        with col_action:

            est_moi = (
                utilisateur["id"]
                == st.session_state.get("user_id")
            )

            if est_moi:

                st.button(
                    "🛡️",
                    key=f"admin_protection_{utilisateur_id}",
                    help="Vous ne pouvez pas supprimer votre propre compte.",
                    disabled=True
                )

            else:

                if st.button(
                    "🗑️",
                    key=f"suppr_user_{utilisateur_id}",
                    help="Supprimer cet utilisateur"
                ):

                    st.session_state[
                        "utilisateur_a_supprimer"
                    ] = utilisateur_id

                    st.rerun()

        # ======================================
        # CONFIRMATION DE SUPPRESSION
        # ======================================

        if (
            st.session_state.get(
                "utilisateur_a_supprimer"
            )
            == utilisateur_id
        ):

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

                    supprimer_utilisateur(
                        utilisateur_id
                    )

                    st.session_state.pop(
                        "utilisateur_a_supprimer",
                        None
                    )

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

                    st.session_state.pop(
                        "utilisateur_a_supprimer",
                        None
                    )

                    st.rerun()


# import streamlit as st
# from database.connexion import obtenir_connexion
# from fonctions.utilisateurs import (
#     compter_utilisateurs_par_role,
#     lister_utilisateurs,
#     modifier_role_utilisateur,
#     supprimer_utilisateur,
# )

# ROLES = ["commercant", "administrateur"]


# def afficher_page_administrateur():

#     # Garde-fou : même si le menu ne montre cette page qu'aux admins,
#     # on revérifie ici au cas où quelqu'un accéderait directement.
#     if st.session_state.get("role") != "administrateur":
#         st.error("⛔ Accès réservé aux administrateurs.")
#         return

#     st.markdown(
#         """
#         <style>
#         .admin-header {
#             background: linear-gradient(135deg, #1F2937, #111827);
#             border-radius: 14px;
#             padding: 14px 18px;
#             margin-bottom: 14px;
#         }
#         .admin-header .titre { color: white; font-size: 19px; font-weight: 700; margin: 0; }
#         .admin-header .sous-titre { color: rgba(255,255,255,0.75); font-size: 12px; margin-top: 2px; }
#         .section-title { font-size: 14px; font-weight: 600; margin: 14px 0 8px 0; }
#         .kpi-card {
#             background: white;
#             border-radius: 12px;
#             border: 1px solid #EAECEF;
#             box-shadow: 0 1px 6px rgba(16,24,40,0.04);
#             padding: 10px 12px;
#             text-align: center;
#         }
#         .kpi-value { font-size: 18px; font-weight: 700; color: #111827; }
#         .kpi-label { font-size: 11px; color: #6B7280; margin-top: 2px; }
#         .ligne-item {
#             display: flex;
#             justify-content: space-between;
#             align-items: center;
#             background: white;
#             border: 1px solid #EAECEF;
#             border-radius: 10px;
#             padding: 8px 12px;
#             margin-bottom: 6px;
#             font-size: 13px;
#         }
#         .ligne-item .nom { font-weight: 600; color: #111827; }
#         .ligne-item .meta { color: #9CA3AF; font-size: 11px; }
#         .badge-role {
#             font-size: 10px;
#             font-weight: 600;
#             padding: 2px 8px;
#             border-radius: 999px;
#         }
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

#     st.markdown(
#         '<div class="admin-header">'
#         '<p class="titre">🛡️ Administration</p>'
#         '<p class="sous-titre">Utilisateurs et vue d\'ensemble de l\'application</p>'
#         '</div>',
#         unsafe_allow_html=True
#     )

#     if "message_admin" in st.session_state:
#         st.success(st.session_state.pop("message_admin"))

#     # ==========================================
#     # STATISTIQUES GLOBALES
#     # ==========================================

#     with closing(obtenir_connexion()) as connexion:
#         nombre_produits = connexion.execute(
#             "SELECT COUNT(*) FROM produits"
#         ).fetchone()[0]
#         nombre_ventes = connexion.execute(
#             "SELECT COUNT(*) FROM ventes"
#         ).fetchone()[0]
#         nombre_clients = connexion.execute(
#             "SELECT COUNT(*) FROM clients"
#         ).fetchone()[0]
#         chiffre_affaires = connexion.execute(
#             "SELECT COALESCE(SUM(montant_total), 0) FROM ventes"
#         ).fetchone()[0]

#     roles_comptes = compter_utilisateurs_par_role()
#     total_utilisateurs = sum(roles_comptes.values())

#     st.markdown(
#         '<p class="section-title">📊 Vue d\'ensemble de l\'application</p>',
#         unsafe_allow_html=True
#     )
#     st.caption(
#         "Ces chiffres portent sur toute l'application, tous comptes "
#         "confondus (contrairement au tableau de bord d'un commerçant, "
#         "qui ne montre que ses propres données)."
#     )

#     col1, col2, col3, col4, col5 = st.columns(5)
#     with col1:
#         st.markdown(
#             f'<div class="kpi-card"><div class="kpi-value">{total_utilisateurs}</div>'
#             f'<div class="kpi-label">Utilisateurs</div></div>',
#             unsafe_allow_html=True
#         )
#     with col2:
#         st.markdown(
#             f'<div class="kpi-card"><div class="kpi-value">{nombre_produits}</div>'
#             f'<div class="kpi-label">Produits</div></div>',
#             unsafe_allow_html=True
#         )
#     with col3:
#         st.markdown(
#             f'<div class="kpi-card"><div class="kpi-value">{nombre_ventes}</div>'
#             f'<div class="kpi-label">Ventes</div></div>',
#             unsafe_allow_html=True
#         )
#     with col4:
#         st.markdown(
#             f'<div class="kpi-card"><div class="kpi-value">{nombre_clients}</div>'
#             f'<div class="kpi-label">Clients</div></div>',
#             unsafe_allow_html=True
#         )
#     with col5:
#         st.markdown(
#             f'<div class="kpi-card"><div class="kpi-value">{chiffre_affaires:,.0f}</div>'
#             f'<div class="kpi-label">KMF (CA total)</div></div>',
#             unsafe_allow_html=True
#         )

#     # ==========================================
#     # GESTION DES UTILISATEURS
#     # ==========================================

#     utilisateurs = lister_utilisateurs()

#     st.markdown(
#         f'<p class="section-title">👥 Utilisateurs ({len(utilisateurs)})</p>',
#         unsafe_allow_html=True
#     )

#     for utilisateur in utilisateurs:

#         est_soi_meme = utilisateur["id"] == st.session_state.utilisateur_id
#         couleur = "#085041" if utilisateur["role"] == "administrateur" else "#374151"
#         fond = "#E1F5EE" if utilisateur["role"] == "administrateur" else "#F3F4F6"

#         col_info, col_role, col_action = st.columns([4, 2, 1])

#         with col_info:
#             suffixe = " (vous)" if est_soi_meme else ""
#             st.markdown(
#                 f'<div class="ligne-item">'
#                 f'<div>'
#                 f'<div class="nom">👤 {utilisateur["nom"]}{suffixe}</div>'
#                 f'<div class="meta">'
#                 f'{utilisateur["email"]} • {utilisateur["provider"]} • '
#                 f'{utilisateur["date_creation"]}'
#                 f'</div>'
#                 f'</div>'
#                 f'<span class="badge-role" style="color:{couleur};background:{fond};">'
#                 f'{utilisateur["role"]}</span>'
#                 f'</div>',
#                 unsafe_allow_html=True
#             )

#         with col_role:
#             nouveau_role = st.selectbox(
#                 "Rôle",
#                 ROLES,
#                 index=ROLES.index(utilisateur["role"]),
#                 key=f"role_{utilisateur['id']}",
#                 label_visibility="collapsed",
#                 disabled=est_soi_meme
#             )
#             if nouveau_role != utilisateur["role"] and not est_soi_meme:
#                 modifier_role_utilisateur(utilisateur["id"], nouveau_role)
#                 st.session_state["message_admin"] = (
#                     f"Rôle de « {utilisateur['nom']} » changé en {nouveau_role}."
#                 )
#                 st.rerun()

#         with col_action:
#             if est_soi_meme:
#                 st.caption("—")
#             elif st.button(
#                 "🗑️",
#                 key=f"suppr_user_{utilisateur['id']}",
#                 help="Supprimer cet utilisateur"
#             ):
#                 supprimer_utilisateur(utilisateur["id"])
#                 st.session_state["message_admin"] = (
#                     f"Utilisateur « {utilisateur['nom']} » supprimé."
#                 )
#                 st.rerun()
