
from database.connexion import obtenir_connexion


def creer_tables():

    connexion = obtenir_connexion()
    curseur = connexion.cursor()

    # ==========================================
    # TABLE UTILISATEURS
    # ==========================================

    curseur.execute(
        """
        CREATE TABLE IF NOT EXISTS utilisateurs (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nom TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            mot_de_passe TEXT,

            provider TEXT DEFAULT 'local',

            google_id TEXT UNIQUE,

            role TEXT NOT NULL DEFAULT 'commercant',

            date_creation TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ==========================================
    # TABLE PRODUITS
    # ==========================================

    curseur.execute(
        """
        CREATE TABLE IF NOT EXISTS produits (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nom TEXT NOT NULL,

            categorie TEXT,

            prix_achat REAL DEFAULT 0,

            prix_vente REAL DEFAULT 0,

            quantite INTEGER DEFAULT 0,

            seuil_alerte INTEGER DEFAULT 0,

            date_creation TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ==========================================
    # TABLE VENTES
    # ==========================================

    curseur.execute(
        """
        CREATE TABLE IF NOT EXISTS ventes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            produit_id INTEGER,

            quantite INTEGER NOT NULL,

            prix_unitaire REAL NOT NULL,

            prix_unitaire REAL DEFAULT 0,

            montant_total REAL NOT NULL,

            date_vente TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (produit_id)
            REFERENCES produits(id)
        )
        """
    )

    # ==========================================
    # TABLE DEPENSES
    # ==========================================

    curseur.execute(
        """
        CREATE TABLE IF NOT EXISTS depenses (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            description TEXT NOT NULL,

            montant REAL NOT NULL,

            categorie TEXT,

            date_depense TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    colones_ventes = [
        ligne[1]
        for ligne in curseur.execute(
            "PRAGMA table_info(ventes)"
        ).fetchall()   
    ]
    if "prix_achat_unitaire" not in colones_ventes:
        curseur.execute(
            """
           ALTER TABLE ventes ADD COLUMN 
           prix_achat_unitaire REAL DEFAULT 0
            """
        )

    # ==========================================
    # TABLE CLIENTS
    # ==========================================

    curseur.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nom TEXT NOT NULL,

            telephone TEXT,

            email TEXT,

            adresse TEXT,

            date_creation TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ==========================================
    # TABLE TOKENS DE RECUPERATION
    # ==========================================

    curseur.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens_recuperation (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            email TEXT NOT NULL,

            token_hash TEXT NOT NULL,

            expiration TIMESTAMP NOT NULL,

            date_creation TIMESTAMP
            DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connexion.commit()

    connexion.close()
