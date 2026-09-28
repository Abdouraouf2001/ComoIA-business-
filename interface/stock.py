from contextlib import closing

import streamlit as st
from config.colors import (
    BORDURE, FOND_CARTE, ORANGE_FOND, ORANGE_FONCE, ROUGE_FOND,
    ROUGE_FONCE, TEXTE_MUET, TEXTE_PRINCIPAL, TEXTE_SECONDAIRE,
    VERT_FOND, VERT_FONCE_TEXTE,
)
from database.connexion import obtenir_connexion


def afficher_page_stock():

    st.markdown(
        f"""
        <style>
        .ligne-item {{
            background: {FOND_CARTE};
            border: 1px solid {BORDURE};
            border-radius: 10px;
            padding: 8px 12px;
            margin-bottom: 6px;
            font-size: 13px;
        }}
        .ligne-item .nom {{ font-weight: 600; color: {TEXTE_PRINCIPAL}; }}
        .ligne-item .meta {{ color: {TEXTE_MUET}; font-size: 11px; }}
        .badge-statut {{
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 999px;
            white-space: nowrap;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<p style="font-size:20px;font-weight:700;margin-bottom:2px;">'
        '📊 Gestion du stock</p>'
        f'<p style="font-size:13px;color:{TEXTE_SECONDAIRE};margin-bottom:10px;">'
        'Suivez les quantités disponibles et identifiez rapidement '
        'les produits à réapprovisionner.</p>',
        unsafe_allow_html=True
    )

    if "message_stock" in st.session_state:
        st.success(st.session_state.pop("message_stock"))

    with closing(obtenir_connexion()) as connexion:
        produits = connexion.execute(
            """
            SELECT id, nom, categorie, prix_achat, prix_vente,
                   quantite, seuil_alerte
            FROM produits
            WHERE utilisateur_id = ?
            ORDER BY nom ASC
            """,
            (st.session_state.utilisateur_id,)
        ).fetchall()

    if not produits:
        st.info(
            "📦 Aucun produit disponible. "
            "Ajoutez d'abord des produits dans la section Produits."
        )
        return

    # ==========================================
    # STATISTIQUES
    # ==========================================

    total_produits = len(produits)
    stock_faible = sum(
        1 for produit in produits
        if produit["quantite"] <= produit["seuil_alerte"]
    )
    stock_total = sum(produit["quantite"] for produit in produits)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📦 Produits", total_produits)
    with col2:
        st.metric("📊 Quantité totale", stock_total)
    with col3:
        st.metric("⚠️ Stock faible", stock_faible)

    # ==========================================
    # RECHERCHE
    # ==========================================

    recherche = st.text_input(
        "🔎 Rechercher un produit",
        placeholder="Exemple : Riz"
    )

    produits_affiches = produits
    if recherche.strip():
        terme = recherche.strip().lower()
        produits_affiches = [
            produit for produit in produits
            if terme in produit["nom"].lower()
            or (produit["categorie"] and terme in produit["categorie"].lower())
        ]

    st.markdown(
        f'<p style="font-size:14px;font-weight:600;margin:10px 0 6px;">'
        f'📋 État du stock ({len(produits_affiches)})</p>',
        unsafe_allow_html=True
    )

    if not produits_affiches:
        st.warning("Aucun produit ne correspond à votre recherche.")
        return

    # ==========================================
    # LISTE COMPACTE
    # ==========================================

    for produit in produits_affiches:
        quantite = produit["quantite"]
        seuil = produit["seuil_alerte"]

        if quantite == 0:
            statut, couleur, fond = "Rupture", ROUGE_FONCE, ROUGE_FOND
        elif quantite <= seuil:
            statut, couleur, fond = "Stock faible", ORANGE_FONCE, ORANGE_FOND
        else:
            statut, couleur, fond = "Disponible", VERT_FONCE_TEXTE, VERT_FOND

        col_info, col_qte, col_action = st.columns([4, 2, 2])

        with col_info:
            categorie_txt = (
                f' • {produit["categorie"]}' if produit["categorie"] else ""
            )
            st.markdown(
                f'<div class="ligne-item">'
                f'<div class="nom">📦 {produit["nom"]}{categorie_txt}</div>'
                f'<div class="meta">Seuil d\'alerte : {seuil}</div>'
                f'<span class="badge-statut" '
                f'style="color:{couleur};background:{fond};">{statut}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_qte:
            nouvelle_quantite = st.number_input(
                "Quantité",
                min_value=0,
                value=int(quantite),
                step=1,
                key=f"stock_{produit['id']}",
                label_visibility="collapsed"
            )

        with col_action:
            if st.button(
                "💾 Mettre à jour",
                key=f"maj_stock_{produit['id']}",
                use_container_width=True
            ):
                with closing(obtenir_connexion()) as connexion:
                    connexion.execute(
                        "UPDATE produits SET quantite = ? "
                        "WHERE id = ? AND utilisateur_id = ?",
                        (nouvelle_quantite, produit["id"],
                         st.session_state.utilisateur_id)
                    )
                    connexion.commit()

                st.session_state["message_stock"] = (
                    f"Stock de « {produit['nom']} » mis à jour."
                )
                st.rerun()
