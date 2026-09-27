from fonctions.utilisateurs import obtenir_utilisateur_par_email, modifier_role_utilisateur

utilisateur = obtenir_utilisateur_par_email("guilbertahamada@gmail.com")

if utilisateur:
    modifier_role_utilisateur(utilisateur["id"], "administrateur")
    print("Fait :", utilisateur["nom"], "est maintenant administrateur.")
else:
    print("Aucun compte trouvé avec cet e-mail.")
 