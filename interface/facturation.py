import base64
from contextlib import closing
import streamlit as st

from database.connexion import obtenir_connexion
from fonctions.facturation import creer_facture, generer_pdf_facture


def afficher_apercu_imprimable(pdf_bytes: bytes, cle: str):
    """Affiche le PDF dans un iframe pour impression directe."""
    if not pdf_bytes:
        st.error("Impossible de générer le PDF.")
        return

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{pdf_base64}" '
        f'width="100%" height="600" '
        f'style="border:1px solid #EAECEF;border-radius:10px;" '
        f'title="apercu_facture_{cle}"></iframe>',
        unsafe_allow_html=True
    )


def obtenir_historique_client(client_id: int, utilisateur_id: int) -> int:
    """Retourne le nombre de factures précédentes d'un client."""
    if client_id is None:
        return 0

    with closing(obtenir_connexion()) as connexion:
        resultat = connexion.execute(
            """
            SELECT COUNT(*) 
            FROM factures 
            WHERE client_id = ? AND utilisateur_id = ?
            """,
            (client_id, utilisateur_id)
        ).fetchone()
        return resultat[0] if resultat else 0


def afficher_page_facturation():
    st.title("🧾 Facturation")
    st.write("Créez et enregistrez vos factures.")

    uid = st.session_state.utilisateur_id

    # =========================================================
    # INITIALISATION DU PANIER
    # =========================================================
    if "articles_facture" not in st.session_state:
        st.session_state.articles_facture = []

    # =========================================================
    # CHARGEMENT DES DONNÉES
    # =========================================================
    with closing(obtenir_connexion()) as connexion:
        clients = connexion.execute(
            "SELECT id, nom, telephone FROM clients "
            "WHERE utilisateur_id = ? ORDER BY nom",
            (uid,)
        ).fetchall()

        produits = connexion.execute(
            "SELECT id, nom, prix_vente, quantite FROM produits "
            "WHERE utilisateur_id = ? ORDER BY nom",
            (uid,)
        ).fetchall()

    # =========================================================
    # CRÉATION D'UNE FACTURE
    # =========================================================
    st.subheader("➕ Nouvelle facture")

    # ---------------------------------------------------------
    # CLIENT (existant ou nouveau)
    # ---------------------------------------------------------
    st.subheader("👤 Client")

    type_client = st.radio(
        "Type de client",
        ["Client existant", "Nouveau client"],
        horizontal=True,
        key="type_client_facture"
    )

    client_id = None
    nb_visites = 0
    remise_suggeree = 0.0   # en pourcentage

    if type_client == "Client existant":
        if not clients:
            st.warning("Aucun client enregistré. Choisissez « Nouveau client ».")
        else:
            clients_dict = {
                f"{c['nom']} - {c['telephone'] or 'Sans téléphone'}": c["id"]
                for c in clients
            }
            client_selectionne = st.selectbox(
                "Sélectionner le client",
                list(clients_dict.keys()),
                key="client_facture"
            )
            client_id = clients_dict[client_selectionne]
            nb_visites = obtenir_historique_client(client_id, uid)

    else:
        # Formulaire de création rapide de client
        with st.form("form_nouveau_client_facture", clear_on_submit=False):
            st.write("**Créer un nouveau client**")
            nom_client = st.text_input("Nom du client *", key="nouveau_client_nom")
            tel_client = st.text_input("Téléphone", key="nouveau_client_tel")
            email_client = st.text_input("Email", key="nouveau_client_email")
            adresse_client = st.text_input("Adresse", key="nouveau_client_adresse")

            submitted_client = st.form_submit_button(
                "💾 Enregistrer le client", use_container_width=True
            )

            if submitted_client:
                if not nom_client.strip():
                    st.error("Le nom du client est obligatoire.")
                else:
                    with closing(obtenir_connexion()) as connexion:
                        curseur = connexion.execute(
                            """
                            INSERT INTO clients
                            (nom, telephone, email, adresse, utilisateur_id)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                nom_client.strip(),
                                tel_client.strip() or None,
                                email_client.strip() or None,
                                adresse_client.strip() or None,
                                uid
                            )
                        )
                        connexion.commit()
                        client_id = curseur.lastrowid

                    st.session_state["client_id_temp"] = client_id
                    st.success(f"Client « {nom_client} » enregistré avec succès.")
                    st.rerun()

    # Récupération du client_id si on vient de le créer
    if client_id is None and "client_id_temp" in st.session_state:
        client_id = st.session_state["client_id_temp"]
        nb_visites = 0

    # ---------------------------------------------------------
    # AFFICHAGE FIDÉLITÉ + SUGGESTION DE REMISE
    # ---------------------------------------------------------
    if client_id is not None:
        if nb_visites == 0:
            st.info("🆕 Nouveau client")
        elif nb_visites == 1:
            st.info("👋 Client déjà venu **1 fois**")
        else:
            st.success(f"⭐ Client fidèle : **{nb_visites} visites** précédentes")

        # Suggestion de remise selon le nombre de visites
        if nb_visites >= 10:
            remise_suggeree = 10.0
            st.caption("🎁 Remise fidélité suggérée : **10 %**")
        elif nb_visites >= 5:
            remise_suggeree = 7.0
            st.caption("🎁 Remise fidélité suggérée : **7 %**")
        elif nb_visites >= 3:
            remise_suggeree = 5.0
            st.caption("🎁 Remise fidélité suggérée : **5 %**")
        elif nb_visites >= 1:
            remise_suggeree = 3.0
            st.caption("🎁 Remise fidélité suggérée : **3 %**")

    st.divider()

    # ---------------------------------------------------------
    # PRODUITS
    # ---------------------------------------------------------
    st.subheader("📦 Ajouter un produit")

    if not produits:
        st.warning("Aucun produit n'est enregistré. Ajoutez d'abord un produit.")
    else:
        produits_disponibles = [p for p in produits if p["quantite"] > 0]

        if not produits_disponibles:
            st.warning("Aucun produit n'est actuellement disponible en stock.")
        else:
            produits_dict = {
                f"{p['nom']} — {p['prix_vente']:,.0f} KMF (Stock : {p['quantite']})": p
                for p in produits_disponibles
            }
            produit_selectionne = st.selectbox(
                "Produit", list(produits_dict.keys()), key="produit_facture"
            )
            produit = produits_dict[produit_selectionne]

            col1, col2 = st.columns(2)
            with col1:
                quantite = st.number_input(
                    "Quantité",
                    min_value=1,
                    max_value=int(produit["quantite"]),
                    value=1,
                    step=1,
                    key="quantite_facture"
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("➕ Ajouter au panier", use_container_width=True):
                    deja_dans_panier = False
                    for article in st.session_state.articles_facture:
                        if article["produit_id"] == produit["id"]:
                            deja_dans_panier = True
                            nouvelle_quantite = article["quantite"] + quantite
                            if nouvelle_quantite > produit["quantite"]:
                                st.error(
                                    f"Stock insuffisant. "
                                    f"Stock disponible : {produit['quantite']}."
                                )
                            else:
                                article["quantite"] = nouvelle_quantite
                                article["montant"] = (
                                    nouvelle_quantite * article["prix_unitaire"]
                                )
                                st.success("Quantité mise à jour.")
                            break

                    if not deja_dans_panier:
                        montant = quantite * produit["prix_vente"]
                        st.session_state.articles_facture.append({
                            "produit_id": produit["id"],
                            "nom": produit["nom"],
                            "quantite": quantite,
                            "prix_unitaire": produit["prix_vente"],
                            "montant": montant
                        })
                        st.success(f"{produit['nom']} ajouté à la facture.")

    # ---------------------------------------------------------
    # PANIER
    # ---------------------------------------------------------
    st.divider()
    st.subheader("🧾 Détails de la facture")

    articles = st.session_state.articles_facture

    if not articles:
        st.info("Aucun article ajouté à la facture.")
    else:
        total_brut = 0
        for index, article in enumerate(articles):
            montant = article["quantite"] * article["prix_unitaire"]
            total_brut += montant

            col1, col2, col3, col4, col5 = st.columns([3, 1, 1.5, 1.5, 0.7])
            with col1:
                st.write(f"**{article['nom']}**")
            with col2:
                st.write(article["quantite"])
            with col3:
                st.write(f"{article['prix_unitaire']:,.0f} KMF")
            with col4:
                st.write(f"{montant:,.0f} KMF")
            with col5:
                if st.button("🗑️", key=f"supprimer_article_{index}"):
                    st.session_state.articles_facture.pop(index)
                    st.rerun()

        st.divider()

        # ---------------------------------------------------------
        # REMISE (avec suggestion fidélité)
        # ---------------------------------------------------------
        st.subheader("💰 Total")

        # Calcul de la remise suggérée en KMF
        remise_montant_suggere = 0.0
        if remise_suggeree > 0 and total_brut > 0:
            remise_montant_suggere = round(total_brut * (remise_suggeree / 100))

        col1, col2 = st.columns(2)
        with col1:
            remise = st.number_input(
                "Remise (KMF)",
                min_value=0.0,
                max_value=float(total_brut),
                value=float(remise_montant_suggere),
                step=500.0,
                key="remise_facture",
                help="Vous pouvez modifier ou mettre 0 si vous ne voulez pas appliquer la remise."
            )
        with col2:
            total_final = total_brut - remise
            st.metric("Total à payer", f"{total_final:,.0f} KMF")

        note = st.text_area(
            "📝 Note / Observation",
            placeholder="Exemple : paiement partiel, commande spéciale...",
            key="note_facture"
        )

        st.divider()

        # ---------------------------------------------------------
        # ACTIONS
        # ---------------------------------------------------------
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Vider la facture", use_container_width=True):
                st.session_state.articles_facture = []
                st.rerun()
        with col2:
            if st.button(
                "✅ Créer la facture", type="primary", use_container_width=True
            ):
                if client_id is None:
                    st.error("Veuillez d'abord sélectionner ou créer un client.")
                else:
                    succes, resultat, facture_id = creer_facture(
                        client_id=client_id,
                        articles=articles,
                        remise=remise,
                        note=note,
                        utilisateur_id=uid
                    )
                    if succes:
                        # Nettoyage
                        st.session_state.pop("client_id_temp", None)
                        st.session_state.articles_facture = []
                        st.session_state["message_facture"] = (
                            f"✅ Facture {resultat} créée avec succès ! "
                            "Le stock a été mis à jour et la vente enregistrée."
                        )
                        st.session_state["derniere_facture_id"] = facture_id
                        st.session_state["derniere_facture_numero"] = resultat
                        st.rerun()
                    else:
                        st.error(f"❌ Impossible de créer la facture : {resultat}")

    # Message de succès
    if "message_facture" in st.session_state:
        st.success(st.session_state.pop("message_facture"))

    # Téléchargement + aperçu de la dernière facture créée
    if "derniere_facture_id" in st.session_state:
        pdf_bytes = generer_pdf_facture(
            st.session_state["derniere_facture_id"], uid
        )
        if pdf_bytes:
            st.download_button(
                f"📄 Télécharger {st.session_state['derniere_facture_numero']} en PDF",
                data=pdf_bytes,
                file_name=f"{st.session_state['derniere_facture_numero']}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="pdf_derniere_facture"
            )
            with st.expander("🖨️ Aperçu et impression"):
                st.caption(
                    "Utilisez l'icône imprimante de la barre d'outils "
                    "ci-dessous (ou Ctrl+P) pour imprimer directement."
                )
                afficher_apercu_imprimable(pdf_bytes, "nouvelle")

    # =========================================================
    # HISTORIQUE DES FACTURES
    # =========================================================
    st.divider()
    st.subheader("📋 Historique des factures")

    with closing(obtenir_connexion()) as connexion:
        factures = connexion.execute(
            """
            SELECT
                factures.id, factures.numero, factures.total_brut,
                factures.remise, factures.total_final, factures.note,
                factures.date_creation,
                clients.nom AS client_nom,
                clients.telephone AS client_telephone
            FROM factures
            LEFT JOIN clients ON factures.client_id = clients.id
            WHERE factures.utilisateur_id = ?
            ORDER BY factures.id DESC
            """,
            (uid,)
        ).fetchall()

    if not factures:
        st.info("Aucune facture enregistrée pour le moment.")
    else:
        st.write(f"**{len(factures)} facture(s) enregistrée(s)**")

        for facture in factures:
            client_nom = facture["client_nom"] or "Client supprimé"

            with st.expander(
                f"🧾 {facture['numero']} — {client_nom} — "
                f"{facture['total_final']:,.0f} KMF"
            ):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write("**Client**")
                    st.write(client_nom)
                    if facture["client_telephone"]:
                        st.write(facture["client_telephone"])
                with col2:
                    st.write("**Date**")
                    st.write(facture["date_creation"])
                    st.write("**Total brut**")
                    st.write(f"{facture['total_brut']:,.0f} KMF")
                with col3:
                    st.write("**Remise**")
                    st.write(f"{facture['remise']:,.0f} KMF")
                    st.write("**Total final**")
                    st.write(f"{facture['total_final']:,.0f} KMF")

                pdf_bytes = generer_pdf_facture(facture["id"], uid)
                if pdf_bytes:
                    st.download_button(
                        "📄 Télécharger en PDF",
                        data=pdf_bytes,
                        file_name=f"{facture['numero']}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"pdf_{facture['id']}"
                    )

                    if st.toggle(
                        "🖨️ Aperçu et impression",
                        key=f"apercu_{facture['id']}"
                    ):
                        st.caption(
                            "Utilisez l'icône imprimante de la barre d'outils "
                            "ci-dessous (ou Ctrl+P) pour imprimer directement."
                        )
                        afficher_apercu_imprimable(pdf_bytes, str(facture["id"]))

                st.write("### 📦 Articles")
                with closing(obtenir_connexion()) as connexion:
                    lignes = connexion.execute(
                        """
                        SELECT
                            lignes_facture.quantite,
                            lignes_facture.prix_unitaire,
                            lignes_facture.montant,
                            produits.nom AS produit_nom
                        FROM lignes_facture
                        LEFT JOIN produits ON lignes_facture.produit_id = produits.id
                        WHERE lignes_facture.facture_id = ?
                        ORDER BY lignes_facture.id
                        """,
                        (facture["id"],)
                    ).fetchall()

                if lignes:
                    for ligne in lignes:
                        produit_nom = ligne["produit_nom"] or "Produit supprimé"
                        st.write(
                            f"• **{produit_nom}** — "
                            f"{ligne['quantite']} × "
                            f"{ligne['prix_unitaire']:,.0f} KMF = "
                            f"**{ligne['montant']:,.0f} KMF**"
                        )
                else:
                    st.info("Aucun article trouvé pour cette facture.")

                if facture["note"]:
                    st.write("### 📝 Note")
                    st.write(facture["note"])
