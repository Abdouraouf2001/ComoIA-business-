
from contextlib import closing

import streamlit as st
from database.connexion import obtenir_connexion


def afficher_page_clients():

    st.markdown(
        """
        <style>
        .ligne-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: white;
            border: 1px solid #EAECEF;
            border-radius: 10px;
            padding: 8px 12px;
            margin-bottom: 6px;
            font-size: 13px;
        }
        .ligne-item .nom { font-weight: 600; color: #111827; }
        .ligne-item .meta { color: #9CA3AF; font-size: 11px; }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<p style="font-size:20px;font-weight:700;margin-bottom:2px;">'
        '👥 Clients</p>'
        '<p style="font-size:13px;color:#6B7280;margin-bottom:10px;">'
        'Gérez les informations de vos clients.</p>',
        unsafe_allow_html=True
    )

    if "message_client" in st.session_state:
        st.success(st.session_state.pop("message_client"))

    # ==========================================================
    # AJOUTER UN CLIENT (repliable)
    # ==========================================================

    with st.expander("➕ Ajouter un client"):

        with st.form("formulaire_client", clear_on_submit=True):

            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input(
                    "Nom du client",
                    placeholder="Exemple : Ahmed Mohamed"
                )
                telephone = st.text_input(
                    "Téléphone",
                    placeholder="Exemple : 33 12 34 56"
                )
            with col2:
                email = st.text_input(
                    "E-mail",
                    placeholder="Exemple : client@gmail.com"
                )
                adresse = st.text_input(
                    "Adresse",
                    placeholder="Exemple : Moroni"
                )

            enregistrer = st.form_submit_button(
                "💾 Enregistrer le client",
                use_container_width=True
            )

        if enregistrer:
            if not nom.strip():
                st.error("Veuillez saisir le nom du client.")
            else:
                with closing(obtenir_connexion()) as connexion:
                    connexion.execute(
                        """
                        INSERT INTO clients (nom, telephone, email, adresse)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            nom.strip(),
                            telephone.strip(),
                            email.strip(),
                            adresse.strip()
                        )
                    )
                    connexion.commit()

                st.session_state["message_client"] = "✅ Client ajouté avec succès !"
                st.rerun()

    # ==========================================================
    # LISTE DES CLIENTS
    # ==========================================================

    with closing(obtenir_connexion()) as connexion:
        clients = connexion.execute(
            """
            SELECT id, nom, telephone, email, adresse, date_creation
            FROM clients
            ORDER BY id DESC
            """
        ).fetchall()

    if not clients:
        st.info("Aucun client enregistré pour le moment.")
        return

    st.markdown(
        f'<p style="font-size:14px;font-weight:600;margin:10px 0 6px;">'
        f'📋 Mes clients ({len(clients)})</p>',
        unsafe_allow_html=True
    )

    # ==========================================================
    # AFFICHAGE COMPACT (une ligne par client)
    # ==========================================================

    for client in clients:

        col_info, col_edit, col_del = st.columns([6, 1, 1])

        with col_info:
            details = " • ".join(
                filter(None, [client["telephone"], client["email"], client["adresse"]])
            )
            st.markdown(
                f'<div class="ligne-item">'
                f'<div>'
                f'<div class="nom">👤 {client["nom"]}</div>'
                f'<div class="meta">{details or "Aucun détail renseigné"}</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_edit:
            if st.button(
                "✏️",
                key=f"modifier_client_{client['id']}",
                help="Modifier le client"
            ):
                st.session_state.client_a_modifier = client["id"]
                st.rerun()

        with col_del:
            if st.button(
                "🗑️",
                key=f"supprimer_client_{client['id']}",
                help="Supprimer le client"
            ):
                with closing(obtenir_connexion()) as connexion:
                    connexion.execute(
                        "DELETE FROM clients WHERE id = ?",
                        (client["id"],)
                    )
                    connexion.commit()

                st.session_state["message_client"] = "Client supprimé."
                st.rerun()

    # ==========================================================
    # MODIFIER UN CLIENT
    # ==========================================================

    if "client_a_modifier" in st.session_state:

        id_client = st.session_state.client_a_modifier

        with closing(obtenir_connexion()) as connexion:
            client = connexion.execute(
                """
                SELECT id, nom, telephone, email, adresse
                FROM clients
                WHERE id = ?
                """,
                (id_client,)
            ).fetchone()

        if client:
            with st.expander(f"✏️ Modifier {client['nom']}", expanded=True):

                with st.form("formulaire_modification_client"):
                    nouveau_nom = st.text_input("Nom du client", value=client["nom"])
                    nouveau_telephone = st.text_input(
                        "Téléphone", value=client["telephone"] or ""
                    )
                    nouvel_email = st.text_input(
                        "E-mail", value=client["email"] or ""
                    )
                    nouvelle_adresse = st.text_input(
                        "Adresse", value=client["adresse"] or ""
                    )

                    col1, col2 = st.columns(2)
                    with col1:
                        enregistrer_modification = st.form_submit_button(
                            "💾 Enregistrer",
                            use_container_width=True
                        )
                    with col2:
                        annuler = st.form_submit_button(
                            "❌ Annuler",
                            use_container_width=True
                        )

                if enregistrer_modification:
                    if not nouveau_nom.strip():
                        st.error("Veuillez saisir le nom du client.")
                    else:
                        with closing(obtenir_connexion()) as connexion:
                            connexion.execute(
                                """
                                UPDATE clients
                                SET nom = ?, telephone = ?, email = ?, adresse = ?
                                WHERE id = ?
                                """,
                                (
                                    nouveau_nom.strip(),
                                    nouveau_telephone.strip(),
                                    nouvel_email.strip(),
                                    nouvelle_adresse.strip(),
                                    id_client
                                )
                            )
                            connexion.commit()

                        del st.session_state.client_a_modifier
                        st.session_state["message_client"] = (
                            "✅ Client modifié avec succès !"
                        )
                        st.rerun()

                if annuler:
                    del st.session_state.client_a_modifier
                    st.rerun()
        else:
            # Le client a été supprimé entre-temps
            del st.session_state.client_a_modifier
