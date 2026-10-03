import base64
from contextlib import closing

import streamlit as st

from config.colors import (
    BORDURE,
    FOND_CARTE,
    FOND_PAGE,
    TEXTE_MUET,
    TEXTE_PRINCIPAL,
    TEXTE_SECONDAIRE,
    VERT,
)

from database.connexion import obtenir_connexion

from fonctions.facturation import (
    creer_facture,
    generer_pdf_facture,
)


# ============================================================
# OUTILS
# ============================================================

def _apercu_pdf(pdf_bytes, cle="facture"):
    """Affiche un aperçu PDF directement dans Streamlit."""

    pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

    st.markdown(
        f"""
        <iframe
            src="data:application/pdf;base64,{pdf_base64}"
            width="100%"
            height="700"
            style="
                border:1px solid {BORDURE};
                border-radius:12px;
                background:white;
            "
            title="{cle}">
        </iframe>
        """,
        unsafe_allow_html=True,
    )


def _initialiser_panier():
    """Crée le panier dans la session s'il n'existe pas."""

    if "panier_vente" not in st.session_state:
        st.session_state["panier_vente"] = []


def _vider_panier():
    """Vide le panier."""

    st.session_state["panier_vente"] = []


def _total_panier():
    """Calcule le total du panier."""

    return sum(
        article["quantite"] * article["prix_unitaire"]
        for article in st.session_state["panier_vente"]
    )


def _ajouter_au_panier(produit, quantite):
    """Ajoute un produit au panier ou augmente sa quantité."""

    panier = st.session_state["panier_vente"]

    for article in panier:
        if article["produit_id"] == produit["id"]:
            nouvelle_quantite = article["quantite"] + quantite

            if nouvelle_quantite > produit["quantite"]:
                st.error(
                    f"Stock insuffisant pour « {produit['nom']} ». "
                    f"Disponible : {produit['quantite']}."
                )
                return False

            article["quantite"] = nouvelle_quantite
            return True

    if quantite > produit["quantite"]:
        st.error(
            f"Stock insuffisant pour « {produit['nom']} ». "
            f"Disponible : {produit['quantite']}."
        )
        return False

    panier.append(
        {
            "produit_id": produit["id"],
            "nom": produit["nom"],
            "quantite": quantite,
            "prix_unitaire": produit["prix_vente"],
        }
    )

    return True


# ============================================================
# PAGE VENTE
# ============================================================

