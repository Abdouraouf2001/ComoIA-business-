
from contextlib import closing

import streamlit as st
from config.colors import (
    BORDURE, FOND_CARTE, TEXTE_MUET, TEXTE_PRINCIPAL, TEXTE_SECONDAIRE, VERT,
)
from database.connexion import obtenir_connexion


def afficher_page_ventes():

    st.markdown(
        f"""
        <style>
        .ligne-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: {FOND_CARTE};
            border: 1px solid {BORDURE};
            border-radius: 10px;
            padding: 8px 12px;
            margin-bottom: 6px;
            font-size: 13px;
        }}
        .ligne-item .nom {{ font-weight: 600; color: {TEXTE_PRINCIPAL}; }}
        .ligne-item .meta {{ color: {TEXTE_MUET}; font-size: 11px; }}
        .ligne-item .montant {{ font-weight: 700; color: {VERT}; }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<p style="font-size:20px;font-weight:700;margin-bottom:2px;">'
        '💰 Ventes</p>'
        f'<p style="font-size:13px;color:{TEXTE_SECONDAIRE};margin-bottom:10px;">'
        'Enregistrez et consultez les ventes de votre entreprise.</p>',
        unsafe_allow_html=True
    )

    if "message_vente" in st.session_state:
        st.success(st.session_state.pop("message_vente"))

    with closing(obtenir_connexion()) as connexion:
        produits = connexion.execute(
            "SELECT id, nom, prix_vente, quantite FROM produits "
            "WHERE utilisateur_id = ? ORDER BY nom ASC",
            (st.session_state.utilisateur_id,)
        ).fetchall()

    if not produits:
        st.warning("⚠️ Aucun produit disponible.")
        st.info("Ajoutez d'abord des produits dans la page 📦 Produits.")
        return

    # ==========================================================
    # ENREGISTRER UNE VENTE (repliable)
    # ==========================================================

    with st.expander("🛒 Enregistrer une vente", expanded=True):

        produits_disponibles = {
            p["nom"]: p for p in produits if p["quantite"] > 0
        }

        if not produits_disponibles:
            st.warning(
                "Tous les produits sont en rupture de stock. "
                "Réapprovisionnez avant d'enregistrer une nouvelle vente."
            )
        else:
            produit_selectionne = st.selectbox(
                "Produit", list(produits_disponibles.keys())
            )
            produit = produits_disponibles[produit_selectionne]

            st.caption(
                f"📦 Stock disponible : **{produit['quantite']} unités** "
                f"&nbsp;|&nbsp; 💰 Prix : **{produit['prix_vente']:,.0f} KMF**"
            )

            quantite = st.number_input(
                "Quantité vendue",
                min_value=1,
                max_value=produit["quantite"],
                value=1,
                step=1
            )

            montant_total = produit["prix_vente"] * quantite

            st.markdown(
                f'<p style="font-size:15px;font-weight:600;margin:8px 0;">'
                f'💵 Total : <span style="color:{VERT};">'
                f'{montant_total:,.0f} KMF</span></p>',
                unsafe_allow_html=True
            )

            if st.button("💾 Enregistrer la vente", use_container_width=True):
                if quantite > produit["quantite"]:
                    st.error("❌ Stock insuffisant pour effectuer cette vente.")
                else:
                    with closing(obtenir_connexion()) as connexion:
                        try:
                            connexion.execute(
                                """
                                INSERT INTO ventes
                                (produit_id, quantite, prix_unitaire,
                                 montant_total, utilisateur_id)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (
                                    produit["id"], quantite,
                                    produit["prix_vente"], montant_total,
                                    st.session_state.utilisateur_id
                                )
                            )
                            connexion.execute(
                                "UPDATE produits SET quantite = quantite - ? "
                                "WHERE id = ? AND utilisateur_id = ?",
                                (quantite, produit["id"],
                                 st.session_state.utilisateur_id)
                            )
                            connexion.commit()

                            # st.toast (contrairement à st.success) survit à un
                            # st.rerun() immédiat : il reste visible même si on
                            # change de page dans la foulée.
                            st.toast("✅ Vente enregistrée avec succès !", icon="✅")
                            st.session_state["page_demandee"] = "Clients"
                            st.rerun()

                        except Exception as erreur:
                            connexion.rollback()
                            st.error(f"❌ Une erreur est survenue : {erreur}")

    # ==========================================================
    # HISTORIQUE DES VENTES
    # ==========================================================

    with closing(obtenir_connexion()) as connexion:
        ventes = connexion.execute(
            """
            SELECT
                ventes.id, produits.nom AS produit, ventes.quantite,
                ventes.prix_unitaire, ventes.montant_total, ventes.date_vente
            FROM ventes
            LEFT JOIN produits ON ventes.produit_id = produits.id
            WHERE ventes.utilisateur_id = ?
            ORDER BY ventes.date_vente DESC
            """,
            (st.session_state.utilisateur_id,)
        ).fetchall()

    if not ventes:
        st.info("Aucune vente enregistrée pour le moment.")
        return

    st.markdown(
        f'<p style="font-size:14px;font-weight:600;margin:10px 0 6px;">'
        f'📋 Historique des ventes ({len(ventes)})</p>',
        unsafe_allow_html=True
    )

    for vente in ventes:
        nom_produit = vente["produit"] or "Produit supprimé"
        st.markdown(
            f'<div class="ligne-item">'
            f'<div>'
            f'<div class="nom">🛒 {nom_produit}</div>'
            f'<div class="meta">'
            f'Vente #{vente["id"]} • {vente["quantite"]} unité(s) × '
            f'{vente["prix_unitaire"]:,.0f} KMF • {vente["date_vente"]}'
            f'</div>'
            f'</div>'
            f'<span class="montant">{vente["montant_total"]:,.0f} KMF</span>'
            f'</div>',
            unsafe_allow_html=True
        )

