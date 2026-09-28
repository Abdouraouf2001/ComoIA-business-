from contextlib import closing

import streamlit as st
from database.connexion import obtenir_connexion
from fonctions.facturation import creer_facture


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
    # CRÉATION D'UNE FACTURE
    # =========================================================

    st.subheader("➕ Nouvelle facture")

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
    # CLIENT
    # =========================================================

    if not clients:
        st.warning(
            "Aucun client n'est enregistré. "
            "Ajoutez d'abord un client dans le module Clients."
        )
    else:

        st.subheader("👤 Client")

        clients_dict = {
            f"{client['nom']} - {client['telephone'] or 'Sans téléphone'}":
            client["id"]
            for client in clients
        }

        client_selectionne = st.selectbox(
            "Sélectionner le client",
            list(clients_dict.keys()),
            key="client_facture"
        )

        client_id = clients_dict[client_selectionne]

        st.divider()

        # =====================================================
        # PRODUITS
        # =====================================================

        st.subheader("📦 Ajouter un produit")

        if not produits:
            st.warning("Aucun produit n'est enregistré. Ajoutez d'abord un produit.")

        else:
            produits_disponibles = [p for p in produits if p["quantite"] > 0]

            if not produits_disponibles:
                st.warning("Aucun produit n'est actuellement disponible en stock.")

            else:
                produits_dict = {
                    f"{produit['nom']} — "
                    f"{produit['prix_vente']:,.0f} KMF "
                    f"(Stock : {produit['quantite']})":
                    produit
                    for produit in produits_disponibles
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

                        # Vaut True dès qu'on a trouvé la ligne correspondante
                        # dans le panier, que la fusion réussisse ou non — ça
                        # évite d'ajouter une seconde ligne en double quand la
                        # fusion échoue faute de stock (bug corrigé).
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

        # =====================================================
        # PANIER
        # =====================================================

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

            # =================================================
            # REMISE
            # =================================================

            st.subheader("💰 Total")

            col1, col2 = st.columns(2)

            with col1:
                remise = st.number_input(
                    "Remise (KMF)",
                    min_value=0.0,
                    max_value=float(total_brut),
                    value=0.0,
                    step=500.0,
                    key="remise_facture"
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

            # =================================================
            # ACTIONS
            # =================================================

            col1, col2 = st.columns(2)

            with col1:
                if st.button("🧹 Vider la facture", use_container_width=True):
                    st.session_state.articles_facture = []
                    st.rerun()

            with col2:
                if st.button(
                    "✅ Créer la facture", type="primary", use_container_width=True
                ):
                    succes, resultat = creer_facture(
                        client_id=client_id,
                        articles=articles,
                        remise=remise,
                        note=note,
                        utilisateur_id=uid
                    )

                    if succes:
                        st.session_state.articles_facture = []
                        st.session_state["message_facture"] = (
                            f"✅ Facture {resultat} créée avec succès ! "
                            "Le stock a été mis à jour et la vente enregistrée."
                        )
                        st.rerun()
                    else:
                        st.error(f"❌ Impossible de créer la facture : {resultat}")

    if "message_facture" in st.session_state:
        st.success(st.session_state.pop("message_facture"))

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
                clients.nom AS client_nom, clients.telephone AS client_telephone
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

                st.write("### 📦 Articles")

                with closing(obtenir_connexion()) as connexion:
                    lignes = connexion.execute(
                        """
                        SELECT
                            lignes_facture.quantite, lignes_facture.prix_unitaire,
                            lignes_facture.montant, produits.nom AS produit_nom
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
