
import os

# ==========================================
# GOOGLE OAUTH
# ==========================================
# Ces valeurs viennent des variables d'environnement, jamais du code en
# clair (surtout si ce dépôt finit un jour sur GitHub, même en privé).
#
# En local (PowerShell) :
#   setx COMORIA_GOOGLE_CLIENT_ID "ton-client-id"
#   setx COMORIA_GOOGLE_CLIENT_SECRET "ton-client-secret"
#   setx COMORIA_GOOGLE_REDIRECT_URI "http://localhost:8501"
# (ferme et rouvre VS Code après un setx pour qu'il prenne effet)
#
# Sur Streamlit Cloud : Settings → Secrets, format TOML avec les mêmes noms.

GOOGLE_CLIENT_ID = os.environ.get("COMORIA_GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("COMORIA_GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.environ.get(
    "COMORIA_GOOGLE_REDIRECT_URI", "http://localhost:8501"
)
