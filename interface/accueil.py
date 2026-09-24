import textwrap

import pandas as pd
import altair as alt
import streamlit as st
from database.connexion import obtenir_connexion

VERT = "#00843D"
VERT_CLAIR = "#A8D5BA"
ROUGE = "#D64545"


def afficher_page_accueil():

    connexion = obtenir_connexion()

    # ==========================================
    # STATISTIQUES GÉNÉRALES
    # ==========================================

    chiffre_affaires = connexion.execute(
        "SELECT COALESCE(SUM(montant_total), 0) FROM ventes"
    ).fetchone()[0]

    total_depenses = connexion.execute(
        "SELECT COALESCE(SUM(montant), 0) FROM depenses"
    ).fetchone()[0]

    benefice = chiffre_affaires - total_depenses

    nombre_produits = connexion.execute(
        "SELECT COUNT(*) FROM produits"
    ).fetchone()[0]

    nombre_clients = connexion.execute(
        "SELECT COUNT(*) FROM clients"
    ).fetchone()[0]

    stocks_faibles = connexion.execute(
        "SELECT COUNT(*) FROM produits WHERE quantite <= seuil_alerte"
    ).fetchone()[0]

    # ==========================================
    # COMPARATIF : CE MOIS-CI VS MOIS DERNIER
    # ==========================================

    ca_mois = connexion.execute(
        """
        SELECT COALESCE(SUM(montant_total), 0)
        FROM ventes
        WHERE date(date_vente) >= date('now', 'localtime', 'start of month')
        """
    ).fetchone()[0]

    ca_mois_dernier = connexion.execute(
        """
        SELECT COALESCE(SUM(montant_total), 0)
        FROM ventes
        WHERE date(date_vente)
              >= date('now', 'localtime', 'start of month', '-1 month')
          AND date(date_vente) < date('now', 'localtime', 'start of month')
        """
    ).fetchone()[0]

    dep_mois = connexion.execute(
        """
        SELECT COALESCE(SUM(montant), 0)
        FROM depenses
        WHERE date(date_depense) >= date('now', 'localtime', 'start of month')
        """
    ).fetchone()[0]

    dep_mois_dernier = connexion.execute(
        """
        SELECT COALESCE(SUM(montant), 0)
        FROM depenses
        WHERE date(date_depense)
              >= date('now', 'localtime', 'start of month', '-1 month')
          AND date(date_depense) < date('now', 'localtime', 'start of month')
        """
    ).fetchone()[0]

    benefice_mois = ca_mois - dep_mois
    benefice_mois_dernier = ca_mois_dernier - dep_mois_dernier

    def variation_pct(valeur_actuelle, valeur_precedente):
        """Renvoie la variation en % (float) ou None si non calculable."""
        if valeur_precedente == 0:
            return None
        return (
            (valeur_actuelle - valeur_precedente)
            / abs(valeur_precedente) * 100
        )

    # ==========================================
    # VENTES SUR LES 30 DERNIERS JOURS
    # ==========================================

    ventes_par_jour = connexion.execute(
        """
        SELECT date(date_vente) AS jour, SUM(montant_total) AS total
        FROM ventes
        WHERE date(date_vente) >= date('now', 'localtime', '-29 days')
        GROUP BY jour
        ORDER BY jour
        """
    ).fetchall()

    # ==========================================
    # TOP 5 DES PRODUITS LES PLUS VENDUS
    # ==========================================

    top_produits = connexion.execute(
        """
        SELECT
            produits.nom AS produit,
            SUM(ventes.quantite) AS quantite_vendue
        FROM ventes
        LEFT JOIN produits
            ON ventes.produit_id = produits.id
        GROUP BY produits.id, produits.nom
        ORDER BY quantite_vendue DESC
        LIMIT 5
        """
    ).fetchall()

    # ==========================================
    # PRODUITS EN STOCK FAIBLE
    # ==========================================

    produits_faibles = connexion.execute(
        """
        SELECT nom, quantite, seuil_alerte
        FROM produits
        WHERE quantite <= seuil_alerte
        ORDER BY quantite ASC
        LIMIT 3
        """
    ).fetchall()

    # ==========================================
    # VENTES RÉCENTES
    # ==========================================

    ventes_recentes = connexion.execute(
        """
        SELECT ventes.montant_total, ventes.date_vente, produits.nom
        FROM ventes
        LEFT JOIN produits
            ON ventes.produit_id = produits.id
        ORDER BY ventes.id DESC
        LIMIT 3
        """
    ).fetchall()

    connexion.close()

    # ==========================================
    # STYLE
    # (textwrap.dedent retire l'indentation Python avant l'envoi à
    # Streamlit, sinon Markdown affiche le bloc comme du code brut)
    # ==========================================

    st.markdown(
        textwrap.dedent(
            """
            <style>
            .db-header {
                background: linear-gradient(135deg, #00843D 0%, #00602B 100%);
                border-radius: 14px;
                padding: 14px 18px;
                margin-bottom: 14px;
            }
            .db-header .titre {
                color: white;
                font-size: 20px;
                font-weight: 700;
                margin: 0;
            }
            .db-header .sous-titre {
                color: rgba(255,255,255,0.85);
                font-size: 12px;
                margin-top: 2px;
            }
            .section-title {
                color: #1A1A1A;
                font-size: 15px;
                font-weight: 700;
                margin: 16px 0 8px 0;
            }
            .kpi-card {
                background: white;
                border-radius: 12px;
                border: 1px solid #EAECEF;
                box-shadow: 0 1px 6px rgba(16,24,40,0.04);
                padding: 10px 12px;
                min-height: 92px;
            }
            .kpi-icon {
                width: 26px;
                height: 26px;
                border-radius: 7px;
                background: #E6F4EA;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 13px;
                margin-bottom: 6px;
            }
            .kpi-label {
                color: #6B7280;
                font-size: 11px;
                font-weight: 500;
                margin-bottom: 2px;
            }
            .kpi-value {
                color: #111827;
                font-size: 16px;
                font-weight: 700;
                margin-bottom: 4px;
            }
            .trend-badge {
                display: inline-block;
                font-size: 10px;
                font-weight: 600;
                padding: 2px 7px;
                border-radius: 999px;
            }
            .stat-mini {
                background: white;
                border-radius: 10px;
                border: 1px solid #EAECEF;
                padding: 8px 10px;
                text-align: center;
            }
            .stat-mini .valeur {
                font-size: 16px;
                font-weight: 700;
                color: #111827;
            }
            .stat-mini .libelle {
                font-size: 11px;
                color: #6B7280;
                margin-top: 1px;
            }
            .alert-card {
                background-color: #FFF8E1;
                padding: 8px 12px;
                border-radius: 10px;
                border: 1px solid #FFE082;
                margin-bottom: 6px;
                font-size: 12px;
            }
            .vente-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: white;
                border: 1px solid #EAECEF;
                border-radius: 10px;
                padding: 8px 12px;
                margin-bottom: 6px;
            }
            .vente-row .nom { font-weight: 600; color: #111827; font-size: 12px; }
            .vente-row .date { color: #9CA3AF; font-size: 10px; }
            .vente-row .montant { font-weight: 700; color: #00843D; font-size: 12px; }

            /* Écrans étroits (téléphone) : Streamlit empile déjà les
               colonnes tout seul, on réduit juste texte/espacements */
            @media (max-width: 640px) {
                .db-header { padding: 10px 14px; border-radius: 12px; }
                .db-header .titre { font-size: 17px; }
                .db-header .sous-titre { font-size: 11px; }
                .section-title { font-size: 13px; margin: 12px 0 6px 0; }
                .kpi-card { padding: 8px 10px; min-height: auto; }
                .kpi-icon { width: 22px; height: 22px; font-size: 11px; }
                .kpi-label { font-size: 10px; }
                .kpi-value { font-size: 14px; }
                .trend-badge { font-size: 9px; padding: 1px 6px; }
                .stat-mini { padding: 6px 8px; }
                .stat-mini .valeur { font-size: 14px; }
                .stat-mini .libelle { font-size: 10px; }
                .alert-card, .vente-row { padding: 6px 10px; }
            }
            </style>
            """
        ),
        unsafe_allow_html=True
    )

    # ==========================================
    # HELPERS D'AFFICHAGE (HTML sur une seule ligne)
    # ==========================================

    def carte_kpi(icone, label, valeur, variation=None, inverse=False):
        badge = ""
        if variation is not None:
            positif = variation >= 0
            bon = positif if not inverse else not positif
            couleur = VERT if bon else ROUGE
            fond = "#E6F4EA" if bon else "#FDECEC"
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
    # COMPARATIF DU MOIS
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
        carte_kpi("🏦", "Bénéfice total", f"{benefice:,.0f} KMF")


    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        carte_mini(nombre_produits, "📦 Produits")
    with col2:
        carte_mini(nombre_clients, "👥 Clients")
    with col3:
        carte_mini(stocks_faibles, "⚠️ Stock faible")

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
            line={"color": VERT, "size": 3},
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
            x=alt.X("jour:T", title=None, axis=alt.Axis(grid=False)),
            y=alt.Y(
                "ventes:Q", title=None,
                axis=alt.Axis(grid=True, gridColor="#F0F0F0")
            ),
            tooltip=[
                alt.Tooltip("jour:T", title="Date", format="%d/%m/%Y"),
                alt.Tooltip("ventes:Q", title="Ventes", format=",.0f"),
            ]
        ).properties(height=170)

        st.altair_chart(graphique, use_container_width=True)
    else:
        st.info("Aucune vente enregistrée sur les 30 derniers jours.")

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
        ).properties(height=160)

        st.altair_chart(barres, use_container_width=True)
    else:
        st.info("Aucune vente enregistrée pour le moment.")

    st.markdown(
        '<div class="section-title">⚠️ Produits avec stock faible</div>',
        unsafe_allow_html=True
    )

    if produits_faibles:
        for produit in produits_faibles:
            st.markdown(
                f'<div class="alert-card">'
                f'<strong>📦 {produit["nom"]}</strong><br>'
                f'Stock actuel : {produit["quantite"]}'
                f' &nbsp;|&nbsp; '
                f'Seuil d\'alerte : {produit["seuil_alerte"]}'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.success("✅ Aucun produit n'est actuellement en stock faible.")

    # ==========================================
    # VENTES RÉCENTES
    # ==========================================

    st.markdown(
        '<div class="section-title">💰 Ventes récentes</div>',
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
