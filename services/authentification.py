
import hashlib

from database.connexion import obtenir_connexion


# ==========================================
# HACHAGE DU MOT DE PASSE
# ==========================================

def hasher_mot_de_passe(mot_de_passe):

    return hashlib.sha256(
        mot_de_passe.encode("utf-8")
    ).hexdigest()


# ==========================================
# CREER UN UTILISATEUR
# ==========================================

def creer_utilisateur(
    nom,
    email,
    mot_de_passe,
    role="commercant"
):

    connexion = obtenir_connexion()
    curseur = connexion.cursor()

    mot_de_passe_hash = hasher_mot_de_passe(
        mot_de_passe
    )

    try:

        curseur.execute(
            """
            INSERT INTO utilisateurs
            (
                nom,
                email,
                mot_de_passe,
                provider,
                role
            )

            VALUES (?, ?, ?, ?, ?)
            """,
            (
                nom,
                email,
                mot_de_passe_hash,
                "local",
                role
            )
        )

        connexion.commit()

        return True, "Compte créé avec succès."

    except Exception as erreur:

        print("Erreur création utilisateur :", erreur)

        return False, (
            "Cette adresse e-mail est déjà utilisée."
        )

    finally:

        connexion.close()


# ==========================================
# VERIFIER LA CONNEXION
# ==========================================

def verifier_connexion(
    email,
    mot_de_passe
):

    connexion = obtenir_connexion()
    connexion.row_factory = None

    curseur = connexion.cursor()

    mot_de_passe_hash = hasher_mot_de_passe(
        mot_de_passe
    )

    curseur.execute(
        """
        SELECT
            id,
            nom,
            email,
            role,
            provider
        FROM utilisateurs

        WHERE email = ?
        AND mot_de_passe = ?
        """,
        (
            email.strip().lower(),
            mot_de_passe_hash
        )
    )

    utilisateur = curseur.fetchone()

    connexion.close()

    if utilisateur:

        return {
            "id": utilisateur[0],
            "nom": utilisateur[1],
            "email": utilisateur[2],
            "role": utilisateur[3],
            "provider": utilisateur[4]
        }

    return None


# ==========================================
# RECHERCHER UN UTILISATEUR PAR EMAIL
# ==========================================

def obtenir_utilisateur_par_email(email):

    connexion = obtenir_connexion()
    curseur = connexion.cursor()

    curseur.execute(
        """
        SELECT
            id,
            nom,
            email,
            role,
            provider,
            google_id
        FROM utilisateurs

        WHERE email = ?
        """,
        (
            email.strip().lower(),
        )
    )

    utilisateur = curseur.fetchone()

    connexion.close()

    if utilisateur:

        return {
            "id": utilisateur[0],
            "nom": utilisateur[1],
            "email": utilisateur[2],
            "role": utilisateur[3],
            "provider": utilisateur[4],
            "google_id": utilisateur[5]
        }

    return None


