

import datetime
from contextlib import closing

from database.connexion import obtenir_connexion


def obtenir_ventes_quotidiennes():
    """
    Récupère le chiffre d'affaires par jour calendaire, du premier
    jour de vente à aujourd'hui, en complétant à 0 les jours sans
    aucune vente (indispensable pour une moyenne mobile fiable).
    """

    with closing(obtenir_connexion()) as connexion:
        lignes = connexion.execute(
            """
            SELECT DATE(date_vente) AS jour, SUM(montant_total) AS chiffre_affaires
            FROM ventes
            GROUP BY DATE(date_vente)
            ORDER BY jour ASC
            """
        ).fetchall()

    if not lignes:
        return []

    totaux_par_jour = {ligne["jour"]: ligne["chiffre_affaires"] for ligne in lignes}

    premier_jour = datetime.date.fromisoformat(lignes[0]["jour"])
    aujourdhui = datetime.date.today()

    serie_complete = []
    jour_courant = premier_jour
    while jour_courant <= aujourdhui:
        cle = jour_courant.isoformat()
        serie_complete.append({
            "jour": cle,
            "chiffre_affaires": totaux_par_jour.get(cle, 0),
        })
        jour_courant += datetime.timedelta(days=1)

    return serie_complete


def obtenir_historique_produit(produit_id):
    """
    Récupère les ventes quotidiennes d'un produit, jours sans
    vente inclus à 0 (même logique que ci-dessus).
    """

    with closing(obtenir_connexion()) as connexion:
        lignes = connexion.execute(
            """
            SELECT DATE(date_vente) AS jour, SUM(quantite) AS quantite
            FROM ventes
            WHERE produit_id = ?
            GROUP BY DATE(date_vente)
            ORDER BY jour ASC
            """,
            (produit_id,)
        ).fetchall()

    if not lignes:
        return []

    totaux_par_jour = {ligne["jour"]: ligne["quantite"] for ligne in lignes}

    premier_jour = datetime.date.fromisoformat(lignes[0]["jour"])
    aujourdhui = datetime.date.today()

    serie_complete = []
    jour_courant = premier_jour
    while jour_courant <= aujourdhui:
        cle = jour_courant.isoformat()
        serie_complete.append({
            "jour": cle,
            "quantite": totaux_par_jour.get(cle, 0),
        })
        jour_courant += datetime.timedelta(days=1)

    return serie_complete


def analyser_historique():
    """
    Analyse la quantité de données disponible (en jours calendaires,
    pas seulement en jours avec vente) pour déterminer si une
    prévision est possible.
    """

    ventes = obtenir_ventes_quotidiennes()
    nombre_jours = len(ventes)

    if nombre_jours == 0:
        return {"disponible": False, "message": "Aucune vente enregistrée."}

    if nombre_jours < 7:
        return {
            "disponible": False,
            "message": (
                f"Seulement {nombre_jours} jour(s) d'historique depuis la "
                "première vente. Il faut au moins une semaine de données "
                "pour produire une prévision fiable."
            )
        }

    return {
        "disponible": True,
        "nombre_jours": nombre_jours,
        "message": f"{nombre_jours} jours d'historique disponibles pour l'analyse.",
    }


def prevoir_chiffre_affaires_moyenne_mobile(nombre_jours=7):
    """
    Prévision simple basée sur la moyenne des derniers jours
    calendaires (jours sans vente comptés comme 0).
    Sert de référence avant un modèle ML plus avancé.
    """

    if nombre_jours <= 0:
        return None

    ventes = obtenir_ventes_quotidiennes()

    if len(ventes) < nombre_jours:
        return None

    derniers_jours = ventes[-nombre_jours:]
    total = sum(vente["chiffre_affaires"] for vente in derniers_jours)
    moyenne = total / nombre_jours

    return round(moyenne, 2)

