import re
from pathlib import Path

from vision.ocr import extraire_texte_image


def analyser_document(chemin_image):
    """
    Analyse une facture ou un reçu à partir d'une image.

    Retourne un dictionnaire contenant :
    - texte_brut
    - montant
    - date
    - numero
    - fournisseur
    """

    chemin = Path(chemin_image)

    if not chemin.exists():
        return {
            "succes": False,
            "message": "Le document n'existe pas.",
            "texte_brut": "",
            "montant": None,
            "date": None,
            "numero": None,
            "fournisseur": None,
        }

    succes, resultat = extraire_texte_image(chemin)

    if not succes:
        return {
            "succes": False,
            "message": resultat,
            "texte_brut": "",
            "montant": None,
            "date": None,
            "numero": None,
            "fournisseur": None,
        }

    texte = resultat

    return {
        "succes": True,
        "message": "Document analysé avec succès.",
        "texte_brut": texte,
        "montant": extraire_montant(texte),
        "date": extraire_date(texte),
        "numero": extraire_numero(texte),
        "fournisseur": extraire_fournisseur(texte),
    }


def extraire_montant(texte):
    """
    Recherche un montant dans le texte OCR.
    Exemple :
        Total : 25 000 KMF
    """

    motifs = [
        r"(?:total|montant|net\s*[àa]\s*payer)\s*[:\-]?\s*"
        r"(\d[\d\s.,]*)\s*(?:KMF|FC|F)?",

        r"(\d[\d\s.,]*)\s*(?:KMF|FC|F)",
    ]

    for motif in motifs:
        correspondance = re.search(
            motif,
            texte,
            flags=re.IGNORECASE
        )

        if correspondance:
            valeur = correspondance.group(1)

            valeur = (
                valeur
                .replace(" ", "")
                .replace(",", ".")
            )

            try:
                return float(valeur)
            except ValueError:
                continue

    return None


def extraire_date(texte):
    """
    Recherche une date sous différentes formes.
    Exemples :
        28/09/2026
        28-09-2026
        28.09.2026
    """

    motif = r"\b(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})\b"

    correspondance = re.search(
        motif,
        texte
    )

    if correspondance:
        return correspondance.group(1)

    return None


def extraire_numero(texte):
    """
    Recherche un numéro de facture.
    """

    motifs = [
        r"(?:facture|fact\.|invoice)\s*(?:n[°o]?)?\s*[:\-]?\s*([A-Z0-9\-\/]+)",
        r"(?:n[°o]|numero|numéro)\s*[:\-]?\s*([A-Z0-9\-\/]+)",
    ]

    for motif in motifs:
        correspondance = re.search(
            motif,
            texte,
            flags=re.IGNORECASE
        )

        if correspondance:
            return correspondance.group(1)

    return None


def extraire_fournisseur(texte):
    """
    Première ligne non vide du document.
    Cette information est une estimation :
    l'OCR ne permet pas toujours d'identifier correctement
    le fournisseur.
    """

    lignes = [
        ligne.strip()
        for ligne in texte.splitlines()
        if ligne.strip()
    ]

    if lignes:
        return lignes[0][:100]

    return None
