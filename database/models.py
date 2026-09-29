
from database.connexion import obtenir_connexion


def _colonne_existe(curseur, table: str, colonne: str) -> bool:
    infos = curseur.execute(f"PRAGMA table_info({table})").fetchall()
    return any(ligne[1] == colonne for ligne in infos)


def _ajouter_colonne_si_absente(curseur, table: str, colonne: str, definition: str):
    if not _colonne_existe(curseur, table, colonne):
        curseur.execute(f"ALTER TABLE {table} ADD COLUMN {colonne} {definition}")


def creer_tables():
    connexion = obtenir_connexion()
    curseur = connexion.cursor()

    # ---------- UTILISATEURS ----------
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT,
            provider TEXT DEFAULT 'local',
            google_id TEXT UNIQUE,
            role TEXT NOT NULL DEFAULT 'commercant',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    _ajouter_colonne_si_absente(curseur, "utilisateurs", "nom_entreprise", "TEXT")
    _ajouter_colonne_si_absente(curseur, "utilisateurs", "telephone_entreprise", "TEXT")
    _ajouter_colonne_si_absente(curseur, "utilisateurs", "adresse_entreprise", "TEXT")

    # ---------- PRODUITS ----------
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            categorie TEXT,
            prix_achat REAL DEFAULT 0,
            prix_vente REAL DEFAULT 0,
            quantite INTEGER DEFAULT 0,
            seuil_alerte INTEGER DEFAULT 0,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    _ajouter_colonne_si_absente(curseur, "produits", "utilisateur_id", "INTEGER")

    # ---------- VENTES ----------
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produit_id INTEGER,
            quantite INTEGER NOT NULL,
            prix_unitaire REAL NOT NULL,
            montant_total REAL NOT NULL,
            date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produit_id) REFERENCES produits(id)
        )
    """)
    _ajouter_colonne_si_absente(curseur, "ventes", "utilisateur_id", "INTEGER")

    # ---------- DÉPENSES ----------
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            montant REAL NOT NULL,
            categorie TEXT,
            date_depense TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    _ajouter_colonne_si_absente(curseur, "depenses", "utilisateur_id", "INTEGER")

    # ---------- CLIENTS ----------
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            telephone TEXT,
            email TEXT,
            adresse TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    _ajouter_colonne_si_absente(curseur, "clients", "utilisateur_id", "INTEGER")

    # ---------- FACTURES ----------
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS factures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            client_id INTEGER,
            utilisateur_id INTEGER,
            total_brut REAL NOT NULL,
            remise REAL DEFAULT 0,
            total_final REAL NOT NULL,
            note TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)
    _ajouter_colonne_si_absente(curseur, "factures", "utilisateur_id", "INTEGER")

    # ---------- LIGNES DE FACTURE ----------
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS lignes_facture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            facture_id INTEGER NOT NULL,
            produit_id INTEGER,
            quantite INTEGER NOT NULL,
            prix_unitaire REAL NOT NULL,
            montant REAL NOT NULL,
            FOREIGN KEY (facture_id) REFERENCES factures(id),
            FOREIGN KEY (produit_id) REFERENCES produits(id)
        )
    """)

    # ---------- TOKENS DE RÉCUPÉRATION ----------
    curseur.execute("""
        CREATE TABLE IF NOT EXISTS tokens_recuperation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expiration TIMESTAMP NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ---------- INDEX pour les performances ----------
    curseur.execute("CREATE INDEX IF NOT EXISTS idx_produits_utilisateur ON produits(utilisateur_id)")
    curseur.execute("CREATE INDEX IF NOT EXISTS idx_ventes_utilisateur ON ventes(utilisateur_id)")
    curseur.execute("CREATE INDEX IF NOT EXISTS idx_clients_utilisateur ON clients(utilisateur_id)")
    curseur.execute("CREATE INDEX IF NOT EXISTS idx_factures_utilisateur ON factures(utilisateur_id)")
    curseur.execute("CREATE INDEX IF NOT EXISTS idx_depenses_utilisateur ON depenses(utilisateur_id)")
    curseur.execute("CREATE INDEX IF NOT EXISTS idx_tokens_email ON tokens_recuperation(email)")

    connexion.commit()
    connexion.close()

