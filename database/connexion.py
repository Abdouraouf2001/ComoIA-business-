
import sqlite3
from pathlib import Path


# ==========================================
# CHEMIN DE LA BASE DE DONNÉES
# ==========================================

DOSSIER_BASE = Path(__file__).parent

CHEMIN_BASE = DOSSIER_BASE / "comoria_business.db"


# ==========================================
# CONNEXION À LA BASE
# ==========================================

def obtenir_connexion():

    connexion = sqlite3.connect(
        CHEMIN_BASE,
        check_same_thread=False
    )

    connexion.row_factory = sqlite3.Row

    # Active les clés étrangères (désactivées par défaut dans SQLite)
    connexion.execute("PRAGMA foreign_keys = ON")

    return connexion


# ==========================================
# CRÉATION DES TABLES
# ==========================================

def creer_tables():

    connexion = obtenir_connexion()

    try:

        curseur = connexion.cursor()

        # ------------------------------
        # TABLE PRODUITS
        # ------------------------------

        curseur.execute(
            """
            CREATE TABLE IF NOT EXISTS produits (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                nom TEXT NOT NULL,

                categorie TEXT,

                prix_achat REAL NOT NULL DEFAULT 0
                    CHECK (prix_achat >= 0),

                prix_vente REAL NOT NULL DEFAULT 0
                    CHECK (prix_vente >= 0),

                quantite INTEGER NOT NULL DEFAULT 0
                    CHECK (quantite >= 0),

                seuil_alerte INTEGER NOT NULL DEFAULT 0
                    CHECK (seuil_alerte >= 0),

                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ------------------------------
        # TABLE CLIENTS
        # (créée avant ventes, car ventes y fait référence)
        # ------------------------------

        # curseur.execute(
        #     """
        #     CREATE TABLE IF NOT EXISTS clients (

        #         id INTEGER PRIMARY KEY AUTOINCREMENT,

        #         nom TEXT NOT NULL,

        #         telephone TEXT,

        #         email TEXT,

        #         date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        #     )
        #     """
        # )

        # ------------------------------
        # TABLE VENTES
        # ------------------------------

        curseur.execute(
            """
            CREATE TABLE IF NOT EXISTS ventes (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                produit_id INTEGER NOT NULL,

                client_id INTEGER,

                quantite INTEGER NOT NULL
                    CHECK (quantite > 0),

                prix_unitaire REAL NOT NULL
                    CHECK (prix_unitaire >= 0),

                montant_total REAL NOT NULL
                    CHECK (montant_total >= 0),

                date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (produit_id)
                    REFERENCES produits(id),

                FOREIGN KEY (client_id)
                    REFERENCES clients(id)
            )
            """
        )

        # ------------------------------
        # TABLE DÉPENSES
        # ------------------------------

        curseur.execute(
            """
            CREATE TABLE IF NOT EXISTS depenses (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                description TEXT NOT NULL,

                montant REAL NOT NULL
                    CHECK (montant >= 0),

                categorie TEXT,

                date_depense TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connexion.commit()

    except sqlite3.Error:

        connexion.rollback()

        raise

    finally:

        # La connexion est toujours fermée, même en cas d'erreur
        connexion.close()


