from contextlib import closing

from database.connexion import obtenir_connexion


def generer_numero_facture(connexion, utilisateur_id):
    """Numéro séquentiel simple par utilisateur : FAC-0001, FAC-0002, ..."""
    total = connexion.execute(
        "SELECT COUNT(*) FROM factures WHERE utilisateur_id = ?",
        (utilisateur_id,)
    ).fetchone()[0]
    return f"FAC-{total + 1:04d}"


def creer_facture(client_id, articles, remise, note, utilisateur_id):
    """
    Crée une facture, ses lignes, les ventes correspondantes, et
    décrémente le stock — le tout dans une seule transaction : si une
    étape échoue (ex. stock insuffisant détecté à la confirmation),
    rien n'est enregistré.
    """

    if not articles:
        return False, "La facture est vide."

    with closing(obtenir_connexion()) as connexion:
        try:
            # Revérifie le stock au moment de la confirmation (il a pu
            # changer depuis que les articles ont été ajoutés au panier)
            for article in articles:
                stock_actuel = connexion.execute(
                    "SELECT quantite FROM produits "
                    "WHERE id = ? AND utilisateur_id = ?",
                    (article["produit_id"], utilisateur_id)
                ).fetchone()

                if stock_actuel is None:
                    return False, f"« {article['nom']} » n'existe plus."

                if article["quantite"] > stock_actuel["quantite"]:
                    return False, (
                        f"Stock insuffisant pour « {article['nom']} » "
                        f"(disponible : {stock_actuel['quantite']})."
                    )

            total_brut = sum(article["montant"] for article in articles)
            total_final = total_brut - remise
            numero = generer_numero_facture(connexion, utilisateur_id)

            curseur = connexion.execute(
                """
                INSERT INTO factures
                (numero, client_id, utilisateur_id, total_brut,
                 remise, total_final, note)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (numero, client_id, utilisateur_id, total_brut,
                 remise, total_final, note.strip() if note else None)
            )
            facture_id = curseur.lastrowid

            for article in articles:
                connexion.execute(
                    """
                    INSERT INTO lignes_facture
                    (facture_id, produit_id, quantite, prix_unitaire, montant)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (facture_id, article["produit_id"], article["quantite"],
                     article["prix_unitaire"], article["montant"])
                )

                # Chaque ligne de facture génère aussi une vente, pour que
                # les pages Rapports/Accueil/Prévisions restent cohérentes
                connexion.execute(
                    """
                    INSERT INTO ventes
                    (produit_id, quantite, prix_unitaire, montant_total,
                     utilisateur_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (article["produit_id"], article["quantite"],
                     article["prix_unitaire"], article["montant"], utilisateur_id)
                )

                connexion.execute(
                    "UPDATE produits SET quantite = quantite - ? "
                    "WHERE id = ? AND utilisateur_id = ?",
                    (article["quantite"], article["produit_id"], utilisateur_id)
                )

            connexion.commit()
            return True, numero

        except Exception as erreur:
            connexion.rollback()
            print("Erreur création facture :", erreur)
            return False, "Une erreur est survenue lors de la création de la facture."
