
import textwrap

import pandas as pd
import altair as alt
import streamlit as st
from config.colors import (
    BANNIERE_SOUS_TITRE,
    BORDURE,
    FOND_CARTE,
    GRILLE_GRAPHIQUE,
    JAUNE_BORDURE,
    JAUNE_FOND,
    OMBRE_CARTE,
    ROUGE,
    ROUGE_FOND,
    TEXTE_MUET,
    TEXTE_PRINCIPAL,
    TEXTE_SECONDAIRE,
    VERT,
    VERT_CLAIR,
    VERT_FOND,
    VERT_FONCE,
)
from database.connexion import obtenir_connexion


def afficher_page_accueil():

    connexion = obtenir_connexion()
    uid = st.session_state.utilisateur_id

    # ==========================================
    # STATISTIQUES
    # ==========================================

    chiffre_affaires = connexion.execute(
        "SELECT COALESCE(SUM(montant_total), 0) FROM ventes WHERE utilisateur_id = ?",
        (uid,)
    ).fetchone()[0]

    total_depenses = connexion.execute(
        "SELECT COALESCE(SUM(montant), 0) FROM depenses WHERE utilisateur_id = ?",
        (uid,)
    ).fetchone()[0]

    benefice = chiffre_affaires - total_depenses

    nombre_produits = connexion.execute(
        "SELECT COUNT(*) FROM produits WHERE utilisateur_id = ?", (uid,)
    ).fetchone()[0]

    nombre_clients = connexion.execute(
        "SELECT COUNT(*) FROM clients WHERE utilisateur_id = ?", (uid,)
    ).fetchone()[0]

    stocks_faibles = connexion.execute(
        "SELECT COUNT(*) FROM produits "
        "WHERE quantite <= seuil_alerte AND utilisateur_id = ?", (uid,)
    ).fetchone()[0]

    # CA du jour
    ca_jour = connexion.execute(
        """
        SELECT COALESCE(SUM(montant_total), 0)
        FROM ventes
        WHERE date(date_vente) = date('now', 'localtime')
          AND utilisateur_id = ?
        """,
        (uid,)
    ).fetchone()[0]

    # Comparatif mois
    ca_mois = connexion.execute(
        """
        SELECT COALESCE(SUM(montant_total), 0)
        FROM ventes
        WHERE date(date_vente) >= date('now', 'localtime', 'start of month')
          AND utilisateur_id = ?
        """,
        (uid,)
    ).fetchone()[0]

    ca_mois_dernier = connexion.execute(
        """
        SELECT COALESCE(SUM(montant_total), 0)
        FROM ventes
        WHERE date(date_vente)
              >= date('now', 'localtime', 'start of month', '-1 month')
          AND date(date_vente) < date('now', 'localtime', 'start of month')
          AND utilisateur_id = ?
        """,
        (uid,)
    ).fetchone()[0]

    dep_mois = connexion.execute(
        """
        SELECT COALESCE(SUM(montant), 0)
        FROM depenses
        WHERE date(date_depense) >= date('now', 'localtime', 'start of month')
          AND utilisateur_id = ?
        """,
        (uid,)
    ).fetchone()[0]

    dep_mois_dernier = connexion.execute(
        """
        SELECT COALESCE(SUM(montant), 0)
        FROM depenses
        WHERE date(date_depense)
              >= date('now', 'localtime', 'start of month', '-1 month')
          AND date(date_depense) < date('now', 'localtime', 'start of month')
          AND utilisateur_id = ?
        """,
        (uid,)
    ).fetchone()[0]

    benefice_mois = ca_mois - dep_mois
    benefice_mois_dernier = ca_mois_dernier - dep_mois_dernier

    def variation_pct(valeur_actuelle, valeur_precedente):
        if valeur_precedente == 0:
            return None
        return (valeur_actuelle - valeur_precedente) / abs(valeur_precedente) * 100

    # Ventes 30 jours
    ventes_par_jour = connexion.execute(
        """
        SELECT date(date_vente) AS jour, SUM(montant_total) AS total
        FROM ventes
        WHERE date(date_vente) >= date('now', 'localtime', '-29 days')
          AND utilisateur_id = ?
        GROUP BY jour
        ORDER BY jour
        """,
        (uid,)
    ).fetchall()

    # Top 5 produits
    top_produits = connexion.execute(
        """
        SELECT
            produits.nom AS produit,
            SUM(ventes.quantite) AS quantite_vendue
        FROM ventes
        LEFT JOIN produits ON ventes.produit_id = produits.id
        WHERE ventes.utilisateur_id = ?
        GROUP BY produits.id, produits.nom
        ORDER BY quantite_vendue DESC
        LIMIT 5
        """,
        (uid,)
    ).fetchall()

    # Stock faible
    produits_faibles = connexion.execute(
        """
        SELECT nom, quantite, seuil_alerte
        FROM produits
        WHERE quantite <= seuil_alerte AND utilisateur_id = ?
        ORDER BY quantite ASC
        LIMIT 5
        """,
        (uid,)
    ).fetchall()

    # Ventes récentes
    ventes_recentes = connexion.execute(
        """
        SELECT ventes.montant_total, ventes.date_vente, produits.nom
        FROM ventes
        LEFT JOIN produits ON ventes.produit_id = produits.id
        WHERE ventes.utilisateur_id = ?
        ORDER BY ventes.id DESC
        LIMIT 5
        """,
        (uid,)
    ).fetchall()

    connexion.close()

    # ==========================================
    # STYLE
    # ==========================================

    st.markdown(
        textwrap.dedent(
            f"""
            <style>
            .db-header {{
                background: linear-gradient(135deg, {VERT} 0%, {VERT_FONCE} 100%);
                border-radius: 16px;
                padding: 18px 20px;
                margin-bottom: 18px;
                box-shadow: 0 4px 14px rgba(0,0,0,0.08);
            }}
            .db-header .titre {{
                color: {FOND_CARTE};
                font-size: 22px;
                font-weight: 700;
                margin: 0;
                text-align: center;
            }}
            .db-header .sous-titre {{
                color: {BANNIERE_SOUS_TITRE};
                font-size: 13px;
                margin-top: 4px;
                opacity: 0.95;
                text-align: center;
            }}
            .section-title {{
                color: {TEXTE_PRINCIPAL};
                font-size: 15px;
                font-weight: 700;
                margin: 20px 0 10px 0;
            }}
            .kpi-card {{
                background: {FOND_CARTE};
                border-radius: 14px;
                border: 1px solid {BORDURE};
                box-shadow: 0 2px 8px {OMBRE_CARTE};
                padding: 14px 14px;
                min-height: 100px;
                transition: transform 0.15s ease;
            }}
            .kpi-icon {{
                width: 28px;
                height: 28px;
                border-radius: 8px;
                background: {VERT_FOND};
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                margin-bottom: 8px;
            }}
            .kpi-label {{
                color: {TEXTE_SECONDAIRE};
                font-size: 11px;
                font-weight: 500;
                margin-bottom: 3px;
            }}
            .kpi-value {{
                color: {TEXTE_PRINCIPAL};
                font-size: 17px;
                font-weight: 700;
                margin-bottom: 5px;
            }}
            .trend-badge {{
                display: inline-block;
                font-size: 10px;
                font-weight: 600;
                padding: 2px 8px;
                border-radius: 999px;
            }}
            .stat-mini {{
                background: {FOND_CARTE};
                border-radius: 12px;
                border: 1px solid {BORDURE};
                padding: 12px 10px;
                text-align: center;
                box-shadow: 0 1px 4px {OMBRE_CARTE};
            }}
            .stat-mini .valeur {{
                font-size: 18px;
                font-weight: 700;
                color: {TEXTE_PRINCIPAL};
            }}
            .stat-mini .libelle {{
                font-size: 11px;
                color: {TEXTE_SECONDAIRE};
                margin-top: 2px;
            }}
            .alert-card {{
                background-color: {JAUNE_FOND};
                padding: 10px 14px;
                border-radius: 10px;
                border: 1px solid {JAUNE_BORDURE};
                margin-bottom: 8px;
                font-size: 13px;
            }}
            .vente-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: {FOND_CARTE};
                border: 1px solid {BORDURE};
                border-radius: 10px;
                padding: 10px 14px;
                margin-bottom: 7px;
            }}
            .vente-row .nom {{ font-weight: 600; color: {TEXTE_PRINCIPAL}; font-size: 13px; }}
            .vente-row .date {{ color: {TEXTE_MUET}; font-size: 11px; }}
            .vente-row .montant {{ font-weight: 700; color: {VERT}; font-size: 13px; }}
            .action-btn {{
                background: {FOND_CARTE};
                border: 1px solid {BORDURE};
                border-radius: 12px;
                padding: 14px 10px;
                text-align: center;
                font-size: 13px;
                font-weight: 600;
                color: {TEXTE_PRINCIPAL};
                box-shadow: 0 1px 4px {OMBRE_CARTE};
            }}
            @media (max-width: 640px) {{
                .db-header {{ padding: 14px 16px; }}
                .db-header .titre {{ font-size: 18px; }}
                .kpi-card {{ min-height: auto; padding: 12px; }}
                .kpi-value {{ font-size: 15px; }}
            }}
            </style>
            """
        ),
        unsafe_allow_html=True
    )

    # ==========================================
    # HELPERS
    # ==========================================

    def carte_kpi(icone, label, valeur, variation=None, inverse=False):
        badge = ""
        if variation is not None:
            positif = variation >= 0
            bon = positif if not inverse else not positif
            couleur = VERT if bon else ROUGE
            fond = VERT_FOND if bon else ROUGE_FOND
            fleche = "▲" if positif else "▼"
            badge = (
                f'<span class="trend-badge" '
                f'style="color:{couleur};background:{fond};">'
                f'{fleche} {abs(variation):.1f}% vs mois dernier</span>'
            )
        st.markdown(
            f'<div class="kpi-card">'
            f'<div class="kpi-icon">{icone}</div>'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{valeur}</div>'
            f'{badge}'
            f'</div>',
            unsafe_allow_html=True
        )

    def carte_mini(valeur, libelle):
        st.markdown(
            f'<div class="stat-mini">'
            f'<div class="valeur">{valeur}</div>'
            f'<div class="libelle">{libelle}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ==========================================
    # EN-TÊTE
    # ==========================================

    st.markdown(
        '<div class="db-header">'
        '<p class="titre">Tableau de bord</p>'
        '<p class="sous-titre">Vue générale de votre activité commerciale</p>'
        '</div>',
        unsafe_allow_html=True
    )

    # ==========================================
    # KPI PRINCIPAUX
    # ==========================================

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        carte_kpi(
            "💰", "CA de ce mois", f"{ca_mois:,.0f} KMF",
            variation_pct(ca_mois, ca_mois_dernier)
        )
    with col2:
        carte_kpi(
            "💳", "Dépenses de ce mois", f"{dep_mois:,.0f} KMF",
            variation_pct(dep_mois, dep_mois_dernier), inverse=True
        )
    with col3:
        carte_kpi(
            "📈", "Bénéfice de ce mois", f"{benefice_mois:,.0f} KMF",
            variation_pct(benefice_mois, benefice_mois_dernier)
        )
    with col4:
        carte_kpi("☀️", "CA du jour", f"{ca_jour:,.0f} KMF")

    # ==========================================
    # CHIFFRES CLÉS
    # ==========================================

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        carte_mini(nombre_produits, "📦 Produits")
    with col2:
        carte_mini(nombre_clients, "👥 Clients")
    with col3:
        carte_mini(stocks_faibles, "⚠️ Stock faible")
    with col4:
        carte_mini(f"{benefice:,.0f}", "🏦 Bénéfice total")

    # ==========================================
    # ACTIONS RAPIDES
    # ==========================================

    st.markdown(
        '<div class="section-title">⚡ Actions rapides</div>',
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🛒 Nouvelle vente", use_container_width=True):
            st.session_state["menu_force"] = "Ventes"
            st.rerun()
    with c2:
        if st.button("🧾 Nouvelle facture", use_container_width=True):
            st.session_state["menu_force"] = "Facturation"
            st.rerun()
    with c3:
        if st.button("📦 Ajouter produit", use_container_width=True):
            st.session_state["menu_force"] = "Produits"
            st.rerun()
    with c4:
        if st.button("👥 Ajouter client", use_container_width=True):
            st.session_state["menu_force"] = "Clients"
            st.rerun()

    # ==========================================
    # GRAPHIQUE 30 JOURS
    # ==========================================

    st.markdown(
        '<div class="section-title">📊 Ventes des 30 derniers jours</div>',
        unsafe_allow_html=True
    )

    jours = pd.date_range(end=pd.Timestamp.now().normalize(), periods=30)
    totaux_par_jour = {ligne["jour"]: ligne["total"] for ligne in ventes_par_jour}
    valeurs = [totaux_par_jour.get(jour.strftime("%Y-%m-%d"), 0) for jour in jours]

    if any(valeurs):
        df_ventes = pd.DataFrame({"jour": jours, "ventes": valeurs})

        graphique = alt.Chart(df_ventes).mark_area(
            line={"color": VERT, "size": 2.5},
            color=alt.Gradient(
                gradient="linear",
                stops=[
                    alt.GradientStop(color="white", offset=0),
                    alt.GradientStop(color=VERT, offset=1),
                ],
                x1=1, x2=1, y1=1, y2=0
            ),
            opacity=0.18,
            interpolate="monotone"
        ).encode(
            x=alt.X("jour:T", title=None, axis=alt.Axis(grid=False, format="%d/%m")),
            y=alt.Y(
                "ventes:Q", title=None,
                axis=alt.Axis(grid=True, gridColor=GRILLE_GRAPHIQUE)
            ),
            tooltip=[
                alt.Tooltip("jour:T", title="Date", format="%d/%m/%Y"),
                alt.Tooltip("ventes:Q", title="Ventes", format=",.0f"),
            ]
        ).properties(height=180)

        st.altair_chart(graphique, use_container_width=True)
    else:
        st.info("Aucune vente enregistrée sur les 30 derniers jours.")

    # ==========================================
    # DEUX COLONNES : TOP PRODUITS + STOCK FAIBLE
    # ==========================================

    col_gauche, col_droite = st.columns(2)

    with col_gauche:
        st.markdown(
            '<div class="section-title">🏆 Top 5 des produits</div>',
            unsafe_allow_html=True
        )

        if top_produits:
            noms = [p["produit"] or "Produit supprimé" for p in top_produits]
            quantites = [p["quantite_vendue"] or 0 for p in top_produits]
            df_top = pd.DataFrame({"produit": noms, "quantite": quantites})

            barres = alt.Chart(df_top).mark_bar(
                cornerRadiusTopRight=6, cornerRadiusBottomRight=6
            ).encode(
                x=alt.X("quantite:Q", title=None, axis=None),
                y=alt.Y("produit:N", sort="-x", title=None),
                color=alt.Color(
                    "quantite:Q",
                    scale=alt.Scale(range=[VERT_CLAIR, VERT]),
                    legend=None
                ),
                tooltip=[
                    alt.Tooltip("produit:N", title="Produit"),
                    alt.Tooltip("quantite:Q", title="Quantité vendue"),
                ]
            ).properties(height=180)

            st.altair_chart(barres, use_container_width=True)
        else:
            st.info("Aucune vente enregistrée.")

    with col_droite:
        st.markdown(
            '<div class="section-title">⚠️ Stock faible</div>',
            unsafe_allow_html=True
        )

        if produits_faibles:
            for produit in produits_faibles:
                st.markdown(
                    f'<div class="alert-card">'
                    f'<strong>📦 {produit["nom"]}</strong><br>'
                    f'Stock : <b>{produit["quantite"]}</b> '
                    f'&nbsp;•&nbsp; Seuil : {produit["seuil_alerte"]}'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.success("✅ Aucun produit en stock faible.")

    # ==========================================
    # VENTES RÉCENTES
    # ==========================================

    st.markdown(
        '<div class="section-title">💰 Dernières ventes</div>',
        unsafe_allow_html=True
    )

    if ventes_recentes:
        for vente in ventes_recentes:
            nom_produit = vente["nom"] or "Produit supprimé"
            st.markdown(
                f'<div class="vente-row">'
                f'<div><div class="nom">🛒 {nom_produit}</div>'
                f'<div class="date">{vente["date_vente"]}</div></div>'
                f'<div class="montant">{vente["montant_total"]:,.0f} KMF</div>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("Aucune vente enregistrée pour le moment.")
