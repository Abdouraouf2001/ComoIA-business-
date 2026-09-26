import hashlib
import sqlite3
from contextlib import closing

from database.connexion import obtenir_connexion


# ==========================================
# HACHAGE DU MOT DE PASSE
# ==========================================

def hasher_mot_de_passe(mot_de_passe):
    return hashlib.sha256(mot_de_passe.encode("utf-8")).hexdigest()


# ==========================================
# CREER UN UTILISATEUR
# ==========================================

def creer_utilisateur(nom, email, mot_de_passe, role="commercant"):

    email_normalise = email.strip().lower()
    mot_de_passe_hash = hasher_mot_de_passe(mot_de_passe)

    try:
        with closing(obtenir_connexion()) as connexion:
            connexion.execute(
                """
                INSERT INTO utilisateurs
                (nom, email, mot_de_passe, provider, role)
                VALUES (?, ?, ?, ?, ?)
                """,
                (nom.strip(), email_normalise, mot_de_passe_hash, "local", role)
            )
            connexion.commit()

        return True, "Compte créé avec succès."

    except sqlite3.IntegrityError:
        # email UNIQUE déjà pris — le seul cas où ce message est vrai
        return False, "Cette adresse e-mail est déjà utilisée."

    except Exception as erreur:
        print("Erreur création utilisateur :", erreur)
        return False, "Une erreur est survenue lors de la création du compte."


# ==========================================
# VERIFIER LA CONNEXION
# ==========================================

def verifier_connexion(email, mot_de_passe):

    mot_de_passe_hash = hasher_mot_de_passe(mot_de_passe)

    with closing(obtenir_connexion()) as connexion:
        utilisateur = connexion.execute(
            """
            SELECT id, nom, email, role, provider
            FROM utilisateurs
            WHERE email = ? AND mot_de_passe = ?
            """,
            (email.strip().lower(), mot_de_passe_hash)
        ).fetchone()

    if utilisateur:
        return {
            "id": utilisateur["id"],
            "nom": utilisateur["nom"],
            "email": utilisateur["email"],
            "role": utilisateur["role"],
            "provider": utilisateur["provider"],
        }

    return None


# ==========================================
# RECHERCHER UN UTILISATEUR PAR EMAIL
# ==========================================

def obtenir_utilisateur_par_email(email):

    with closing(obtenir_connexion()) as connexion:
        utilisateur = connexion.execute(
            """
            SELECT id, nom, email, role, provider, google_id
            FROM utilisateurs
            WHERE email = ?
            """,
            (email.strip().lower(),)
        ).fetchone()

    if utilisateur:
        return {
            "id": utilisateur["id"],
            "nom": utilisateur["nom"],
            "email": utilisateur["email"],
            "role": utilisateur["role"],
            "provider": utilisateur["provider"],
            "google_id": utilisateur["google_id"],
        }

    return None
