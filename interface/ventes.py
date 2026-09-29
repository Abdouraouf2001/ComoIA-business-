
import base64
from contextlib import closing

import streamlit as st
from config.colors import (
    BORDURE, FOND_CARTE, TEXTE_MUET, TEXTE_PRINCIPAL, TEXTE_SECONDAIRE, VERT,
)
from database.connexion import obtenir_connexion
from fonctions.ventes import creer_vente, generer_pdf_recu


def afficher_apercu_recu(pdf_bytes: bytes, cle: str):
    """Affiche le reçu PDF dans un iframe pour impression."""
    if not pdf_bytes:
        st.error("Impossible de générer le reçu.")
        return
    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{pdf_base64}" '
        f'width="100%" height="480" '
        f'style="border:1px solid {BORDURE};border-radius:10px;" '
        f'title="recu_{cle}"></iframe>',
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
        'Enregistrez une vente et imprimez le reçu.</p>',
        unsafe_allow_html=True
    )

    # Message de succès
    if "message_vente" in st.session_state:
        st.success(st.session_state.pop("message_vente"))

    uid = st.session_state.utilisateur_id

    # Initialisation du panier
    if "articles_vente" not in st.session_state:
        st.session_state.articles_vente = []

    # Chargement des produits
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

    # ==========================================================
    # ENREGISTRER UNE VENTE
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
                "Produit", list(produits_disponibles.keys()), key="sel_produit_vente"
            )
            produit = produits_disponibles[produit_selectionne]

            st.caption(
                f"📦 Stock disponible : **{produit['quantite']} unités** "
                f"&nbsp;|&nbsp; 💰 Prix : **{produit['prix_vente']:,.0f} KMF**"
            )

            col1, col2 = st.columns([2, 1])
            with col1:
                quantite = st.number_input(
                    "Quantité",
                    min_value=1,
                    max_value=int(produit["quantite"]),
                    value=1,
                    step=1,
                    key="qte_vente"
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("➕ Ajouter", use_container_width=True):
                    # Fusion si le produit est déjà dans le panier
                    deja = False
                    for art in st.session_state.articles_vente:
                        if art["produit_id"] == produit["id"]:
                            deja = True
                            nouvelle_qte = art["quantite"] + quantite
                            if nouvelle_qte > produit["quantite"]:
                                st.error(
                                    f"Stock insuffisant "
                                    f"(disponible : {produit['quantite']})."
                                )
                            else:
                                art["quantite"] = nouvelle_qte
                                art["montant"] = nouvelle_qte * art["prix_unitaire"]
                                st.success("Quantité mise à jour.")
                            break

                    if not deja:
                        st.session_state.articles_vente.append({
                            "produit_id": produit["id"],
                            "nom": produit["nom"],
                            "quantite": quantite,
                            "prix_unitaire": produit["prix_vente"],
                            "montant": quantite * produit["prix_vente"]
                        })
                        st.success(f"{produit['nom']} ajouté.")

        # ---------- Panier ----------
        articles = st.session_state.articles_vente

        if articles:
            st.markdown("---")
            st.markdown("**🧾 Articles de la vente**")

            total = 0
            for i, art in enumerate(articles):
                total += art["montant"]
                c1, c2, c3, c4 = st.columns([3, 1, 1.5, 0.6])
                with c1:
                    st.write(f"**{art['nom']}**")
                with c2:
                    st.write(f"{art['quantite']}")
                with c3:
                    st.write(f"{art['montant']:,.0f} KMF")
                with c4:
                    if st.button("🗑️", key=f"suppr_v_{i}"):
                        st.session_state.articles_vente.pop(i)
                        st.rerun()

            st.markdown(
                f'<p style="font-size:15px;font-weight:600;margin:8px 0;">'
                f'💵 Total : <span style="color:{VERT};">'
                f'{total:,.0f} KMF</span></p>',
                unsafe_allow_html=True
            )

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🧹 Vider le panier", use_container_width=True):
                    st.session_state.articles_vente = []
                    st.rerun()
            with col_b:
                if st.button(
                    "💾 Enregistrer la vente",
                    use_container_width=True,
                    type="primary"
                ):
                    succes, message, ids_ventes = creer_vente(
                        articles=articles,
                        utilisateur_id=uid
                    )
                    if succes:
                        st.session_state.articles_vente = []
                        st.session_state["message_vente"] = f"✅ {message}"
                        st.session_state["derniers_ids_ventes"] = ids_ventes
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")

    # ==========================================================
    # REÇU DE LA DERNIÈRE VENTE
    # ==========================================================
    if "derniers_ids_ventes" in st.session_state:
        ids = st.session_state["derniers_ids_ventes"]
        pdf_bytes = generer_pdf_recu(ids, uid)

        if pdf_bytes:
            st.markdown("---")
            st.markdown("### 🧾 Reçu de la vente")

            st.download_button(
                "📄 Télécharger le reçu",
                data=pdf_bytes,
                file_name="recu_vente.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="dl_recu_vente"
            )

            with st.expander("🖨️ Aperçu et impression"):
                st.caption("Utilisez l'icône imprimante du lecteur PDF ou Ctrl+P.")
                afficher_apercu_recu(pdf_bytes, "dernier")

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
            LIMIT 50
            """,
            (uid,)
        ).fetchall()

    if not ventes:
        st.info("Aucune vente enregistrée pour le moment.")
        return

    st.markdown(
        f'<p style="font-size:14px;font-weight:600;margin:16px 0 6px;">'
        f'📋 Historique des ventes ({len(ventes)})</p>',
        unsafe_allow_html=True
    )

    for vente in ventes:
        nom_produit = vente["produit"] or "Produit supprimé"

        with st.container():
            col1, col2 = st.columns([5, 1])
            with col1:
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
            with col2:
                # Bouton reçu individuel
                pdf_bytes = generer_pdf_recu([vente["id"]], uid)
                if pdf_bytes:
                    st.download_button(
                        "🧾",
                        data=pdf_bytes,
                        file_name=f"recu_{vente['id']}.pdf",
                        mime="application/pdf",
                        key=f"recu_h_{vente['id']}",
                        help="Télécharger le reçu"
                    )
