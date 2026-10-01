from collections import defaultdict
from contextlib import closing

from fpdf import FPDF

from config.colors import FOND_PAGE, TEXTE_PRINCIPAL, TEXTE_SECONDAIRE, VERT
from database.connexion import obtenir_connexion


def _rgb(couleur_hex):
    return tuple(int(couleur_hex[i:i + 2], 16) for i in (1, 3, 5))


def _txt(valeur):
    texte = "" if valeur is None else str(valeur)
    return texte.encode("latin-1", "replace").decode("latin-1")


def _date_lisible(date_sql):
    texte = str(date_sql or "")
    try:
        annee, mois, jour = texte[:10].split("-")
        return f"{jour}/{mois}/{annee}"
    except ValueError:
        return texte


def creer_vente(articles, utilisateur_id, note=None):
    """
    Enregistre une ou plusieurs ventes + décrémente le stock.
    Retourne (succès, message, liste_ids_ventes).

    `note` est accepté mais n'est pas encore persisté : la table `ventes`
    n'a pas de colonne dédiée pour l'instant. Si tu veux vraiment
    l'enregistrer, dis-le et on ajoute la colonne (comme pour les factures).
    """
    if not articles:
        return False, "Aucune vente à enregistrer.", None

    with closing(obtenir_connexion()) as connexion:
        try:
            # Regroupe par produit AVANT de vérifier le stock : deux lignes
            # du même produit doivent être comparées à leur somme, pas
            # chacune isolément contre le stock actuel (sinon les deux
            # passent la vérification alors qu'ensemble elles dépassent
            # le stock réel).
            quantites_par_produit = defaultdict(int)
            for article in articles:
                quantites_par_produit[article["produit_id"]] += article["quantite"]

            for produit_id, quantite_totale in quantites_par_produit.items():
                stock = connexion.execute(
                    "SELECT quantite, nom FROM produits "
                    "WHERE id = ? AND utilisateur_id = ?",
                    (produit_id, utilisateur_id)
                ).fetchone()

                if stock is None:
                    return False, "Un des produits n'existe plus.", None

                if quantite_totale > stock["quantite"]:
                    return False, (
                        f"Stock insuffisant pour « {stock['nom']} » "
                        f"(disponible : {stock['quantite']}, "
                        f"demandé : {quantite_totale})."
                    ), None

            ids_ventes = []

            for article in articles:
                curseur = connexion.execute(
                    """
                    INSERT INTO ventes
                    (produit_id, quantite, prix_unitaire, montant_total, utilisateur_id)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        article["produit_id"],
                        article["quantite"],
                        article["prix_unitaire"],
                        article["montant"],
                        utilisateur_id
                    )
                )
                ids_ventes.append(curseur.lastrowid)

                connexion.execute(
                    "UPDATE produits SET quantite = quantite - ? "
                    "WHERE id = ? AND utilisateur_id = ?",
                    (article["quantite"], article["produit_id"], utilisateur_id)
                )

            connexion.commit()
            return True, "Vente enregistrée avec succès.", ids_ventes

        except Exception as erreur:
            connexion.rollback()
            print("Erreur création vente :", erreur)
            return False, "Une erreur est survenue lors de l'enregistrement de la vente.", None


def generer_pdf_recu(ids_ventes, utilisateur_id):
    """
    Génère un reçu de vente professionnel (format ticket 80mm).
    Renvoie None si aucune vente ne correspond à cet utilisateur —
    impossible de générer le reçu de la vente de quelqu'un d'autre en
    devinant un ID.
    """
    if not ids_ventes:
        return None

    with closing(obtenir_connexion()) as connexion:
        placeholders = ",".join("?" * len(ids_ventes))
        ventes = connexion.execute(
            f"""
            SELECT
                ventes.id, ventes.quantite, ventes.prix_unitaire,
                ventes.montant_total, ventes.date_vente,
                produits.nom AS produit_nom
            FROM ventes
            LEFT JOIN produits ON ventes.produit_id = produits.id
            WHERE ventes.id IN ({placeholders})
              AND ventes.utilisateur_id = ?
            ORDER BY ventes.id
            """,
            (*ids_ventes, utilisateur_id)
        ).fetchall()

        if not ventes:
            return None

        vendeur = connexion.execute(
            """
            SELECT nom, nom_entreprise, telephone_entreprise, adresse_entreprise
            FROM utilisateurs
            WHERE id = ?
            """,
            (utilisateur_id,)
        ).fetchone()

    vert = _rgb(VERT)
    texte_fonce = _rgb(TEXTE_PRINCIPAL)
    texte_gris = _rgb(TEXTE_SECONDAIRE)

    pdf = FPDF(orientation="P", unit="mm", format=(80, 200))
    pdf.set_auto_page_break(auto=True, margin=6)
    pdf.add_page()
    pdf.set_margins(6, 6, 6)

    nom_boutique = ""
    if vendeur:
        nom_boutique = (
            vendeur["nom_entreprise"] or vendeur["nom"] or "Ma Boutique"
        ).strip()

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*vert)
    pdf.cell(0, 6, _txt(nom_boutique)[:26], align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*texte_gris)

    if vendeur and vendeur["telephone_entreprise"]:
        pdf.cell(
            0, 4, _txt(f"Tél : {vendeur['telephone_entreprise']}"),
            align="C", new_x="LMARGIN", new_y="NEXT"
        )
    if vendeur and vendeur["adresse_entreprise"]:
        pdf.cell(
            0, 4, _txt(vendeur["adresse_entreprise"])[:32],
            align="C", new_x="LMARGIN", new_y="NEXT"
        )

    pdf.ln(2)
    pdf.set_draw_color(*vert)
    pdf.set_line_width(0.5)
    y = pdf.get_y()
    pdf.line(8, y, 72, y)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*texte_fonce)
    pdf.cell(0, 5, "RECU DE VENTE", align="C", new_x="LMARGIN", new_y="NEXT")

    numero_recu = f"R-{ventes[0]['id']:05d}"
    date_vente = _date_lisible(ventes[0]["date_vente"])

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*texte_gris)
    pdf.cell(
        0, 4, f"N° {numero_recu}  - {date_vente}",
        align="C", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(3)

    pdf.set_fill_color(*vert)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(38, 6, " Produit", fill=True, new_x="RIGHT", new_y="TOP")
    pdf.cell(12, 6, "Qté", fill=True, align="C", new_x="RIGHT", new_y="TOP")
    pdf.cell(18, 6, "Total", fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    total_general = 0
    pdf.set_font("Helvetica", "", 8)

    for index, v in enumerate(ventes):
        nom = v["produit_nom"] or "Produit"
        total_general += v["montant_total"]
        fill = index % 2 == 1
        if fill:
            pdf.set_fill_color(245, 247, 250)

        pdf.set_text_color(*texte_fonce)
        pdf.cell(38, 5, _txt(nom)[:20], fill=fill, new_x="RIGHT", new_y="TOP")
        pdf.cell(12, 5, str(v["quantite"]), fill=fill, align="C", new_x="RIGHT", new_y="TOP")
        pdf.cell(18, 5, f"{v['montant_total']:,.0f}", fill=fill, align="R", new_x="LMARGIN", new_y="NEXT")

        pdf.set_text_color(*texte_gris)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(
            0, 3.5, f"  {v['prix_unitaire']:,.0f} KMF × {v['quantite']}",
            new_x="LMARGIN", new_y="NEXT"
        )
        pdf.set_font("Helvetica", "", 8)

    pdf.ln(2)
    pdf.set_draw_color(*vert)
    pdf.set_line_width(0.4)
    y = pdf.get_y()
    pdf.line(8, y, 72, y)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*vert)
    pdf.cell(40, 6, "TOTAL", new_x="RIGHT", new_y="TOP")
    pdf.cell(28, 6, f"{total_general:,.0f} KMF", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(6)
    pdf.set_draw_color(200, 200, 200)
    pdf.set_line_width(0.2)
    y = pdf.get_y()
    pdf.line(15, y, 65, y)
    pdf.ln(3)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*texte_gris)
    pdf.cell(0, 4, _txt("Merci pour votre confiance !"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 4, _txt("A bientot"), align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(0, 3.5, "ComorIA Business AI", align="C")

    return bytes(pdf.output())
