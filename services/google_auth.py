import requests

from config.settings import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI
)


GOOGLE_AUTH_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth"
)

GOOGLE_TOKEN_URL = (
    "https://oauth2.googleapis.com/token"
)

GOOGLE_USERINFO_URL = (
    "https://www.googleapis.com/oauth2/v2/userinfo"
)


def obtenir_url_connexion_google():

    if not GOOGLE_CLIENT_ID:

        return None

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account"
    }

    parametres = "&".join(
        f"{cle}={requests.utils.quote(str(valeur))}"
        for cle, valeur in params.items()
    )

    return f"{GOOGLE_AUTH_URL}?{parametres}"


def obtenir_token_google(code):

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:

        return None

    donnees = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": GOOGLE_REDIRECT_URI
    }

    try:

        reponse = requests.post(
            GOOGLE_TOKEN_URL,
            data=donnees,
            timeout=10
        )

        reponse.raise_for_status()

        return reponse.json()

    except Exception as erreur:

        print(
            "Erreur Google OAuth :",
            erreur
        )

        return None


def obtenir_informations_google(access_token):

    try:

        reponse = requests.get(
            GOOGLE_USERINFO_URL,
            headers={
                "Authorization": f"Bearer {access_token}"
            },
            timeout=10
        )

        reponse.raise_for_status()

        return reponse.json()

    except Exception as erreur:

        print(
            "Erreur récupération profil Google :",
            erreur
        )

        return None
