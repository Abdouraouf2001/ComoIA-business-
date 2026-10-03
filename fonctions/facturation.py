from contextlib import closing

from fpdf import FPDF

from config.colors import (
    FOND_PAGE,
    TEXTE_PRINCIPAL,
    TEXTE_SECONDAIRE,
    VERT,
)
from database.connexion import obtenir_connexion


def _rgb(couleur_hex):
    return tuple(
        int(couleur_hex[i:i + 2], 16)
        for i in (1, 3, 5)
    )


def _txt(valeur):
    texte = "" if valeur is None else str(valeur)
    return texte.encode(
        "latin-1",
        "replace"
    ).decode("latin-1")


def _date_lisible(date_sql):
    texte = str(date_sql or "")

    try:
        annee, mois, jour = texte[:10].split("-")
        return f"{jour}/{mois}/{annee}"

    except ValueError:
        return texte


def generer_numero_facture(connexion, utilisateur_id):
    total = connexion.execute(
        """
        SELECT COUNT(*)
        FROM factures
        WHERE utilisateur_id = ?
        """,
        (utilisateur_id,)
    ).fetchone()[0]

    return f"FAC-{total + 1:04d}"


def creer_facture(
    client_id,
    articles,
    remise,
    note,
    utilisateur_id
):
    """
    Crée une facture avec ses lignes.

    La création de la facture, des ventes et la
    diminution du stock se font dans une seule
    transaction.
    """

    if not articles:
        return False, "La facture est vide.", None

    with closing(obtenir_connexion()) as connexion:

        try:

            # ==================================================
            # CLIENT
            # ==================================================

            if client_id is not None:

                client = connexion.execute(
                    """
                    SELECT id
                    FROM clients
                    WHERE id = ?
                      AND utilisateur_id = ?
                    """,
                    (
                        client_id,
                        utilisateur_id
                    )
                ).fetchone()

                if client is None:
                    return (
                        False,
                        "Le client sélectionné "
                        "n'appartient pas à votre compte.",
                        None
                    )

            # ==================================================
            # STOCK
            # ==================================================

            for article in articles:

                stock = connexion.execute(
                    """
                    SELECT
                        id,
                        nom,
                        quantite,
                        prix_vente
                    FROM produits
                    WHERE id = ?
                      AND utilisateur_id = ?
                    """,
                    (
                        article["produit_id"],
                        utilisateur_id
                    )
                ).fetchone()

                if stock is None:

                    return (
                        False,
                        f"Le produit « {article['nom']} » "
                        "n'existe plus.",
                        None
                    )

                if article["quantite"] <= 0:

                    return (
                        False,
                        f"La quantité du produit "
                        f"« {article['nom']} » est invalide.",
                        None
                    )

                if article["quantite"] > stock["quantite"]:

                    return (
                        False,
                        f"Stock insuffisant pour "
                        f"« {article['nom']} » "
                        f"(disponible : {stock['quantite']}).",
                        None
                    )

            # ==================================================
            # TOTAL
            # ==================================================

            total_brut = sum(
                article["montant"]
                for article in articles
            )

            remise = float(remise or 0)

            if remise < 0:
                remise = 0

            if remise > total_brut:
                remise = total_brut

            total_final = total_brut - remise

            # ==================================================
            # NUMÉRO FACTURE
            # ==================================================

            numero = generer_numero_facture(
                connexion,
                utilisateur_id
            )

            # ==================================================
            # FACTURE
            # ==================================================

            curseur = connexion.execute(
                """
                INSERT INTO factures
                (
                    numero,
                    client_id,
                    utilisateur_id,
                    total_brut,
                    remise,
                    total_final,
                    note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    numero,
                    client_id,
                    utilisateur_id,
                    total_brut,
                    remise,
                    total_final,
                    note.strip()
                    if note
                    else None
                )
            )

            facture_id = curseur.lastrowid

            # ==================================================
            # LIGNES + VENTES + STOCK
            # ==================================================

            for article in articles:

                # Ligne facture
                connexion.execute(
                    """
                    INSERT INTO lignes_facture
                    (
                        facture_id,
                        produit_id,
                        quantite,
                        prix_unitaire,
                        montant
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        facture_id,
                        article["produit_id"],
                        article["quantite"],
                        article["prix_unitaire"],
                        article["montant"]
                    )
                )

                # Vente
                connexion.execute(
                    """
                    INSERT INTO ventes
                    (
                        produit_id,
                        quantite,
                        prix_unitaire,
                        montant_total,
                        utilisateur_id
                    )
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

                # Stock
                connexion.execute(
                    """
                    UPDATE produits
                    SET quantite = quantite - ?
                    WHERE id = ?
                      AND utilisateur_id = ?
                    """,
                    (
                        article["quantite"],
                        article["produit_id"],
                        utilisateur_id
                    )
                )

            connexion.commit()

            return (
                True,
                numero,
                facture_id
            )

        except Exception as erreur:

            connexion.rollback()

            print(
                "Erreur création facture :",
                erreur
            )

            return (
                False,
                "Une erreur est survenue lors "
                "de la création de la facture.",
                None
            )


# ============================================================
# PDF FACTURE
# ============================================================

def generer_pdf_facture(
    facture_id,
    utilisateur_id
):

    with closing(obtenir_connexion()) as connexion:

        # ------------------------------------------------------
        # FACTURE
        # ------------------------------------------------------

        facture = connexion.execute(
            """
            SELECT
                factures.numero,
                factures.total_brut,
                factures.remise,
                factures.total_final,
                factures.note,
                factures.date_creation,

                clients.nom AS client_nom,
                clients.telephone AS client_telephone,
                clients.email AS client_email,
                clients.adresse AS client_adresse

            FROM factures

            LEFT JOIN clients
                ON factures.client_id = clients.id

            WHERE factures.id = ?
              AND factures.utilisateur_id = ?
            """,
            (
                facture_id,
                utilisateur_id
            )
        ).fetchone()

        if facture is None:
            return None

        # ------------------------------------------------------
        # LIGNES FACTURE
        # ------------------------------------------------------

        lignes = connexion.execute(
            """
            SELECT
                lignes_facture.quantite,
                lignes_facture.prix_unitaire,
                lignes_facture.montant,
                produits.nom AS produit_nom

            FROM lignes_facture

            LEFT JOIN produits
                ON lignes_facture.produit_id = produits.id

            WHERE lignes_facture.facture_id = ?

            ORDER BY lignes_facture.id
            """,
            (facture_id,)
        ).fetchall()

        # ------------------------------------------------------
        # VENDEUR
        # ------------------------------------------------------

        vendeur = connexion.execute(
            """
            SELECT
                nom,
                email,
                nom_entreprise,
                telephone_entreprise,
                adresse_entreprise

            FROM utilisateurs

            WHERE id = ?
            """,
            (utilisateur_id,)
        ).fetchone()

    # ==========================================================
    # COULEURS
    # ==========================================================

    vert = _rgb(VERT)

    texte_fonce = _rgb(
        TEXTE_PRINCIPAL
    )

    texte_gris = _rgb(
        TEXTE_SECONDAIRE
    )

    fond_clair = _rgb(
        FOND_PAGE
    )

    # ==========================================================
    # PDF
    # ==========================================================

    pdf = FPDF(
        orientation="P",
        unit="mm",
        format="A4"
    )

    pdf.set_auto_page_break(
        auto=True,
        margin=15
    )

    pdf.add_page()

    # ----------------------------------------------------------
    # EN-TÊTE
    # ----------------------------------------------------------

    pdf.set_font(
        "Helvetica",
        "B",
        22
    )

    pdf.set_text_color(*vert)

    pdf.cell(
        100,
        10,
        "FACTURE",
        new_x="RIGHT",
        new_y="TOP"
    )

    pdf.set_font(
        "Helvetica",
        "B",
        13
    )

    pdf.set_text_color(
        *texte_fonce
    )

    pdf.cell(
        0,
        10,
        _txt(facture["numero"]),
        align="R",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.set_font(
        "Helvetica",
        "",
        10
    )

    pdf.set_text_color(
        *texte_gris
    )

    pdf.cell(
        100,
        6,
        "ComorIA Business AI",
        new_x="RIGHT",
        new_y="TOP"
    )

    pdf.cell(
        0,
        6,
        f"Date : {_date_lisible(facture['date_creation'])}",
        align="R",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    pdf.ln(3)

    pdf.set_draw_color(*vert)

    pdf.set_line_width(0.6)

    y = pdf.get_y()

    pdf.line(
        pdf.l_margin,
        y,
        pdf.w - pdf.r_margin,
        y
    )

    pdf.ln(6)

    # ----------------------------------------------------------
    # VENDEUR / CLIENT
    # ----------------------------------------------------------

    x_gauche = pdf.l_margin
    x_droite = pdf.l_margin + 95
    y_debut = pdf.get_y()

    def bloc(
        x,
        titre,
        lignes_texte
    ):

        pdf.set_xy(
            x,
            y_debut
        )

        pdf.set_font(
            "Helvetica",
            "B",
            10
        )

        pdf.set_text_color(*vert)

        pdf.cell(
            85,
            6,
            _txt(titre),
            new_x="LMARGIN",
            new_y="NEXT"
        )

        premiere = True

        for texte in lignes_texte:

            if not texte:
                continue

            pdf.set_x(x)

            pdf.set_font(
                "Helvetica",
                "B" if premiere else "",
                10
            )

            pdf.set_text_color(
                *(
                    texte_fonce
                    if premiere
                    else texte_gris
                )
            )

            pdf.cell(
                85,
                5,
                _txt(texte)[:48],
                new_x="LMARGIN",
                new_y="NEXT"
            )

            premiere = False

        return pdf.get_y()

    nom_vendeur = ""

    if vendeur:

        nom_vendeur = (
            vendeur["nom_entreprise"]
            or vendeur["nom"]
            or ""
        )

    y_gauche = bloc(
        x_gauche,
        "Émis par",
        [
            nom_vendeur,
            vendeur["telephone_entreprise"]
            if vendeur else None,
            vendeur["adresse_entreprise"]
            if vendeur else None,
            vendeur["email"]
            if vendeur else None,
        ]
    )

    y_droite = bloc(
        x_droite,
        "Facturé à",
        [
            facture["client_nom"]
            or "Client comptant",

            facture["client_telephone"],

            facture["client_email"],

            facture["client_adresse"],
        ]
    )

    pdf.set_y(
        max(
            y_gauche,
            y_droite
        ) + 8
    )

    # ----------------------------------------------------------
    # TABLEAU
    # ----------------------------------------------------------

    largeurs = [
        80,
        25,
        35,
        40
    ]

    def entete_tableau():

        pdf.set_font(
            "Helvetica",
            "B",
            10
        )

        pdf.set_fill_color(*vert)

        pdf.set_text_color(
            255,
            255,
            255
        )

        pdf.cell(
            largeurs[0],
            8,
            "Produit",
            border=1,
            fill=True,
            new_x="RIGHT",
            new_y="TOP"
        )

        pdf.cell(
            largeurs[1],
            8,
            "Quantité",
            border=1,
            fill=True,
            align="C",
            new_x="RIGHT",
            new_y="TOP"
        )

        pdf.cell(
            largeurs[2],
            8,
            "Prix unitaire",
            border=1,
            fill=True,
            align="R",
            new_x="RIGHT",
            new_y="TOP"
        )

        pdf.cell(
            largeurs[3],
            8,
            "Montant",
            border=1,
            fill=True,
            align="R",
            new_x="LMARGIN",
            new_y="NEXT"
        )

    entete_tableau()

    pdf.set_font(
        "Helvetica",
        "",
        10
    )

    pdf.set_text_color(
        *texte_fonce
    )

    for index, ligne in enumerate(lignes):

        if pdf.get_y() > 265:

            pdf.add_page()

            entete_tableau()

            pdf.set_font(
                "Helvetica",
                "",
                10
            )

            pdf.set_text_color(
                *texte_fonce
            )

        remplir = index % 2 == 1

        if remplir:
            pdf.set_fill_color(
                *fond_clair
            )

        nom = (
            ligne["produit_nom"]
            or "Produit supprimé"
        )

        pdf.cell(
            largeurs[0],
            8,
            _txt(nom)[:42],
            border=1,
            fill=remplir,
            new_x="RIGHT",
            new_y="TOP"
        )

        pdf.cell(
            largeurs[1],
            8,
            str(ligne["quantite"]),
            border=1,
            fill=remplir,
            align="C",
            new_x="RIGHT",
            new_y="TOP"
        )

        pdf.cell(
            largeurs[2],
            8,
            f"{ligne['prix_unitaire']:,.0f} KMF",
            border=1,
            fill=remplir,
            align="R",
            new_x="RIGHT",
            new_y="TOP"
        )

        pdf.cell(
            largeurs[3],
            8,
            f"{ligne['montant']:,.0f} KMF",
            border=1,
            fill=remplir,
            align="R",
            new_x="LMARGIN",
            new_y="NEXT"
        )

    # ----------------------------------------------------------
    # TOTAUX
    # ----------------------------------------------------------

    pdf.ln(4)

    def ligne_total(
        libelle,
        valeur,
        gras=False
    ):

        pdf.set_font(
            "Helvetica",
            "B" if gras else "",
            12 if gras else 10
        )

        pdf.set_text_color(
            *(vert if gras else texte_fonce)
        )

        pdf.cell(
            105,
            7,
            "",
            new_x="RIGHT",
            new_y="TOP"
        )

        pdf.cell(
            35,
            7,
            libelle,
            align="R",
            new_x="RIGHT",
            new_y="TOP"
        )

        pdf.cell(
            40,
            7,
            valeur,
            align="R",
            new_x="LMARGIN",
            new_y="NEXT"
        )

    ligne_total(
        "Total brut",
        f"{facture['total_brut']:,.0f} KMF"
    )

    if facture["remise"]:

        ligne_total(
            "Remise",
            f"-{facture['remise']:,.0f} KMF"
        )

    ligne_total(
        "TOTAL À PAYER",
        f"{facture['total_final']:,.0f} KMF",
        gras=True
    )

    # ----------------------------------------------------------
    # NOTE
    # ----------------------------------------------------------

    if facture["note"]:

        pdf.ln(6)

        pdf.set_font(
            "Helvetica",
            "B",
            10
        )

        pdf.set_text_color(*vert)

        pdf.cell(
            0,
            6,
            "Note",
            new_x="LMARGIN",
            new_y="NEXT"
        )

        pdf.set_font(
            "Helvetica",
            "",
            10
        )

        pdf.set_text_color(
            *texte_gris
        )

        pdf.multi_cell(
            0,
            5,
            _txt(facture["note"]),
            align="L",
            new_x="LMARGIN",
            new_y="NEXT"
        )

    # ----------------------------------------------------------
    # PIED DE PAGE
    # ----------------------------------------------------------

    pdf.ln(10)

    pdf.set_font(
        "Helvetica",
        "I",
        9
    )

    pdf.set_text_color(
        *texte_gris
    )

    pdf.cell(
        0,
        5,
        "Merci pour votre confiance.",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT"
    )

    return bytes(
        pdf.output()
    )
