"""
Palette de couleurs centralisée pour ComorIA Business AI.

But : éviter que chaque page réécrive ses propres codes hexadécimaux.
Usage : from config.colors import VERT, ROUGE, ...
"""

# ==========================================
# COULEURS DE MARQUE
# ==========================================
VERT = "#00843D"           # Vert principal (boutons, valeurs positives)
VERT_FONCE = "#006B32"      # Dégradés, survol de bouton
VERT_CLAIR = "#A8D5BA"       # Extrémité claire des dégradés de graphiques
VERT_FOND = "#E6F4EA"        # Fond des badges/icônes verts
VERT_FONCE_TEXTE = "#085041"  # Texte sur fond vert clair

# ==========================================
# COULEURS D'ALERTE
# ==========================================
ROUGE = "#D64545"
ROUGE_FONCE = "#791F1F"
ROUGE_FOND = "#FCEBEB"

ORANGE_FONCE = "#854F0B"
ORANGE_FOND = "#FAEEDA"
JAUNE_BORDURE = "#FFE082"
JAUNE_FOND = "#FFF8E1"

# ==========================================
# NEUTRES / TEXTE
# ==========================================
FOND_PAGE = "#F5F7F7"
FOND_CARTE = "#FFFFFF"
BORDURE = "#EAECEF"
TEXTE_PRINCIPAL = "#111827"
TEXTE_SECONDAIRE = "#6B7280"
TEXTE_MUET = "#9CA3AF"

# ==========================================
# ADMINISTRATION (distinct du vert commerçant)
# ==========================================
GRIS_FONCE = "#1F2937"
GRIS_TRES_FONCE = "#111827"

# ==========================================
# DIVERS (graphiques, ombres, bandeaux)
# ==========================================
GRILLE_GRAPHIQUE = "#F0F0F0"       # Lignes de grille Altair
OMBRE_CARTE = "rgba(16,24,40,0.04)"  # box-shadow des cartes KPI
BANNIERE_SOUS_TITRE = "rgba(255,255,255,0.85)"  # Texte clair sur bandeau vert/gris