def afficher_page_ventes():

    _initialiser_panier()

    uid = st.session_state.get("utilisateur_id")

    if not uid:
        st.error("Utilisateur non connecté.")
        return

    # --------------------------------------------------------
    # STYLE
    # --------------------------------------------------------

    st.markdown(
        f"""
        <style>

        .vente-titre {{
            color: {TEXTE_PRINCIPAL};
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 5px;
        }}

        .vente-sous-titre {{
            color: {TEXTE_SECONDAIRE};
            font-size: 15px;
            margin-bottom: 20px;
        }}

        .carte-total {{
            background: {FOND_CARTE};
            border: 1px solid {BORDURE};
            border-radius: 12px;
            padding: 18px;
            text-align: center;
        }}

        .total-label {{
            color: {TEXTE_SECONDAIRE};
            font-size: 14px;
        }}

        .total-value {{
            color: {VERT};
            font-size: 28px;
            font-weight: 700;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="vente-titre">💰 Nouvelle vente</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="vente-sous-titre">'
        "Créez une vente complète : client → produits → panier → facture."
        "</div>",
        unsafe_allow_html=True,
    )

    # ========================================================
    # FACTURE GÉNÉRÉE
    # ========================================================

    if "derniere_facture_id" in st.session_state:

        facture_id = st.session_state["derniere_facture_id"]
        numero_facture = st.session_state.get(
            "derniere_facture_numero",
            f"FAC-{facture_id}",
        )

        st.success(
            f"✅ Vente enregistrée avec succès — Facture {numero_facture}"
        )

        pdf_bytes = generer_pdf_facture(facture_id, uid)

        if pdf_bytes:

            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    "📥 Télécharger la facture PDF",
                    data=pdf_bytes,
                    file_name=f"{numero_facture}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

            with col2:
                if st.button(
                    "🆕 Nouvelle vente",
                    use_container_width=True,
                    type="primary",
                ):
                    st.session_state.pop("derniere_facture_id", None)
                    st.session_state.pop("derniere_facture_numero", None)
                    _vider_panier()
                    st.rerun()

            afficher_apercu = st.toggle(
                "🖨️ Afficher la facture pour impression",
                key="afficher_apercu_facture",
            )

            if afficher_apercu:
                st.markdown("### 🧾 Aperçu de la facture")
                _apercu_pdf(
                    pdf_bytes,
                    f"facture_{facture_id}",
                )

        st.divider()

    # ========================================================
    # CHARGEMENT DES CLIENTS ET PRODUITS
    # ========================================================

    with closing(obtenir_connexion()) as connexion:

        clients = connexion.execute(
            """
            SELECT
                id,
                nom,
                telephone,
                email,
                adresse
            FROM clients
            WHERE utilisateur_id = ?
            ORDER BY nom ASC
            """,
            (uid,),
        ).fetchall()

        produits = connexion.execute(
            """
            SELECT
                id,
                nom,
                categorie,
                prix_vente,
                quantite
            FROM produits
            WHERE utilisateur_id = ?
            ORDER BY nom ASC
            """,
            (uid,),
        ).fetchall()

    # ========================================================
    # 1. CLIENT
    # ========================================================

    st.markdown("### 👤 1. Client")

    col_client, col_nouveau = st.columns([2, 1])

    with col_client:

        options_clients = {
            "💵 Client comptant": None
        }

        for client in clients:
            informations = client["nom"]

            if client["telephone"]:
                informations += f" — {client['telephone']}"

            options_clients[informations] = client["id"]

        noms_clients = list(options_clients.keys())

        selected_client_id = st.session_state.get(
            "client_vente_selectionne"
        )

        index_client = 0

        if selected_client_id is not None:

            for index, nom_client in enumerate(noms_clients):

                if options_clients[nom_client] == selected_client_id:
                    index_client = index
                    break

        choix_client = st.selectbox(
            "Sélectionner un client",
            noms_clients,
            index=index_client,
            key="select_client_vente",
        )

        client_id = options_clients[choix_client]

        st.session_state["client_vente_selectionne"] = client_id

    with col_nouveau:

        st.write("")

        if st.button(
            "➕ Nouveau client",
            use_container_width=True,
        ):
            st.session_state["afficher_formulaire_client_vente"] = True

    # ========================================================
    # FORMULAIRE NOUVEAU CLIENT
    # ========================================================

    if st.session_state.get(
        "afficher_formulaire_client_vente",
        False,
    ):

        with st.expander(
            "➕ Créer un nouveau client",
            expanded=True,
        ):

            with st.form("formulaire_nouveau_client_vente"):

                nom_client = st.text_input(
                    "Nom du client *"
                )

                col1, col2 = st.columns(2)

                with col1:
                    telephone_client = st.text_input(
                        "Téléphone"
                    )

                with col2:
                    email_client = st.text_input(
                        "E-mail"
                    )

                adresse_client = st.text_input(
                    "Adresse"
                )

                creer_client = st.form_submit_button(
                    "💾 Créer le client",
                    type="primary",
                    use_container_width=True,
                )

                if creer_client:

                    if not nom_client.strip():
                        st.error(
                            "Le nom du client est obligatoire."
                        )

                    else:

                        try:

                            with closing(obtenir_connexion()) as connexion:

                                curseur = connexion.execute(
                                    """
                                    INSERT INTO clients
                                    (
                                        nom,
                                        telephone,
                                        email,
                                        adresse,
                                        utilisateur_id
                                    )
                                    VALUES (?, ?, ?, ?, ?)
                                    """,
                                    (
                                        nom_client.strip(),
                                        telephone_client.strip() or None,
                                        email_client.strip() or None,
                                        adresse_client.strip() or None,
                                        uid,
                                    ),
                                )

                                nouveau_client_id = curseur.lastrowid

                                connexion.commit()

                            st.session_state[
                                "client_vente_selectionne"
                            ] = nouveau_client_id

                            st.session_state[
                                "afficher_formulaire_client_vente"
                            ] = False

                            st.success(
                                f"✅ Client « {nom_client.strip()} » créé."
                            )

                            st.rerun()

                        except Exception as erreur:

                            st.error(
                                "Impossible de créer le client."
                            )

                            print(
                                "Erreur création client vente :",
                                erreur,
                            )

    # ========================================================
    # 2. PRODUITS
    # ========================================================

    st.markdown("### 📦 2. Ajouter des produits")

    produits_disponibles = [
        produit
        for produit in produits
        if produit["quantite"] > 0
    ]

    if not produits_disponibles:

        st.warning(
            "⚠️ Aucun produit disponible en stock."
        )

    else:

        produits_dict = {
            produit["nom"]: produit
            for produit in produits_disponibles
        }

        col_produit, col_quantite, col_action = st.columns(
            [3, 1, 1]
        )

        with col_produit:

            produit_nom = st.selectbox(
                "Produit",
                list(produits_dict.keys()),
                key="produit_a_ajouter",
            )

            produit_selectionne = produits_dict[
                produit_nom
            ]

        with col_quantite:

            quantite = st.number_input(
                "Quantité",
                min_value=1,
                max_value=int(
                    produit_selectionne["quantite"]
                ),
                value=1,
                step=1,
                key="quantite_a_ajouter",
            )

        with col_action:

            st.write("")

            if st.button(
                "➕ Ajouter",
                use_container_width=True,
                type="primary",
            ):

                if _ajouter_au_panier(
                    produit_selectionne,
                    int(quantite),
                ):

                    st.success(
                        "Produit ajouté au panier."
                    )

                    st.rerun()

        st.caption(
            f"Stock disponible : "
            f"{produit_selectionne['quantite']} "
            f"unité(s) • "
            f"Prix : "
            f"{produit_selectionne['prix_vente']:,.0f} KMF"
        )

    # ========================================================
    # 3. PANIER
    # ========================================================

    st.markdown("### 🛒 3. Panier")

    panier = st.session_state["panier_vente"]

    if not panier:

        st.info(
            "🛒 Le panier est vide. "
            "Ajoutez un ou plusieurs produits."
        )

    else:

        total_general = _total_panier()

        # ----------------------------------------------
        # AFFICHAGE DES ARTICLES
        # ----------------------------------------------

        for index, article in enumerate(panier):

            col_nom, col_qte, col_prix, col_total, col_suppr = (
                st.columns([3, 1, 1.5, 1.5, 0.7])
            )

            with col_nom:

                st.write(
                    f"**{article['nom']}**"
                )

            with col_qte:

                st.write(
                    f"{article['quantite']}"
                )

            with col_prix:

                st.write(
                    f"{article['prix_unitaire']:,.0f} KMF"
                )

            with col_total:

                montant = (
                    article["quantite"]
                    * article["prix_unitaire"]
                )

                st.write(
                    f"**{montant:,.0f} KMF**"
                )

            with col_suppr:

                if st.button(
                    "🗑️",
                    key=f"supprimer_article_{index}",
                ):

                    panier.pop(index)
                    st.rerun()

        st.divider()

        # ----------------------------------------------
        # TOTAL
        # ----------------------------------------------

        total_general = _total_panier()

        col_total1, col_total2 = st.columns([2, 1])

        with col_total2:

            st.markdown(
                f"""
                <div class="carte-total">
                    <div class="total-label">
                        TOTAL
                    </div>
                    <div class="total-value">
                        {total_general:,.0f} KMF
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # ====================================================
        # REMISE ET NOTE
        # ====================================================

        st.markdown("### 💳 4. Paiement")

        col_remise, col_note = st.columns(2)

        with col_remise:

            remise = st.number_input(
                "Remise (KMF)",
                min_value=0.0,
                max_value=float(total_general),
                value=0.0,
                step=500.0,
                key="remise_vente",
            )

        with col_note:

            note = st.text_input(
                "Note sur la facture",
                placeholder="Ex : Paiement comptant",
                key="note_vente",
            )

        total_final = max(
            0,
            total_general - remise,
        )

        st.markdown(
            f"### 💰 Total à payer : "
            f"**{total_final:,.0f} KMF**"
        )

        # ====================================================
        # ACTIONS
        # ====================================================

        col_annuler, col_valider = st.columns(2)

        with col_annuler:

            if st.button(
                "🗑️ Vider le panier",
                use_container_width=True,
            ):

                _vider_panier()

                st.session_state.pop(
                    "remise_vente",
                    None,
                )

                st.session_state.pop(
                    "note_vente",
                    None,
                )

                st.rerun()

        with col_valider:

            if st.button(
                "✅ Valider la vente et créer la facture",
                use_container_width=True,
                type="primary",
            ):

                # ------------------------------------------
                # Préparation des articles
                # ------------------------------------------

                articles = []

                for article in panier:

                    articles.append(
                        {
                            "produit_id": article[
                                "produit_id"
                            ],
                            "quantite": article[
                                "quantite"
                            ],
                            "prix_unitaire": article[
                                "prix_unitaire"
                            ],
                            "montant": (
                                article["quantite"]
                                * article["prix_unitaire"]
                            ),
                        }
                    )

                # ------------------------------------------
                # Création facture + vente + stock
                # ------------------------------------------

                succes, resultat, facture_id = creer_facture(
                    client_id=client_id,
                    articles=articles,
                    remise=float(remise),
                    note=note.strip() or None,
                    utilisateur_id=uid,
                )

                if succes:

                    st.session_state[
                        "derniere_facture_id"
                    ] = facture_id

                    st.session_state[
                        "derniere_facture_numero"
                    ] = resultat

                    _vider_panier()

                    st.session_state.pop(
                        "client_vente_selectionne",
                        None,
                    )

                    st.session_state.pop(
                        "remise_vente",
                        None,
                    )

                    st.session_state.pop(
                        "note_vente",
                        None,
                    )

                    st.rerun()

                else:

                    st.error(
                        f"❌ {resultat}"
                    )

    # ========================================================
    # HISTORIQUE DES FACTURES
    # ========================================================

    st.divider()

    st.markdown("### 🧾 Historique des factures")

    with closing(obtenir_connexion()) as connexion:

        factures = connexion.execute(
            """
            SELECT
                factures.id,
                factures.numero,
                factures.total_brut,
                factures.remise,
                factures.total_final,
                factures.date_creation,
                clients.nom AS client_nom
            FROM factures
            LEFT JOIN clients
                ON factures.client_id = clients.id
            WHERE factures.utilisateur_id = ?
            ORDER BY factures.id DESC
            LIMIT 20
            """,
            (uid,),
        ).fetchall()

    if not factures:

        st.info(
            "Aucune facture enregistrée pour le moment."
        )

    else:

        for facture in factures:

            client_nom = (
                facture["client_nom"]
                or "Client comptant"
            )

            with st.expander(
                f"🧾 {facture['numero']} — "
                f"{client_nom} — "
                f"{facture['total_final']:,.0f} KMF"
            ):

                col1, col2, col3 = st.columns(3)

                with col1:

                    st.write(
                        f"**Client :** {client_nom}"
                    )

                with col2:

                    st.write(
                        f"**Date :** "
                        f"{facture['date_creation']}"
                    )

                with col3:

                    st.write(
                        f"**Total :** "
                        f"{facture['total_final']:,.0f} KMF"
                    )

                pdf_historique = generer_pdf_facture(
                    facture["id"],
                    uid,
                )

                if pdf_historique:

                    col_pdf, col_apercu = st.columns(2)

                    with col_pdf:

                        st.download_button(
                            "📥 Télécharger PDF",
                            data=pdf_historique,
                            file_name=(
                                f"{facture['numero']}.pdf"
                            ),
                            mime="application/pdf",
                            key=(
                                f"download_facture_"
                                f"{facture['id']}"
                            ),
                            use_container_width=True,
                        )

                    with col_apercu:

                        if st.button(
                            "🖨️ Aperçu / Imprimer",
                            key=(
                                f"print_facture_"
                                f"{facture['id']}"
                            ),
                            use_container_width=True,
                        ):

                            st.session_state[
                                "facture_a_apercu"
                            ] = facture["id"]

                            st.rerun()

    # ========================================================
    # APERÇU D'UNE ANCIENNE FACTURE
    # ========================================================

    facture_a_apercu = st.session_state.get(
        "facture_a_apercu"
    )

    if facture_a_apercu:

        st.divider()

        st.markdown(
            "### 🖨️ Aperçu de la facture"
        )

        pdf_apercu = generer_pdf_facture(
            facture_a_apercu,
            uid,
        )

        if pdf_apercu:

            _apercu_pdf(
                pdf_apercu,
                f"historique_{facture_a_apercu}",
            )

            if st.button(
                "✖️ Fermer l'aperçu",
                use_container_width=True,
            ):

                st.session_state.pop(
                    "facture_a_apercu",
                    None,
                )

                st.rerun()




# import base64
# from contextlib import closing

# import streamlit as st
# from config.colors import (
#     BORDURE, FOND_CARTE, TEXTE_MUET, TEXTE_PRINCIPAL, TEXTE_SECONDAIRE, VERT,
# )
# from database.connexion import obtenir_connexion
# from fonctions.ventes import creer_vente, generer_pdf_recu


# def _apercu_imprimable(pdf_bytes, cle):
#     """PDF affiché dans la page, avec la barre d'outils du lecteur du
#     navigateur (zoom, impression) — pas besoin de télécharger d'abord."""
#     pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
#     st.markdown(
#         f'<iframe src="data:application/pdf;base64,{pdf_base64}" '
#         f'width="100%" height="500" '
#         f'style="border:1px solid {BORDURE};border-radius:10px;" '
#         f'title="apercu_recu_{cle}"></iframe>',
#         unsafe_allow_html=True
#     )


# def afficher_page_ventes():

#     st.markdown(
#         f"""
#         <style>
#         .ligne-item {{
#             display: flex;
#             justify-content: space-between;
#             align-items: center;
#             background: {FOND_CARTE};
#             border: 1px solid {BORDURE};
#             border-radius: 10px;
#             padding: 8px 12px;
#             margin-bottom: 6px;
#             font-size: 13px;
#         }}
#         .ligne-item .nom {{ font-weight: 600; color: {TEXTE_PRINCIPAL}; }}
#         .ligne-item .meta {{ color: {TEXTE_MUET}; font-size: 11px; }}
#         .ligne-item .montant {{ font-weight: 700; color: {VERT}; }}
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

#     st.markdown(
#         '<p style="font-size:20px;font-weight:700;margin-bottom:2px;">'
#         '💰 Ventes</p>'
#         f'<p style="font-size:13px;color:{TEXTE_SECONDAIRE};margin-bottom:10px;">'
#         'Enregistrez et consultez les ventes de votre entreprise.</p>',
#         unsafe_allow_html=True
#     )

#     uid = st.session_state.utilisateur_id

#     # ==========================================================
#     # REÇU DE LA DERNIÈRE VENTE (affiché tant qu'on n'a pas continué)
#     # ==========================================================

#     if "derniere_vente_ids" in st.session_state:

#         st.success("✅ Vente enregistrée avec succès !")

#         pdf_bytes = generer_pdf_recu(
#             st.session_state["derniere_vente_ids"], uid
#         )

#         if pdf_bytes:
#             col_telecharger, col_continuer = st.columns(2)
#             with col_telecharger:
#                 st.download_button(
#                     "📄 Télécharger le reçu",
#                     data=pdf_bytes,
#                     file_name=f"recu_{st.session_state['derniere_vente_ids'][0]}.pdf",
#                     mime="application/pdf",
#                     use_container_width=True,
#                     key="telecharger_recu"
#                 )
#             with col_continuer:
#                 if st.button(
#                     "➡️ Continuer vers Clients",
#                     use_container_width=True,
#                     type="primary",
#                     key="continuer_vers_clients"
#                 ):
#                     st.session_state.pop("derniere_vente_ids", None)
#                     st.session_state["page_demandee"] = "Clients"
#                     st.rerun()

#             if st.toggle("🖨️ Aperçu et impression", key="apercu_recu"):
#                 st.caption(
#                     "Utilisez l'icône imprimante de la barre d'outils "
#                     "ci-dessous (ou Ctrl+P) pour imprimer directement."
#                 )
#                 _apercu_imprimable(pdf_bytes, "derniere")
#         else:
#             if st.button("➡️ Continuer vers Clients", use_container_width=True):
#                 st.session_state.pop("derniere_vente_ids", None)
#                 st.session_state["page_demandee"] = "Clients"
#                 st.rerun()

#         st.divider()

#     # ==========================================================
#     # ENREGISTRER UNE VENTE (repliable)
#     # ==========================================================

#     with closing(obtenir_connexion()) as connexion:
#         produits = connexion.execute(
#             "SELECT id, nom, prix_vente, quantite FROM produits "
#             "WHERE utilisateur_id = ? ORDER BY nom ASC",
#             (uid,)
#         ).fetchall()

#     if not produits:
#         st.warning("⚠️ Aucun produit disponible.")
#         st.info("Ajoutez d'abord des produits dans la page 📦 Produits.")
#         return

#     with st.expander("🛒 Enregistrer une vente", expanded=True):

#         produits_disponibles = {
#             p["nom"]: p for p in produits if p["quantite"] > 0
#         }

#         if not produits_disponibles:
#             st.warning(
#                 "Tous les produits sont en rupture de stock. "
#                 "Réapprovisionnez avant d'enregistrer une nouvelle vente."
#             )
#         else:
#             produit_selectionne = st.selectbox(
#                 "Produit", list(produits_disponibles.keys())
#             )
#             produit = produits_disponibles[produit_selectionne]

#             st.caption(
#                 f"📦 Stock disponible : **{produit['quantite']} unités** "
#                 f"&nbsp;|&nbsp; 💰 Prix : **{produit['prix_vente']:,.0f} KMF**"
#             )

#             quantite = st.number_input(
#                 "Quantité vendue",
#                 min_value=1,
#                 max_value=produit["quantite"],
#                 value=1,
#                 step=1
#             )

#             montant_total = produit["prix_vente"] * quantite

#             st.markdown(
#                 f'<p style="font-size:15px;font-weight:600;margin:8px 0;">'
#                 f'💵 Total : <span style="color:{VERT};">'
#                 f'{montant_total:,.0f} KMF</span></p>',
#                 unsafe_allow_html=True
#             )

#             if st.button("💾 Enregistrer la vente", use_container_width=True):

#                 articles = [{
#                     "produit_id": produit["id"],
#                     "nom": produit["nom"],
#                     "quantite": quantite,
#                     "prix_unitaire": produit["prix_vente"],
#                     "montant": montant_total,
#                 }]

#                 succes, message, ids_ventes = creer_vente(articles, uid)

#                 if succes:
#                     st.session_state["derniere_vente_ids"] = ids_ventes
#                     st.rerun()
#                 else:
#                     st.error(f"❌ {message}")

#     # ==========================================================
#     # HISTORIQUE DES VENTES
#     # ==========================================================

#     with closing(obtenir_connexion()) as connexion:
#         ventes = connexion.execute(
#             """
#             SELECT
#                 ventes.id, produits.nom AS produit, ventes.quantite,
#                 ventes.prix_unitaire, ventes.montant_total, ventes.date_vente
#             FROM ventes
#             LEFT JOIN produits ON ventes.produit_id = produits.id
#             WHERE ventes.utilisateur_id = ?
#             ORDER BY ventes.date_vente DESC
#             """,
#             (uid,)
#         ).fetchall()

#     if not ventes:
#         st.info("Aucune vente enregistrée pour le moment.")
#         return

#     st.markdown(
#         f'<p style="font-size:14px;font-weight:600;margin:10px 0 6px;">'
#         f'📋 Historique des ventes ({len(ventes)})</p>',
#         unsafe_allow_html=True
#     )

#     for vente in ventes:
#         nom_produit = vente["produit"] or "Produit supprimé"
#         col_info, col_pdf = st.columns([5, 1])

#         with col_info:
#             st.markdown(
#                 f'<div class="ligne-item">'
#                 f'<div>'
#                 f'<div class="nom">🛒 {nom_produit}</div>'
#                 f'<div class="meta">'
#                 f'Vente #{vente["id"]} • {vente["quantite"]} unité(s) × '
#                 f'{vente["prix_unitaire"]:,.0f} KMF • {vente["date_vente"]}'
#                 f'</div>'
#                 f'</div>'
#                 f'<span class="montant">{vente["montant_total"]:,.0f} KMF</span>'
#                 f'</div>',
#                 unsafe_allow_html=True
#             )

#         with col_pdf:
#             recu = generer_pdf_recu([vente["id"]], uid)
#             if recu:
#                 st.download_button(
#                     "📄", data=recu, file_name=f"recu_{vente['id']}.pdf",
#                     mime="application/pdf", key=f"recu_{vente['id']}",
#                     help="Télécharger le reçu"
#                 )

