from pathlib import Path

import pytesseract
from PIL import Image


def extraire_texte_image(chemin_image):
    """
    Extrait le texte présent dans une image.

    Retourne :
        - texte extrait si la lecture réussit
        - message d'erreur en cas de problème
    """

    try:
        chemin = Path(chemin_image)

        if not chemin.exists():
            return False, "L'image indiquée n'existe pas."

        image = Image.open(chemin)

        texte = pytesseract.image_to_string(image, lang="fra")

        texte = texte.strip()

        if not texte:
            return False, "Aucun texte n'a été détecté dans cette image."

        return True, texte

    except Exception as erreur:
        print("Erreur OCR :", erreur)
        return False, "Impossible d'analyser cette image."
