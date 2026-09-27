from contextlib import closing

import streamlit as st
from database.connexion import obtenir_connexion


def afficher_page_assistant_ia():

    st.markdown(
        """
        <style>
        .assistant-header {
            background: linear-gradient(135deg, #00843D, #006B32);
            color: white;
            padding: 14px 18px;
            border-radius: 14px;
            margin-bottom: 14px;
        }
        .assistant-header h2 {
            margin: 0;
            font-size: 19px;
        }
        .assistant-header p {
            margin: 4px 0 0 0;
            font-size: 12px;
            opacity: 0.9;
        }
        .assistant-section {
            font-size: 14px;
            font-weight: 600;
            margin: 12px 0 8px 0;
        }
        .question-box {
            background: #F5F7F7;
            border-radius: 12px;
            padding: 12px 14px;
            margin-bottom: 8px;
            font-size: 13px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="assistant-header">
            <h2>🤖 Assistant IA</h2>
            <p>
                Posez une question sur votre activité et ComorIA Business
                analysera vos données.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "💡 Cette première version fonctionne sans API. "
        "Elle analyse directement les données de votre entreprise."
    )

    # ==========================================
    # QUESTIONS RAPIDES
    # ==========================================

    st.markdown(
        '<p class="assistant-section">💬 Questions rapides</p>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💰 Quel est mon chiffre d'affaires ?", use_container_width=True):
            st.session_state["question_assistant"] = "Quel est mon chiffre d'affaires ?"
        if st.button("📦 Quels produits sont en rupture ?", use_container_width=True):
            st.session_state["question_assistant"] = "Quels produits sont en rupture ?"
        if st.button("👥 Combien ai-je de clients ?", use_container_width=True):
            st.session_state["question_assistant"] = "Combien ai-je de clients ?"
    with col2:
        if st.button("💳 Combien ai-je dépensé ?", use_container_width=True):
            st.session_state["question_assistant"] = "Combien ai-je dépensé ?"
        if st.button("📈 Quel est mon bénéfice ?", use_container_width=True):
            st.session_state["question_assistant"] = "Quel est mon bénéfice ?"
        if st.button("🛒 Quel produit se vend le mieux ?", use_container_width=True):
            st.session_state["question_assistant"] = "Quel produit se vend le mieux ?"

    # ==========================================
    # CHAMP DE QUESTION
    # ==========================================

    question = st.text_input(
        "Votre question",
        value=st.session_state.get("question_assistant", ""),
        placeholder="Exemple : Quels sont mes produits les plus vendus ?"
    )

    if st.button("🤖 Analyser", use_container_width=True, type="primary"):
        if not question.strip():
            st.warning("⚠️ Écrivez d'abord une question.")
        else:
            reponse = analyser_question(question, st.session_state.utilisateur_id)
            st.markdown(
                '<p class="assistant-section">💡 Réponse</p>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="question-box">{reponse}</div>',
                unsafe_allow_html=True
            )
            st.session_state["question_assistant"] = ""


# ============================================================
# MOTEUR D'ANALYSE
# ============================================================

def analyser_question(question, utilisateur_id):
    question = question.lower().strip()

    with closing(obtenir_connexion()) as connexion:

        # ==========================================
        # DÉTECTION DE LA PÉRIODE
        # ==========================================
        periode = None
        if "aujourd'hui" in question or "aujourd hui" in question or "aujourd" in question:
            periode = "aujourd'hui"
        elif "cette semaine" in question:
            periode = "semaine"
        elif (
            "ce mois" in question or "ce mois-ci" in question
            or "ce mois ci" in question or "mensuel" in question
        ):
            periode = "mois"

        condition_ventes = "WHERE utilisateur_id = ?"
        condition_depenses = "WHERE utilisateur_id = ?"
        if periode == "aujourd'hui":
            condition_ventes += " AND date(date_vente) = date('now', 'localtime')"
            condition_depenses += " AND date(date_depense) = date('now', 'localtime')"
        elif periode == "semaine":
            condition_ventes += (
                " AND date(date_vente) >= date('now', 'localtime', '-6 days')"
            )
            condition_depenses += (
                " AND date(date_depense) >= date('now', 'localtime', '-6 days')"
            )
        elif periode == "mois":
            condition_ventes += (
                " AND date(date_vente) >= date('now', 'localtime', 'start of month')"
            )
            condition_depenses += (
                " AND date(date_depense) >= "
                "date('now', 'localtime', 'start of month')"
            )

        def texte_periode():
            return {
                "aujourd'hui": "aujourd'hui",
                "semaine": "cette semaine",
                "mois": "ce mois-ci",
            }.get(periode, "au total")

        try:
            # ==========================================
            # CHIFFRE D'AFFAIRES
            # ==========================================
            if (
                "chiffre d'affaires" in question or "chiffre affaire" in question
                or "chiffre d affaire" in question or question == "ca"
                or "combien j'ai fait" in question or "combien ai-je fait" in question
            ):
                resultat = connexion.execute(
                    f"SELECT COALESCE(SUM(montant_total), 0) FROM ventes "
                    f"{condition_ventes}",
                    (utilisateur_id,)
                ).fetchone()[0]
                return (
                    f"💰 Votre chiffre d'affaires {texte_periode()} "
                    f"est de **{resultat:,.0f} KMF**."
                )

            # ==========================================
            # PRODUITS LES PLUS VENDUS
            # (vérifié AVANT le bloc générique "ventes" ci-dessous, car
            # "vendus"/"vendu" y matcherait sinon en premier et court-
            # circuiterait cette réponse plus précise)
            # ==========================================
            if (
                "plus vendu" in question or "plus vendus" in question
                or "meilleur produit" in question or "meilleurs produits" in question
                or "se vend le mieux" in question or "se vendent le mieux" in question
            ):
                produits = connexion.execute(
                    f"""
                    SELECT produits.nom, SUM(ventes.quantite) AS quantite
                    FROM ventes
                    LEFT JOIN produits ON ventes.produit_id = produits.id
                    {condition_ventes}
                    GROUP BY produits.id, produits.nom
                    ORDER BY quantite DESC
                    LIMIT 5
                    """,
                    (utilisateur_id,)
                ).fetchall()
                if not produits:
                    return "ℹ️ Aucune vente enregistrée pour cette période."
                liste = "\n".join(
                    f"- 🛒 {p['nom']} : **{p['quantite']} unité(s)** vendue(s)"
                    for p in produits
                )
                suffixe = f" {texte_periode()}" if periode else ""
                return f"📈 Voici les produits les plus vendus{suffixe} :\n\n{liste}"

            # ==========================================
            # VENTES (comptage global)
            # ==========================================
            if (
                "vente" in question or "ventes" in question
                or "vendu" in question or "vendues" in question
            ):
                nombre = connexion.execute(
                    f"SELECT COUNT(*) FROM ventes {condition_ventes}",
                    (utilisateur_id,)
                ).fetchone()[0]
                quantite = connexion.execute(
                    f"SELECT COALESCE(SUM(quantite), 0) FROM ventes "
                    f"{condition_ventes}",
                    (utilisateur_id,)
                ).fetchone()[0]
                return (
                    f"🛒 {texte_periode().capitalize()}, vous avez enregistré "
                    f"**{nombre} vente(s)** représentant "
                    f"**{quantite} unité(s)** vendue(s)."
                )

            # ==========================================
            # DÉPENSES
            # ==========================================
            if (
                "dépense" in question or "dépenses" in question
                or "depense" in question or "depenses" in question
                or "dépensé" in question
            ):
                resultat = connexion.execute(
                    f"SELECT COALESCE(SUM(montant), 0) FROM depenses "
                    f"{condition_depenses}",
                    (utilisateur_id,)
                ).fetchone()[0]
                return (
                    f"💳 Vos dépenses {texte_periode()} sont de "
                    f"**{resultat:,.0f} KMF**."
                )

            # ==========================================
            # BÉNÉFICE / RÉSULTAT
            # ==========================================
            if (
                "bénéfice" in question or "benefice" in question
                or "profit" in question or "résultat" in question
                or "resultat" in question
            ):
                ca = connexion.execute(
                    f"SELECT COALESCE(SUM(montant_total), 0) FROM ventes "
                    f"{condition_ventes}",
                    (utilisateur_id,)
                ).fetchone()[0]
                depenses = connexion.execute(
                    f"SELECT COALESCE(SUM(montant), 0) FROM depenses "
                    f"{condition_depenses}",
                    (utilisateur_id,)
                ).fetchone()[0]
                resultat = ca - depenses
                return (
                    f"📈 Votre résultat {texte_periode()} est de "
                    f"**{resultat:,.0f} KMF** (ventes moins dépenses enregistrées)."
                )

            # ==========================================
            # CLIENTS
            # ==========================================
            if "client" in question:
                nombre = connexion.execute(
                    "SELECT COUNT(*) FROM clients WHERE utilisateur_id = ?",
                    (utilisateur_id,)
                ).fetchone()[0]
                return f"👥 Vous avez actuellement **{nombre} client(s)** enregistré(s)."

            # ==========================================
            # PRODUITS EN RUPTURE
            # ==========================================
            if "rupture" in question:
                produits = connexion.execute(
                    "SELECT nom, quantite FROM produits "
                    "WHERE quantite <= 0 AND utilisateur_id = ? "
                    "ORDER BY nom",
                    (utilisateur_id,)
                ).fetchall()
                if not produits:
                    return "✅ Aucun produit n'est actuellement en rupture de stock."
                liste = "\n".join(
                    f"- 📦 {p['nom']} : {p['quantite']} unité(s)" for p in produits
                )
                return f"⚠️ Produits actuellement en rupture :\n\n{liste}"

            # ==========================================
            # STOCK FAIBLE
            # ==========================================
            if (
                "stock faible" in question or "stocks faibles" in question
                or "presque en rupture" in question
                or "bientôt en rupture" in question or "bientot en rupture" in question
            ):
                produits = connexion.execute(
                    "SELECT nom, quantite, seuil_alerte FROM produits "
                    "WHERE quantite <= seuil_alerte AND utilisateur_id = ? "
                    "ORDER BY quantite ASC",
                    (utilisateur_id,)
                ).fetchall()
                if not produits:
                    return "✅ Aucun produit n'est actuellement sous son seuil d'alerte."
                liste = "\n".join(
                    f"- 📦 {p['nom']} : {p['quantite']} unité(s) "
                    f"(seuil : {p['seuil_alerte']})"
                    for p in produits
                )
                return f"⚠️ Produits nécessitant une attention :\n\n{liste}"

            # ==========================================
            # NOMBRE DE PRODUITS
            # ==========================================
            if "produit" in question:
                nombre = connexion.execute(
                    "SELECT COUNT(*) FROM produits WHERE utilisateur_id = ?",
                    (utilisateur_id,)
                ).fetchone()[0]
                return f"📦 Votre entreprise possède **{nombre} produit(s)** enregistré(s)."

            # ==========================================
            # QUESTION NON COMPRISE
            # ==========================================
            return (
                "🤔 Je n'ai pas encore compris cette question.\n\n"
                "Vous pouvez essayer par exemple :\n"
                "- 💰 Quel est mon chiffre d'affaires aujourd'hui ?\n"
                "- 📊 Combien ai-je vendu ce mois-ci ?\n"
                "- 💳 Combien ai-je dépensé cette semaine ?\n"
                "- 📈 Quel est mon bénéfice ce mois-ci ?\n"
                "- 🛒 Quel produit se vend le mieux ?\n"
                "- 📦 Quels produits sont presque en rupture ?\n"
                "- 👥 Combien ai-je de clients ?"
            )

        except Exception as erreur:
            return f"❌ Une erreur est survenue lors de l'analyse : {erreur}"
