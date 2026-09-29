
from contextlib import closing
from fpdf import FPDF
from config.colors import FOND_PAGE, TEXTE_PRINCIPAL, TEXTE_SECONDAIRE, VERT
from database.connexion import obtenir_connexion


def _rgb(couleur_hex: str):
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


def creer_vente(articles: list, utilisateur_id: int, note: str = None):
    """
    Enregistre une ou plusieurs ventes + décrémente le stock.
    Retourne (succès, message, liste_ids_ventes)
    """
    if not articles:
        return False, "Aucune vente à enregistrer.", None

    with closing(obtenir_connexion()) as connexion:
        try:
            # Vérification du stock
            for article in articles:
                stock = connexion.execute(
                    "SELECT quantite, nom FROM produits "
                    "WHERE id = ? AND utilisateur_id = ?",
                    (article["produit_id"], utilisateur_id)
                ).fetchone()

                if stock is None:
                    return False, f"Le produit « {article['nom']} » n'existe plus.", None

                if article["quantite"] > stock["quantite"]:
                    return False, (
                        f"Stock insuffisant pour « {stock['nom']} » "
                        f"(disponible : {stock['quantite']})."
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

                # Décrémentation du stock
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



def generer_pdf_recu(ids_ventes: list, utilisateur_id: int) -> bytes | None:
    """
    Génère un reçu de vente professionnel (format ticket).
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

    # Couleurs
    vert = _rgb(VERT)
    texte_fonce = _rgb(TEXTE_PRINCIPAL)
    texte_gris = _rgb(TEXTE_SECONDAIRE)

    # Format ticket (80 mm de large)
    pdf = FPDF(orientation="P", unit="mm", format=(80, 200))
    pdf.set_auto_page_break(auto=True, margin=6)
    pdf.add_page()
    pdf.set_margins(6, 6, 6)

    # =====================================================
    # EN-TÊTE
    # =====================================================
    nom_boutique = ""
    if vendeur:
        nom_boutique = (vendeur["nom_entreprise"] or vendeur["nom"] or "Ma Boutique").strip()

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*vert)
    pdf.cell(0, 6, _txt(nom_boutique)[:26], align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*texte_gris)

    if vendeur and vendeur["telephone_entreprise"]:
        pdf.cell(0, 4, _txt(f"Tél : {vendeur['telephone_entreprise']}"), align="C", new_x="LMARGIN", new_y="NEXT")
    if vendeur and vendeur["adresse_entreprise"]:
        pdf.cell(0, 4, _txt(vendeur["adresse_entreprise"])[:32], align="C", new_x="LMARGIN", new_y="NEXT")

    # Ligne de séparation
    pdf.ln(2)
    pdf.set_draw_color(*vert)
    pdf.set_line_width(0.5)
    y = pdf.get_y()
    pdf.line(8, y, 72, y)
    pdf.ln(3)

    # =====================================================
    # TITRE + INFOS
    # =====================================================
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*texte_fonce)
    pdf.cell(0, 5, "RECU DE VENTE", align="C", new_x="LMARGIN", new_y="NEXT")

    # Numéro de reçu (on prend le premier ID)
    numero_recu = f"R-{ventes[0]['id']:05d}"
    date_vente = _date_lisible(ventes[0]["date_vente"])

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*texte_gris)
    pdf.cell(0, 4, f"N° {numero_recu}  - {date_vente}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # =====================================================
    # EN-TÊTE DU TABLEAU
    # =====================================================
    pdf.set_fill_color(*vert)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)

    pdf.cell(38, 6, " Produit", border=0, fill=True, new_x="RIGHT", new_y="TOP")
    pdf.cell(12, 6, "Qté", border=0, fill=True, align="C", new_x="RIGHT", new_y="TOP")
    pdf.cell(18, 6, "Total", border=0, fill=True, align="R", new_x="LMARGIN", new_y="NEXT")

    # =====================================================
    # LIGNES DES ARTICLES
    # =====================================================
    total_general = 0
    pdf.set_font("Helvetica", "", 8)

    for index, v in enumerate(ventes):
        nom = v["produit_nom"] or "Produit"
        total_general += v["montant_total"]

        # Alternance de fond léger
        if index % 2 == 1:
            pdf.set_fill_color(245, 247, 250)
            fill = True
        else:
            fill = False

        pdf.set_text_color(*texte_fonce)
        pdf.cell(38, 5, _txt(nom)[:20], border=0, fill=fill, new_x="RIGHT", new_y="TOP")
        pdf.cell(12, 5, str(v["quantite"]), border=0, fill=fill, align="C", new_x="RIGHT", new_y="TOP")
        pdf.cell(18, 5, f"{v['montant_total']:,.0f}", border=0, fill=fill, align="R", new_x="LMARGIN", new_y="NEXT")

        # Détail prix unitaire
        pdf.set_text_color(*texte_gris)
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(0, 3.5, f"  {v['prix_unitaire']:,.0f} KMF × {v['quantite']}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)

    # =====================================================
    # TOTAL
    # =====================================================
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

    # =====================================================
    # PIED DE PAGE
    # =====================================================
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

