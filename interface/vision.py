import streamlit as st

from vision.analyse_documents import analyser_document


def afficher_page_vision():

    st.title("👁️ Analyse de documents")

    st.write(
        "Importez une facture ou un reçu. "
        "ComorIA Business analyse automatiquement le document."
    )

    fichier = st.file_uploader(
        "📷 Choisir une facture ou un reçu",
        type=["jpg", "jpeg", "png"]
    )

    if fichier is None:
        st.info(
            "Sélectionnez une image de facture ou de reçu "
            "pour commencer l'analyse."
        )
        return

    st.image(
        fichier,
        caption="Document sélectionné",
        use_container_width=True
    )

    if st.button(
        "🔍 Analyser le document",
        use_container_width=True
    ):

        with st.spinner("Analyse du document en cours..."):

            # Sauvegarde temporaire du fichier
            chemin_temporaire = "document_ocr_temp.png"

            with open(chemin_temporaire, "wb") as fichier_temp:
                fichier_temp.write(fichier.getbuffer())

            resultat = analyser_document(chemin_temporaire)

        if not resultat["succes"]:
            st.error(resultat["message"])
            return

        st.success("✅ Document analysé avec succès.")

        st.subheader("📋 Informations détectées")

        col1, col2 = st.columns(2)

        with col1:
            st.write("🏪 **Fournisseur**")
            st.write(resultat["fournisseur"] or "Non détecté")

            st.write("🧾 **Numéro**")
            st.write(resultat["numero"] or "Non détecté")

        with col2:
            st.write("📅 **Date**")
            st.write(resultat["date"] or "Non détectée")

            st.write("💰 **Montant**")

            if resultat["montant"] is not None:
                st.write(
                    f"{resultat['montant']:,.0f} KMF"
                )
            else:
                st.write("Non détecté")

        st.divider()

        st.subheader("📝 Texte détecté")

        st.text_area(
            "Résultat OCR",
            resultat["texte_brut"],
            height=300
        )



