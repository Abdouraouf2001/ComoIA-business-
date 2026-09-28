from contextlib import closing

import altair as alt
import pandas as pd
import streamlit as st
from database.connexion import obtenir_connexion
from config.colors import (
    BANNIERE_SOUS_TITRE, BORDURE, FOND_CARTE, GRILLE_GRAPHIQUE, OMBRE_CARTE,
    TEXTE_MUET, TEXTE_PRINCIPAL, TEXTE_SECONDAIRE, VERT, VERT_CLAIR, VERT_FONCE,
)
from ml.prediction import (
    analyser_historique,
    obtenir_historique_produit,
    obtenir_ventes_quotidiennes,
    prevoir_chiffre_affaires_moyenne_mobile,
)


def afficher_page_previsions():

    st.markdown(
        f"""
        <style>
        .prev-header {{
            background: linear-gradient(135deg, {VERT}, {VERT_FONCE});
            border-radius: 14px;
            padding: 14px 18px;
            margin-bottom: 14px;
        }}
        .prev-header .titre {{ color: {FOND_CARTE}; font-size: 19px; font-weight: 700; margin: 0; }}
        .prev-header .sous-titre {{ color: {BANNIERE_SOUS_TITRE}; font-size: 12px; margin-top: 2px; }}
        .section-title {{ font-size: 14px; font-weight: 600; margin: 14px 0 8px 0; }}
        .kpi-card {{
            background: {FOND_CARTE};
            border-radius: 12px;
            border: 1px solid {BORDURE};
            box-shadow: 0 1px 6px {OMBRE_CARTE};
            padding: 10px 12px;
        }}
        .kpi-label {{ color: {TEXTE_SECONDAIRE}; font-size: 11px; margin-bottom: 3px; }}
        .kpi-value {{ color: {TEXTE_PRINCIPAL}; font-size: 17px; font-weight: 700; }}
        .kpi-note {{ color: {TEXTE_MUET}; font-size: 10px; margin-top: 2px; }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="prev-header">'
        '<p class="titre">🔮 Prévisions IA</p>'
        '<p class="sous-titre">'
        "Estimation de vos ventes à venir, basée sur votre historique"
        '</p></div>',
        unsafe_allow_html=True
    )

    # ==========================================
    # VÉRIFICATION DE L'HISTORIQUE DISPONIBLE
    # ==========================================

    uid = st.session_state.utilisateur_id
    analyse = analyser_historique(uid)

    if not analyse["disponible"]:
        st.info(f"ℹ️ {analyse['message']}")
        nombre_jours = analyse.get("nombre_jours", 0)
        st.progress(
            min(nombre_jours / 7, 1.0),
            text=f"{nombre_jours} / 7 jours minimum requis"
        )
        return

    # ==========================================
    # PRÉVISION DU CHIFFRE D'AFFAIRES
    # ==========================================

    prevision_7 = prevoir_chiffre_affaires_moyenne_mobile(uid, 7)
    prevision_30 = prevoir_chiffre_affaires_moyenne_mobile(uid, 30)

    st.markdown(
        '<p class="section-title">💰 Chiffre d\'affaires prévu</p>',
        unsafe_allow_html=True
    )

    colonnes = st.columns(3) if prevision_30 else st.columns(2)

    with colonnes[0]:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">Moyenne / jour (7 derniers jours)</div>'
            f'<div class="kpi-value">{prevision_7:,.0f} KMF</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    with colonnes[1]:
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-label">Estimation des 7 prochains jours</div>'
            f'<div class="kpi-value">{prevision_7 * 7:,.0f} KMF</div>'
            f'<div class="kpi-note">7 × moyenne journalière</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    if prevision_30:
        with colonnes[2]:
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-label">Moyenne / jour (30 derniers jours)</div>'
                f'<div class="kpi-value">{prevision_30:,.0f} KMF</div>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.caption(
        "⚠️ Estimation basée sur une simple moyenne mobile de votre "
        "historique récent, pas encore sur un modèle d'apprentissage "
        "automatique — à prendre comme un ordre de grandeur."
    )

    # ==========================================
    # HISTORIQUE + PROJECTION (GRAPHIQUE)
    # ==========================================

    ventes = obtenir_ventes_quotidiennes(uid)
    donnees = pd.DataFrame(ventes).tail(30)
    donnees["jour"] = pd.to_datetime(donnees["jour"])
    donnees["type"] = "Historique"

    dernier_jour = donnees["jour"].max()
    projection = pd.DataFrame({
        "jour": pd.date_range(
            start=dernier_jour, periods=8, freq="D"
        ),
        "chiffre_affaires": [donnees["chiffre_affaires"].iloc[-1]] + [prevision_7] * 7,
        "type": "Projection",
    })

    combine = pd.concat([donnees, projection], ignore_index=True)

    st.markdown(
        '<p class="section-title">📊 30 derniers jours + projection à 7 jours</p>',
        unsafe_allow_html=True
    )

    graphique = alt.Chart(combine).mark_line(interpolate="monotone").encode(
        x=alt.X("jour:T", title=None, axis=alt.Axis(grid=False)),
        y=alt.Y(
            "chiffre_affaires:Q", title=None,
            axis=alt.Axis(grid=True, gridColor=GRILLE_GRAPHIQUE)
        ),
        color=alt.Color(
            "type:N",
            scale=alt.Scale(
                domain=["Historique", "Projection"],
                range=[VERT, VERT_CLAIR]
            ),
            legend=alt.Legend(title=None, orient="top")
        ),
        strokeDash=alt.StrokeDash(
            "type:N",
            scale=alt.Scale(domain=["Historique", "Projection"], range=[[1, 0], [4, 3]])
        ),
        tooltip=[
            alt.Tooltip("jour:T", title="Date", format="%d/%m/%Y"),
            alt.Tooltip("chiffre_affaires:Q", title="CA", format=",.0f"),
            alt.Tooltip("type:N", title="Type"),
        ]
    ).properties(height=200)

    st.altair_chart(graphique, use_container_width=True)

    # ==========================================
    # PRÉVISION PAR PRODUIT
    # ==========================================

    with closing(obtenir_connexion()) as connexion:
        produits = connexion.execute(
            "SELECT id, nom FROM produits WHERE utilisateur_id = ? ORDER BY nom ASC",
            (uid,)
        ).fetchall()

    if produits:
        st.markdown(
            '<p class="section-title">📦 Prévision par produit</p>',
            unsafe_allow_html=True
        )

        noms_produits = {p["nom"]: p["id"] for p in produits}
        produit_choisi = st.selectbox("Produit", list(noms_produits.keys()))
        id_produit = noms_produits[produit_choisi]

        historique_produit = obtenir_historique_produit(uid, id_produit)

        if len(historique_produit) < 7:
            st.info(
                f"Pas assez d'historique de vente pour « {produit_choisi} » "
                "pour estimer une tendance (minimum 7 jours)."
            )
        else:
            df_produit = pd.DataFrame(historique_produit).tail(30)
            df_produit["jour"] = pd.to_datetime(df_produit["jour"])

            moyenne_produit = (
                sum(v["quantite"] for v in historique_produit[-7:]) / 7
            )

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(
                    f'<div class="kpi-card">'
                    f'<div class="kpi-label">Ventes moyennes / jour (7 derniers jours)</div>'
                    f'<div class="kpi-value">{moyenne_produit:.1f} unité(s)</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(
                    f'<div class="kpi-card">'
                    f'<div class="kpi-label">Estimation des 7 prochains jours</div>'
                    f'<div class="kpi-value">{moyenne_produit * 7:.0f} unité(s)</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            barres = alt.Chart(df_produit).mark_bar(color=VERT, cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                x=alt.X("jour:T", title=None, axis=alt.Axis(grid=False)),
                y=alt.Y("quantite:Q", title=None),
                tooltip=[
                    alt.Tooltip("jour:T", title="Date", format="%d/%m/%Y"),
                    alt.Tooltip("quantite:Q", title="Quantité vendue"),
                ]
            ).properties(height=160)

            st.altair_chart(barres, use_container_width=True)