import smtplib
from email.message import EmailMessage

from config.settings import (
    EMAIL_EXPEDITEUR,
    EMAIL_MOT_DE_PASSE,
    EMAIL_SERVEUR_SMTP,
    EMAIL_PORT_SMTP
)


def envoyer_email(
    destinataire,
    sujet,
    contenu
):

    if not EMAIL_EXPEDITEUR or not EMAIL_MOT_DE_PASSE:

        return False, (
            "Le service d'envoi d'e-mails "
            "n'est pas encore configuré."
        )

    message = EmailMessage()

    message["From"] = EMAIL_EXPEDITEUR
    message["To"] = destinataire
    message["Subject"] = sujet

    message.set_content(contenu)

    try:

        with smtplib.SMTP(
            EMAIL_SERVEUR_SMTP,
            EMAIL_PORT_SMTP
        ) as serveur:

            serveur.starttls()

            serveur.login(
                EMAIL_EXPEDITEUR,
                EMAIL_MOT_DE_PASSE
            )

            serveur.send_message(message)

        return True, "E-mail envoyé avec succès."

    except Exception as erreur:

        print(
            "Erreur envoi e-mail :",
            erreur
        )

        return False, (
            "Impossible d'envoyer l'e-mail."
        )


def envoyer_email_recuperation(
    destinataire,
    lien_recuperation
):

    sujet = "Réinitialisation de votre mot de passe - ComorIA Business"

    contenu = f"""
Bonjour,

Vous avez demandé la réinitialisation
de votre mot de passe ComorIA Business.

Cliquez sur le lien suivant pour continuer :

{lien_recuperation}

Ce lien est valable pendant 30 minutes.

Si vous n'êtes pas à l'origine de cette demande,
vous pouvez ignorer cet e-mail.

Cordialement,

L'équipe ComorIA Business
🇰🇲
"""

    return envoyer_email(
        destinataire,
        sujet,
        contenu
    )
