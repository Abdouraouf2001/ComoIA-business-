import datetime

import streamlit as st
from database.connexion import obtenir_connexion

PERIODES = [
    "Aujourd'hui",
    "7 derniers jours",
    "30 derniers jours",
    "Ce mois-ci",
    "Période personnalisée",
]


def calculer_dates(periode):
    """Renvoie (date_debut, date_fin) au format YYYY-MM-DD, bornes incluses."""

    aujourdhui = datetime.date.today()

    if periode == "Aujourd'hui":
        return aujourdhui, aujourdhui

    if periode == "7 derniers jours":
        return aujourdhui - datetime.timedelta(days=6), aujourdhui

    if periode == "30 derniers jours":
        return aujourdhui - datetime.timedelta(days=29), aujourdhui

    if periode == "Ce mois-ci":
        return aujourdhui.replace(day=1), aujourdhui

    # Période personnalisée : gérée séparément via st.date_input
    return aujourdhui - datetime.timedelta(days=29), aujourdhui


def afficher_page_rapports():

    st.markdown(
        '<p style="font-size:20px;font-weight:700;margin-bottom:2px;">'
        '📈 Rapports</p>'
        '<p style="font-size:13px;color:#6B7280;margin-bottom:10px;">'
        'Analyse de l\'activité de votre entreprise.</p>',
        unsafe_allow_html=True
    )

    # ==========================================================
    # FILTRE PAR PÉRIODE
    # ==========================================================

    col_periode, col_dates = st.columns([2, 3])

    with col_periode:
        periode = st.selectbox("Période", PERIODES, index=2)

    date_debut, date_fin = calculer_dates(periode)

    if periode == "Période personnalisée":
        with col_dates:
            date_debut, date_fin = st.date_input(
                "Du / au",
                value=(date_debut, date_fin),
                format="DD/MM/YYYY"
            )

    if date_debut > date_fin:
        st.error("La date de début doit être avant la date de fin.")
        return

    st.caption(
        f"Période analysée : du {date_debut.strftime('%d/%m/%Y')} "
        f"au {date_fin.strftime('%d/%m/%Y')}"
    )

    date_debut_sql = date_debut.isoformat()
    date_fin_sql = date_fin.isoformat()

    connexion = obtenir_connexion()

    # ==========================================================
    # INDICATEURS DE LA PÉRIODE
    # ==========================================================

    chiffre_affaires = connexion.execute(
        """
        SELECT COALESCE(SUM(montant_total), 0)
        FROM ventes
        WHERE date(date_vente) BETWEEN ? AND ?
        """,
        (date_debut_sql, date_fin_sql)
    ).fetchone()[0]

    total_depenses = connexion.execute(
        """
        SELECT COALESCE(SUM(montant), 0)
        FROM depenses
        WHERE date(date_depense) BETWEEN ? AND ?
        """,
        (date_debut_sql, date_fin_sql)
    ).fetchone()[0]

    benefice = chiffre_affaires - total_depenses

    nombre_ventes = connexion.execute(
        """
        SELECT COUNT(*)
        FROM ventes
        WHERE date(date_vente) BETWEEN ? AND ?
        """,
        (date_debut_sql, date_fin_sql)
    ).fetchone()[0]

    st.markdown('<p style="font-size:14px;font-weight:600;margin:6px 0;">🗓️ Sur la période sélectionnée</p>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Chiffre d'affaires", f"{chiffre_affaires:,.0f} KMF")
    with col2:
        st.metric("💳 Dépenses", f"{total_depenses:,.0f} KMF")
    with col3:
        st.metric("📊 Bénéfice", f"{benefice:,.0f} KMF")
    with col4:
        st.metric("🧾 Ventes", nombre_ventes)

    # ==========================================================
    # ÉTAT ACTUEL (non filtré par période : ce sont des totaux
    # au moment présent, pas une activité passée)
    # ==========================================================

    nombre_clients = connexion.execute(
        "SELECT COUNT(*) FROM clients"
    ).fetchone()[0]

    nombre_produits = connexion.execute(
        "SELECT COUNT(*) FROM produits"
    ).fetchone()[0]

    produits_alerte = connexion.execute(
        "SELECT COUNT(*) FROM produits WHERE quantite <= seuil_alerte"
    ).fetchone()[0]

    st.markdown('<p style="font-size:14px;font-weight:600;margin:6px 0;">📦 État actuel</p>', unsafe_allow_html=True)

    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric("👥 Clients", nombre_clients)
    with col6:
        st.metric("📦 Produits", nombre_produits)
    with col7:
        st.metric("⚠️ Stock faible", produits_alerte)

    # ==========================================================
    # VENTES PAR PRODUIT (sur la période)
    # ==========================================================

    st.markdown('<p style="font-size:14px;font-weight:600;margin:6px 0;">🏆 Ventes par produit</p>', unsafe_allow_html=True)

    ventes_produits = connexion.execute(
        """
        SELECT
            produits.nom AS produit,
            SUM(ventes.quantite) AS quantite_vendue,
            SUM(ventes.montant_total) AS chiffre_affaires
        FROM ventes
        LEFT JOIN produits
            ON ventes.produit_id = produits.id
        WHERE date(ventes.date_vente) BETWEEN ? AND ?
        GROUP BY produits.id, produits.nom
        ORDER BY chiffre_affaires DESC
        """,
        (date_debut_sql, date_fin_sql)
    ).fetchall()

    if ventes_produits:
        for vente in ventes_produits:
            produit = vente["produit"] or "Produit supprimé"
            quantite = vente["quantite_vendue"] or 0
            montant = vente["chiffre_affaires"] or 0
            st.markdown(
                f'<div style="font-size:13px;padding:4px 0;border-bottom:1px solid #F1F1F1;">'
                f'<strong>{produit}</strong> — {quantite} unité(s) — {montant:,.0f} KMF'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("Aucune vente enregistrée sur cette période.")

    # ==========================================================
    # DÉPENSES PAR CATÉGORIE (sur la période)
    # ==========================================================

    st.markdown('<p style="font-size:14px;font-weight:600;margin:6px 0;">💳 Dépenses par catégorie</p>', unsafe_allow_html=True)

    depenses_categories = connexion.execute(
        """
        SELECT
            COALESCE(categorie, 'Sans catégorie') AS categorie,
            SUM(montant) AS total
        FROM depenses
        WHERE date(date_depense) BETWEEN ? AND ?
        GROUP BY categorie
        ORDER BY total DESC
        """,
        (date_debut_sql, date_fin_sql)
    ).fetchall()

    if depenses_categories:
        for depense in depenses_categories:
            st.markdown(
                f'<div style="font-size:13px;padding:4px 0;border-bottom:1px solid #F1F1F1;">'
                f'<strong>{depense["categorie"]}</strong> — {depense["total"] or 0:,.0f} KMF'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("Aucune dépense enregistrée sur cette période.")

    # ==========================================================
    # PRODUITS EN STOCK FAIBLE (état actuel, non filtré)
    # ==========================================================

    st.markdown('<p style="font-size:14px;font-weight:600;margin:6px 0;">⚠️ Produits nécessitant un réapprovisionnement</p>', unsafe_allow_html=True)

    quantite_faibles = connexion.execute(
        """
        SELECT nom, quantite, seuil_alerte
        FROM produits
        WHERE quantite <= seuil_alerte
        ORDER BY quantite ASC
        """
    ).fetchall()

    connexion.close()

    if quantite_faibles:
        for produit in quantite_faibles:
            st.markdown(
                f'<div style="font-size:13px;background:#FFF8E1;'
                f'border:1px solid #FFE082;border-radius:8px;'
                f'padding:6px 10px;margin-bottom:5px;">'
                f'<strong>{produit["nom"]}</strong> — '
                f'Stock : {produit["quantite"]} | '
                f'Minimum : {produit["seuil_alerte"]}'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.success("✅ Aucun produit n'est actuellement sous le seuil minimum.")
