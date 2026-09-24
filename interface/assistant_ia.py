
import streamlit as st
from database.connexion import obtenir_connexion


def afficher_page_assistant_ia():

    st.markdown(
        """
        <style>
        .assistant-header {
            background: linear-gradient(135deg, #00843D, #006B32);
            color: white;
            padding: 20px;
            border-radius: 16px;
            margin-bottom: 20px;
        }

        .assistant-header h2 {
            margin: 0;
            font-size: 24px;
        }

        .assistant-header p {
            margin: 6px 0 0 0;
            font-size: 13px;
            opacity: 0.9;
        }

        .question-box {
            background: #F5F7F7;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 8px;
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
                Posez une question sur votre activité et Comoria Business
                analysera vos données.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "💡 pas besoin de reflechir dit seulement ce que tu veux et je te donne les reponse  "
    )

    # ==========================================
    # QUESTIONS RAPIDES
    # ==========================================

    st.markdown("### 💬 Questions rapides")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "💰 Quel est mon chiffre d'affaires ?",
            use_container_width=True
        ):
            st.session_state["question_assistant"] = (
                "Quel est mon chiffre d'affaires ?"
            )

        if st.button(
            "📦 Quels produits sont en rupture ?",
            use_container_width=True
        ):
            st.session_state["question_assistant"] = (
                "Quels produits sont en rupture ?"
            )

        if st.button(
            "👥 Combien ai-je de clients ?",
            use_container_width=True
        ):
            st.session_state["question_assistant"] = (
                "Combien ai-je de clients ?"
            )

    with col2:
        if st.button(
            "💳 Combien ai-je dépensé ?",
            use_container_width=True
        ):
            st.session_state["question_assistant"] = (
                "Combien ai-je dépensé ?"
            )

        if st.button(
            "📈 Quel est mon bénéfice ?",
            use_container_width=True
        ):
            st.session_state["question_assistant"] = (
                "Quel est mon bénéfice ?"
            )

        if st.button(
            "🛒 Combien de ventes ai-je réalisées ?",
            use_container_width=True
        ):
            st.session_state["question_assistant"] = (
                "Combien de ventes ai-je réalisées ?"
            )

    # ==========================================
    # CHAMP DE QUESTION
    # ==========================================

    question = st.text_input(
        "Votre question",
        value=st.session_state.get("question_assistant", ""),
        placeholder="Exemple : Quels sont mes produits les plus vendus ?"
    )

    if st.button("🤖 Analyser", use_container_width=True):

        if not question.strip():
            st.warning("⚠️ Écrivez d'abord une question.")
            return

        reponse = analyser_question(question)

        st.markdown("### 💡 Réponse")

        st.success(reponse)

        st.session_state["question_assistant"] = ""


# ============================================================
# MOTEUR D'ANALYSE
# ============================================================
def analyser_question(question):

    question = question.lower().strip()

    connexion = obtenir_connexion()

    try:

        # ==========================================
        # DÉTECTION DE LA PÉRIODE
        # ==========================================

        periode = None

        if (
            "aujourd'hui" in question
            or "aujourd hui" in question
            or "aujourd" in question
        ):
            periode = "aujourd'hui"

        elif (
            "cette semaine" in question
            or "cette semaine-ci" in question
        ):
            periode = "semaine"

        elif (
            "ce mois" in question
            or "ce mois-ci" in question
            or "ce mois ci" in question
            or "mensuel" in question
        ):
            periode = "mois"

        # ==========================================
        # CONDITIONS SQL DE PÉRIODE
        # ==========================================

        condition_ventes = ""
        condition_depenses = ""

        if periode == "aujourd'hui":

            condition_ventes = (
                "WHERE date(date_vente) = date('now', 'localtime')"
            )

            condition_depenses = (
                "WHERE date(date_depense) = date('now', 'localtime')"
            )

        elif periode == "semaine":

            condition_ventes = (
                "WHERE date(date_vente) >= "
                "date('now', 'localtime', '-6 days')"
            )

            condition_depenses = (
                "WHERE date(date_depense) >= "
                "date('now', 'localtime', '-6 days')"
            )

        elif periode == "mois":

            condition_ventes = (
                "WHERE date(date_vente) >= "
                "date('now', 'localtime', 'start of month')"
            )

            condition_depenses = (
                "WHERE date(date_depense) >= "
                "date('now', 'localtime', 'start of month')"
            )

        # ==========================================
        # CHIFFRE D'AFFAIRES
        # ==========================================

        if (
            "chiffre d'affaires" in question
            or "chiffre affaire" in question
            or "chiffre d affaire" in question
            or question == "ca"
            or "combien j'ai fait" in question
            or "combien ai-je fait" in question
        ):

            resultat = connexion.execute(
                f"""
                SELECT COALESCE(SUM(montant_total), 0)
                FROM ventes
                {condition_ventes}
                """
            ).fetchone()[0]

            if periode == "aujourd'hui":
                texte_periode = "aujourd'hui"

            elif periode == "semaine":
                texte_periode = "cette semaine"

            elif periode == "mois":
                texte_periode = "ce mois-ci"

            else:
                texte_periode = "au total"

            return (
                f"💰 Votre chiffre d'affaires {texte_periode} "
                f"est de **{resultat:,.0f} KMF**."
            )

        # ==========================================
        # VENTES
        # ==========================================

        if (
            "vente" in question
            or "ventes" in question
            or "vendu" in question
            or "vendues" in question
        ):

            nombre = connexion.execute(
                f"""
                SELECT COUNT(*)
                FROM ventes
                {condition_ventes}
                """
            ).fetchone()[0]

            quantite = connexion.execute(
                f"""
                SELECT COALESCE(SUM(quantite), 0)
                FROM ventes
                {condition_ventes}
                """
            ).fetchone()[0]

            if periode == "aujourd'hui":
                texte_periode = "aujourd'hui"

            elif periode == "semaine":
                texte_periode = "cette semaine"

            elif periode == "mois":
                texte_periode = "ce mois-ci"

            else:
                texte_periode = "au total"

            return (
                f"🛒 {texte_periode.capitalize()}, vous avez enregistré "
                f"**{nombre} vente(s)** représentant "
                f"**{quantite} unité(s)** vendue(s)."
            )

        # ==========================================
        # DÉPENSES
        # ==========================================

        if (
            "dépense" in question
            or "dépenses" in question
            or "depense" in question
            or "depenses" in question
            or "dépensé" in question
            or "depense" in question
        ):

            resultat = connexion.execute(
                f"""
                SELECT COALESCE(SUM(montant), 0)
                FROM depenses
                {condition_depenses}
                """
            ).fetchone()[0]

            if periode == "aujourd'hui":
                texte_periode = "aujourd'hui"

            elif periode == "semaine":
                texte_periode = "cette semaine"

            elif periode == "mois":
                texte_periode = "ce mois-ci"

            else:
                texte_periode = "au total"

            return (
                f"💳 Vos dépenses {texte_periode} sont de "
                f"**{resultat:,.0f} KMF**."
            )

        # ==========================================
        # BÉNÉFICE / RÉSULTAT
        # ==========================================

        if (
            "bénéfice" in question
            or "benefice" in question
            or "profit" in question
            or "résultat" in question
            or "resultat" in question
        ):

            ca = connexion.execute(
                f"""
                SELECT COALESCE(SUM(montant_total), 0)
                FROM ventes
                {condition_ventes}
                """
            ).fetchone()[0]

            depenses = connexion.execute(
                f"""
                SELECT COALESCE(SUM(montant), 0)
                FROM depenses
                {condition_depenses}
                """
            ).fetchone()[0]

            resultat = ca - depenses

            if periode == "aujourd'hui":
                texte_periode = "aujourd'hui"

            elif periode == "semaine":
                texte_periode = "cette semaine"

            elif periode == "mois":
                texte_periode = "ce mois-ci"

            else:
                texte_periode = "au total"

            return (
                f"📈 Votre résultat {texte_periode} est de "
                f"**{resultat:,.0f} KMF** "
                f"(ventes moins dépenses enregistrées)."
            )

        # ==========================================
        # CLIENTS
        # ==========================================

        if "client" in question:

            nombre = connexion.execute(
                """
                SELECT COUNT(*)
                FROM clients
                """
            ).fetchone()[0]

            return (
                f"👥 Vous avez actuellement "
                f"**{nombre} client(s)** enregistré(s)."
            )

        # ==========================================
        # PRODUITS EN RUPTURE
        # ==========================================

        if (
            "rupture" in question
            or "en rupture" in question
        ):

            produits = connexion.execute(
                """
                SELECT nom, quantite
                FROM produits
                WHERE quantite <= 0
                ORDER BY nom
                """
            ).fetchall()

            if not produits:
                return (
                    "✅ Aucun produit n'est actuellement "
                    "en rupture de stock."
                )

            liste = "\n".join(
                [
                    f"- 📦 {produit['nom']} : "
                    f"{produit['quantite']} unité(s)"
                    for produit in produits
                ]
            )

            return (
                "⚠️ Produits actuellement en rupture :\n\n"
                + liste
            )

        # ==========================================
        # STOCK FAIBLE
        # ==========================================

        if (
            "stock faible" in question
            or "stocks faibles" in question
            or "presque en rupture" in question
            or "bientôt en rupture" in question
            or "bientot en rupture" in question
        ):

            produits = connexion.execute(
                """
                SELECT nom, quantite, seuil_alerte
                FROM produits
                WHERE quantite <= seuil_alerte
                ORDER BY quantite ASC
                """
            ).fetchall()

            if not produits:
                return (
                    "✅ Aucun produit n'est actuellement "
                    "sous son seuil d'alerte."
                )

            liste = "\n".join(
                [
                    f"- 📦 {p['nom']} : {p['quantite']} unité(s) "
                    f"(seuil : {p['seuil_alerte']})"
                    for p in produits
                ]
            )

            return (
                "⚠️ Produits nécessitant une attention :\n\n"
                + liste
            )

        # ==========================================
        # PRODUITS LES PLUS VENDUS
        # ==========================================

        if (
            "plus vendu" in question
            or "plus vendus" in question
            or "meilleur produit" in question
            or "meilleurs produits" in question
            or "se vend le mieux" in question
            or "se vendent le mieux" in question
        ):

            produits = connexion.execute(
                f"""
                SELECT
                    produits.nom,
                    SUM(ventes.quantite) AS quantite
                FROM ventes
                LEFT JOIN produits
                    ON ventes.produit_id = produits.id
                {condition_ventes}
                GROUP BY produits.id, produits.nom
                ORDER BY quantite DESC
                LIMIT 5
                """
            ).fetchall()

            if not produits:
                return (
                    "ℹ️ Aucune vente enregistrée "
                    "pour cette période."
                )

            liste = "\n".join(
                [
                    f"- 🛒 {p['nom']} : "
                    f"**{p['quantite']} unité(s)** vendue(s)"
                    for p in produits
                ]
            )

            return (
                "📈 Voici les produits les plus vendus "
                f"{'pour ' + periode if periode else ''} :\n\n"
                + liste
            )

        # ==========================================
        # NOMBRE DE PRODUITS
        # ==========================================

        if "produit" in question:

            nombre = connexion.execute(
                """
                SELECT COUNT(*)
                FROM produits
                """
            ).fetchone()[0]

            return (
                f"📦 Votre entreprise possède "
                f"**{nombre} produit(s)** enregistré(s)."
            )

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

        return (
            f"❌ Une erreur est survenue lors de l'analyse : "
            f"{erreur}"
        )

    finally:
        connexion.close()
