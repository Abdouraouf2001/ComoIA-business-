import hashlib
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta

from database.connexion import obtenir_connexion


# ==========================================
# HACHAGE
# ==========================================
def hasher_mot_de_passe(mot_de_passe: str) -> str:
    """Attention : SHA-256 sans sel. À remplacer par bcrypt en production."""
    return hashlib.sha256(mot_de_passe.encode("utf-8")).hexdigest()


# ==========================================
# CRÉATION / CONNEXION
# ==========================================
def creer_utilisateur(nom: str, email: str, mot_de_passe: str, role: str = "commercant"):
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
        return False, "Cette adresse e-mail est déjà utilisée."
    except Exception as erreur:
        print("Erreur création utilisateur :", erreur)
        return False, "Une erreur est survenue lors de la création du compte."


def verifier_connexion(email: str, mot_de_passe: str):
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


def obtenir_utilisateur_par_email(email: str):
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


# ==========================================
# RÉCUPÉRATION DE MOT DE PASSE
# ==========================================
def creer_token_recuperation(email: str) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expiration = datetime.now() + timedelta(minutes=30)

    with closing(obtenir_connexion()) as connexion:
        connexion.execute(
            "DELETE FROM tokens_recuperation WHERE email = ?",
            (email.strip().lower(),)
        )
        connexion.execute(
            """
            INSERT INTO tokens_recuperation (email, token_hash, expiration)
            VALUES (?, ?, ?)
            """,
            (email.strip().lower(), token_hash, expiration.isoformat())
        )
        connexion.commit()
    return token


def verifier_token_recuperation(email: str, token: str) -> bool:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    email_normalise = email.strip().lower()

    with closing(obtenir_connexion()) as connexion:
        ligne = connexion.execute(
            """
            SELECT expiration FROM tokens_recuperation
            WHERE email = ? AND token_hash = ?
            ORDER BY id DESC LIMIT 1
            """,
            (email_normalise, token_hash)
        ).fetchone()

        if ligne is None:
            return False

        expiration = datetime.fromisoformat(ligne["expiration"])
        return datetime.now() <= expiration


def reinitialiser_mot_de_passe(email: str, token: str, nouveau_mot_de_passe: str):
    email_normalise = email.strip().lower()

    if not verifier_token_recuperation(email_normalise, token):
        return False, "Ce code de récupération est invalide ou a expiré."

    if len(nouveau_mot_de_passe) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."

    with closing(obtenir_connexion()) as connexion:
        connexion.execute(
            "UPDATE utilisateurs SET mot_de_passe = ? WHERE email = ?",
            (hasher_mot_de_passe(nouveau_mot_de_passe), email_normalise)
        )
        # Token à usage unique
        connexion.execute(
            "DELETE FROM tokens_recuperation WHERE email = ?",
            (email_normalise,)
        )
        connexion.commit()

    return True, "Mot de passe mis à jour avec succès."


# ==========================================
# PROFIL ENTREPRISE
# ==========================================
def obtenir_profil_entreprise(utilisateur_id: int):
    with closing(obtenir_connexion()) as connexion:
        profil = connexion.execute(
            """
            SELECT nom, nom_entreprise, telephone_entreprise, adresse_entreprise
            FROM utilisateurs
            WHERE id = ?
            """,
            (utilisateur_id,)
        ).fetchone()

        if profil is None:
            return None

        return {
            "nom": profil["nom"],
            "nom_entreprise": profil["nom_entreprise"],
            "telephone_entreprise": profil["telephone_entreprise"],
            "adresse_entreprise": profil["adresse_entreprise"],
        }


def modifier_profil_entreprise(
    utilisateur_id: int,
    nom_entreprise: str,
    telephone_entreprise: str,
    adresse_entreprise: str
):
    with closing(obtenir_connexion()) as connexion:
        connexion.execute(
            """
            UPDATE utilisateurs
            SET nom_entreprise = ?, telephone_entreprise = ?, adresse_entreprise = ?
            WHERE id = ?
            """,
            (
                nom_entreprise.strip() or None,
                telephone_entreprise.strip() or None,
                adresse_entreprise.strip() or None,
                utilisateur_id,
            )
        )
        connexion.commit()


# ==========================================
# ADMINISTRATION
# ==========================================
def lister_utilisateurs():
    with closing(obtenir_connexion()) as connexion:
        return connexion.execute(
            """
            SELECT id, nom, email, role, provider, date_creation
            FROM utilisateurs
            ORDER BY date_creation DESC
            """
        ).fetchall()


def compter_utilisateurs_par_role():
    with closing(obtenir_connexion()) as connexion:
        lignes = connexion.execute(
            "SELECT role, COUNT(*) AS total FROM utilisateurs GROUP BY role"
        ).fetchall()
        return {ligne["role"]: ligne["total"] for ligne in lignes}


def modifier_role_utilisateur(utilisateur_id: int, nouveau_role: str):
    with closing(obtenir_connexion()) as connexion:
        connexion.execute(
            "UPDATE utilisateurs SET role = ? WHERE id = ?",
            (nouveau_role, utilisateur_id)
        )
        connexion.commit()


def supprimer_utilisateur(utilisateur_id: int):
    with closing(obtenir_connexion()) as connexion:
        connexion.execute(
            "DELETE FROM utilisateurs WHERE id = ?",
            (utilisateur_id,)
        )
        connexion.commit()
