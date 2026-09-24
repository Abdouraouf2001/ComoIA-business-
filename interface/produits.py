import io
import sqlite3
from contextlib import closing

import pandas as pd
import streamlit as st
from fpdf import FPDF

from database.connexion import obtenir_connexion

VERT = "#00843D"
ROUGE = "#D64545"


def generer_excel(produits):
    """Construit un fichier Excel (bytes) à partir de la liste des produits."""
    donnees = [
        {
            "Nom": p["nom"],
            "Catégorie": p["categorie"] or "",
            "Prix d'achat (KMF)": p["prix_achat"],
            "Prix de vente (KMF)": p["prix_vente"],
            "Quantité": p["quantite"],
            "Seuil d'alerte": p["seuil_alerte"],
        }
        for p in produits
    ]
    tampon = io.BytesIO()
    with pd.ExcelWriter(tampon, engine="openpyxl") as ecrivain:
        pd.DataFrame(donnees).to_excel(ecrivain, index=False, sheet_name="Produits")
    return tampon.getvalue()


def generer_pdf(produits):
    """Construit un fichier PDF (bytes) à partir de la liste des produits."""
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(0, 132, 61)
    pdf.cell(0, 10, "ComorIA Business - Liste des produits", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, f"{len(produits)} produit(s) au total", ln=True)
    pdf.ln(4)

    colonnes = ["Nom", "Catégorie", "Prix d'achat", "Prix de vente", "Quantité", "Seuil"]
    largeurs = [70, 55, 40, 40, 30, 30]

    pdf.set_font("Helvetica", "B", 10)
    pdf.set_fill_color(230, 244, 234)
    for titre, largeur in zip(colonnes, largeurs):
        pdf.cell(largeur, 8, titre, border=1, fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    for p in produits:
        pdf.cell(largeurs[0], 8, str(p["nom"])[:40], border=1)
        pdf.cell(largeurs[1], 8, str(p["categorie"] or "-")[:30], border=1)
        pdf.cell(largeurs[2], 8, f"{p['prix_achat']:,.0f} KMF", border=1)
        pdf.cell(largeurs[3], 8, f"{p['prix_vente']:,.0f} KMF", border=1)
        pdf.cell(largeurs[4], 8, str(p["quantite"]), border=1)
        pdf.cell(largeurs[5], 8, str(p["seuil_alerte"]), border=1)
        pdf.ln()

    return bytes(pdf.output())


def afficher_page_produits():

    st.markdown(
        """
        <style>
        .ligne-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: white;
            border: 1px solid #EAECEF;
            border-radius: 10px;
            padding: 8px 12px;
            margin-bottom: 6px;
            font-size: 13px;
        }
        .ligne-item .nom { font-weight: 600; color: #111827; }
        .ligne-item .meta { color: #9CA3AF; font-size: 11px; }
        .badge-stock {
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 999px;
            white-space: nowrap;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        '<p style="font-size:20px;font-weight:700;margin-bottom:2px;">'
        '📦 Produits</p>'
        '<p style="font-size:13px;color:#6B7280;margin-bottom:10px;">'
        'Gérez vos produits, leurs prix et leurs quantités en stock.</p>',
        unsafe_allow_html=True
    )

    # Message affiché après un st.rerun() (sinon il serait effacé aussitôt)
    if "message_produit" in st.session_state:
        st.success(st.session_state.pop("message_produit"))
    if "erreur_produit" in st.session_state:
        st.error(st.session_state.pop("erreur_produit"))

    # ==========================================================
    # AJOUTER UN PRODUIT (repliable, pour ne pas prendre de place
    # une fois que la liste est bien remplie)
    # ==========================================================

    with st.expander("➕ Ajouter un produit"):

        # clear_on_submit=True : le formulaire se vide après l'enregistrement
        with st.form("formulaire_produit", clear_on_submit=True):

            col1, col2 = st.columns(2)

            with col1:
                nom = st.text_input(
                    "Nom du produit",
                    placeholder="Exemple : Riz 25 kg"
                )
                categorie = st.text_input(
                    "Catégorie",
                    placeholder="Exemple : Alimentation"
                )
                prix_achat = st.number_input(
                    "Prix d'achat (KMF)",
                    min_value=0.0,
                    step=100.0
                )

            with col2:
                prix_vente = st.number_input(
                    "Prix de vente (KMF)",
                    min_value=0.0,
                    step=100.0
                )
                quantite = st.number_input(
                    "Quantité initiale",
                    min_value=0,
                    step=1
                )
                seuil_alerte = st.number_input(
                    "Seuil d'alerte",
                    min_value=0,
                    value=5,
                    step=1
                )

            bouton = st.form_submit_button(
                "💾 Enregistrer le produit",
                use_container_width=True
            )

        if bouton:

            if not nom.strip():
                st.error("Veuillez saisir le nom du produit.")

            elif prix_vente <= 0:
                st.error("Le prix de vente doit être supérieur à 0.")

            else:
                # closing() ferme la connexion même en cas d'erreur
                with closing(obtenir_connexion()) as connexion:
                    connexion.execute(
                        """
                        INSERT INTO produits
                        (nom, categorie, prix_achat, prix_vente,
                         quantite, seuil_alerte)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            nom.strip(),
                            categorie.strip(),
                            prix_achat,
                            prix_vente,
                            quantite,
                            seuil_alerte
                        )
                    )
                    connexion.commit()

                st.session_state["message_produit"] = (
                    "✅ Produit ajouté avec succès !"
                )
                st.rerun()

    # ==========================================================
    # LISTE DES PRODUITS
    # ==========================================================

    with closing(obtenir_connexion()) as connexion:
        produits = connexion.execute(
            """
            SELECT
                id,
                nom,
                categorie,
                prix_achat,
                prix_vente,
                quantite,
                seuil_alerte
            FROM produits
            ORDER BY id DESC
            """
        ).fetchall()

    if not produits:
        st.info("Aucun produit enregistré pour le moment.")
        return

    st.markdown(
        f'<p style="font-size:14px;font-weight:600;margin:10px 0 6px;">'
        f'📋 Mes produits ({len(produits)})</p>',
        unsafe_allow_html=True
    )

    # ==========================================================
    # EXPORT
    # ==========================================================

    col_excel, col_pdf = st.columns(2)
    with col_excel:
        st.download_button(
            "📊 Excel",
            data=generer_excel(produits),
            file_name="produits_comoria.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument"
                ".spreadsheetml.sheet"
            ),
            use_container_width=True
        )
    with col_pdf:
        st.download_button(
            "📄 PDF",
            data=generer_pdf(produits),
            file_name="produits_comoria.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ==========================================================
    # AFFICHAGE COMPACT (une ligne par produit)
    # ==========================================================

    for produit in produits:

        col_info, col_action = st.columns([6, 1])

        with col_info:
            faible = produit["quantite"] <= produit["seuil_alerte"]
            couleur_badge = ROUGE if faible else VERT
            fond_badge = "#FDECEC" if faible else "#E6F4EA"
            categorie_txt = f' • {produit["categorie"]}' if produit["categorie"] else ""

            st.markdown(
                f'<div class="ligne-item">'
                f'<div>'
                f'<div class="nom">📦 {produit["nom"]}{categorie_txt}</div>'
                f'<div class="meta">'
                f'Achat {produit["prix_achat"]:,.0f} KMF • '
                f'Vente {produit["prix_vente"]:,.0f} KMF'
                f'</div>'
                f'</div>'
                f'<span class="badge-stock" '
                f'style="color:{couleur_badge};background:{fond_badge};">'
                f'{produit["quantite"]} en stock</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        with col_action:
            if st.button(
                "🗑️",
                key=f"supprimer_{produit['id']}",
                help="Supprimer le produit"
            ):
                try:
                    with closing(obtenir_connexion()) as connexion:
                        connexion.execute(
                            "DELETE FROM produits WHERE id = ?",
                            (produit["id"],)
                        )
                        connexion.commit()

                    st.session_state["message_produit"] = "Produit supprimé."

                except sqlite3.IntegrityError:
                    # Le produit est utilisé par des ventes
                    st.session_state["erreur_produit"] = (
                        f"« {produit['nom']} » a déjà des ventes "
                        "enregistrées : impossible de le supprimer."
                    )

                st.rerun()
