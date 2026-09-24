from contextlib import closing

import streamlit as st
from database.connexion import obtenir_connexion

CATEGORIES = [
    "Marchandises", "Transport", "Loyer", "Électricité", "Internet",
    "Salaires", "Matériel", "Maintenance", "Marketing", "Autre",
]


def afficher_page_depenses():

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
        .ligne-item .montant { font-weight: 700; color: #D64545; }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<p style="font-size:20px;font-weight:700;margin-bottom:2px;">'
        '💳 Dépenses</p>'
        '<p style="font-size:13px;color:#6B7280;margin-bottom:10px;">'
        'Enregistrez et suivez les dépenses de votre entreprise.</p>',
        unsafe_allow_html=True
    )

    if "message_depense" in st.session_state:
        st.success(st.session_state.pop("message_depense"))

    # ==========================================================
    # ENREGISTRER UNE DÉPENSE (repliable)
    # ==========================================================

    with st.expander("➕ Enregistrer une dépense"):

        with st.form("formulaire_depense", clear_on_submit=True):

            col1, col2 = st.columns(2)
            with col1:
                description = st.text_input(
                    "Description",
                    placeholder="Exemple : Achat de marchandises"
                )
                categorie = st.selectbox("Catégorie", CATEGORIES)
            with col2:
                montant = st.number_input(
                    "Montant (KMF)",
                    min_value=0.0,
                    step=100.0
                )

            enregistrer = st.form_submit_button(
                "💾 Enregistrer la dépense",
                use_container_width=True
            )

        if enregistrer:
            if not description.strip():
                st.error("Veuillez saisir une description.")
            elif montant <= 0:
                st.error("Le montant doit être supérieur à 0.")
            else:
                with closing(obtenir_connexion()) as connexion:
                    connexion.execute(
                        """
                        INSERT INTO depenses (description, montant, categorie)
                        VALUES (?, ?, ?)
                        """,
                        (description.strip(), montant, categorie)
                    )
                    connexion.commit()

                st.session_state["message_depense"] = (
                    "✅ Dépense enregistrée avec succès !"
                )
                st.rerun()

    # ==========================================================
    # HISTORIQUE DES DÉPENSES
    # ==========================================================

    with closing(obtenir_connexion()) as connexion:
        depenses = connexion.execute(
            """
            SELECT id, description, montant, categorie, date_depense
            FROM depenses
            ORDER BY date_depense DESC
            """
        ).fetchall()

    if not depenses:
        st.info("Aucune dépense enregistrée pour le moment.")
        return

    total_depenses = sum(depense["montant"] for depense in depenses)

    st.markdown(
        f'<p style="font-size:14px;font-weight:600;margin:10px 0 6px;">'
        f'📋 Historique ({len(depenses)}) • Total '
        f'<span style="color:#D64545;">{total_depenses:,.0f} KMF</span></p>',
        unsafe_allow_html=True
    )

    for depense in depenses:

        col_info, col_del = st.columns([6, 1])

        with col_info:
            st.markdown(
                f'<div class="ligne-item">'
                f'<div>'
                f'<div class="nom">💸 {depense["description"]}</div>'
                f'<div class="meta">'
                f'{depense["categorie"]} • {depense["date_depense"]}'
                f'</div>'
                f'</div>'
                f'<span class="montant">-{depense["montant"]:,.0f} KMF</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_del:
            if st.button(
                "🗑️",
                key=f"supprimer_depense_{depense['id']}",
                help="Supprimer cette dépense"
            ):
                with closing(obtenir_connexion()) as connexion:
                    connexion.execute(
                        "DELETE FROM depenses WHERE id = ?",
                        (depense["id"],)
                    )
                    connexion.commit()

                st.session_state["message_depense"] = "Dépense supprimée."
                st.rerun()

