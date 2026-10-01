import base64
from contextlib import closing

import streamlit as st
from config.colors import (
    BORDURE, FOND_CARTE, TEXTE_MUET, TEXTE_PRINCIPAL, TEXTE_SECONDAIRE, VERT,
)
from database.connexion import obtenir_connexion
from fonctions.vente import creer_vente, generer_pdf_recu


def _apercu_imprimable(pdf_bytes, cle):
    """PDF affiché dans la page, avec la barre d'outils du lecteur du
    navigateur (zoom, impression) — pas besoin de télécharger d'abord."""
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{pdf_base64}" '
        f'width="100%" height="500" '
        f'style="border:1px solid {BORDURE};border-radius:10px;" '
        f'title="apercu_recu_{cle}"></iframe>',
        unsafe_allow_html=True
    )


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

    uid = st.session_state.utilisateur_id

    # ==========================================================
    # REÇU DE LA DERNIÈRE VENTE (affiché tant qu'on n'a pas continué)
    # ==========================================================

    if "derniere_vente_ids" in st.session_state:

        st.success("✅ Vente enregistrée avec succès !")

        pdf_bytes = generer_pdf_recu(
            st.session_state["derniere_vente_ids"], uid
        )

        if pdf_bytes:
            col_telecharger, col_continuer = st.columns(2)
            with col_telecharger:
                st.download_button(
                    "📄 Télécharger le reçu",
                    data=pdf_bytes,
                    file_name=f"recu_{st.session_state['derniere_vente_ids'][0]}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="telecharger_recu"
                )
            with col_continuer:
                if st.button(
                    "➡️ Continuer vers Clients",
                    use_container_width=True,
                    type="primary",
                    key="continuer_vers_clients"
                ):
                    st.session_state.pop("derniere_vente_ids", None)
                    st.session_state["page_demandee"] = "Clients"
                    st.rerun()

            if st.toggle("🖨️ Aperçu et impression", key="apercu_recu"):
                st.caption(
                    "Utilisez l'icône imprimante de la barre d'outils "
                    "ci-dessous (ou Ctrl+P) pour imprimer directement."
                )
                _apercu_imprimable(pdf_bytes, "derniere")
        else:
            if st.button("➡️ Continuer vers Clients", use_container_width=True):
                st.session_state.pop("derniere_vente_ids", None)
                st.session_state["page_demandee"] = "Clients"
                st.rerun()

        st.divider()

    # ==========================================================
    # ENREGISTRER UNE VENTE (repliable)
    # ==========================================================

    with closing(obtenir_connexion()) as connexion:
        produits = connexion.execute(
            "SELECT id, nom, prix_vente, quantite FROM produits "
            "WHERE utilisateur_id = ? ORDER BY nom ASC",
            (uid,)
        ).fetchall()

    if not produits:
        st.warning("⚠️ Aucun produit disponible.")
        st.info("Ajoutez d'abord des produits dans la page 📦 Produits.")
        return

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

                articles = [{
                    "produit_id": produit["id"],
                    "nom": produit["nom"],
                    "quantite": quantite,
                    "prix_unitaire": produit["prix_vente"],
                    "montant": montant_total,
                }]

                succes, message, ids_ventes = creer_vente(articles, uid)

                if succes:
                    st.session_state["derniere_vente_ids"] = ids_ventes
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

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
            (uid,)
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
        col_info, col_pdf = st.columns([5, 1])

        with col_info:
            st.markdown(
                f'<div class="ligne-item">'
                f'<div>'
                f'<div class="nom">🛒 {nom_produit}</div>'
                f'<div class="meta">'
                f'Vente #{vente["id"]} · {vente["quantite"]} unité(s) × '
                f'{vente["prix_unitaire"]:,.0f} KMF · {vente["date_vente"]}'
                f'</div>'
                f'</div>'
                f'<span class="montant">{vente["montant_total"]:,.0f} KMF</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_pdf:
            recu = generer_pdf_recu([vente["id"]], uid)
            if recu:
                st.download_button(
                    "📄", data=recu, file_name=f"recu_{vente['id']}.pdf",
                    mime="application/pdf", key=f"recu_{vente['id']}",
                    help="Télécharger le reçu"
                )
