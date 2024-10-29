import json
from spyne import Application, rpc, ServiceBase, Unicode, Float
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication


class CreditPolicies:
    """Définit les politiques de crédit pour les critères de base."""
    MIN_CREDIT_SCORE = 650
    MAX_DEBT_TO_INCOME_RATIO = 0.43
    MIN_PROPERTY_VALUE_TO_LOAN_RATIO = 1.2

    @classmethod
    def meets_basic_requirements(cls, credit_score, debt_to_income_ratio, property_value, loan_amount):
        """Vérifie si les critères de base sont respectés."""
        return (
            credit_score >= cls.MIN_CREDIT_SCORE and
            debt_to_income_ratio <= cls.MAX_DEBT_TO_INCOME_RATIO and
            property_value >= loan_amount * cls.MIN_PROPERTY_VALUE_TO_LOAN_RATIO
        )


class RiskAnalyzer:
    """Classe pour analyser les risques de crédit."""

    @staticmethod
    def calculate_risk_score(credit_score, debt_to_income_ratio, property_value, loan_amount):
        """Calcule le score de risque en fonction des facteurs donnés."""
        risk_score = 100 - (credit_score / 8.5)
        risk_score += debt_to_income_ratio * 100
        loan_to_value_ratio = loan_amount / property_value
        risk_score += loan_to_value_ratio * 60
        return min(max(risk_score, 0), 100)

    @staticmethod
    def predict_default_probability(credit_score, debt_to_income_ratio):
        """Prédit la probabilité de défaut basée sur le score de crédit et le ratio dette/revenu."""
        return max(0, min(1, ((850 - credit_score) / 850 + debt_to_income_ratio) / 2))


class LoanDecisionMaker:
    """Classe pour prendre une décision d'approbation basée sur le risque et les politiques."""

    @staticmethod
    def decide_approval(risk_score, meets_policies, default_probability):
        """Prend une décision d'approbation en fonction du score de risque et de la probabilité de défaut."""
        if not meets_policies:
            return False, "Les critères de base ne sont pas respectés"
        if risk_score > 75:
            return False, "Niveau de risque évalué trop élevé"
        if default_probability > 0.35:
            return False, "Probabilité de défaut élevée"
        return True, "Demande approuvée"

    @staticmethod
    def determine_loan_terms(approved, loan_amount, credit_score):
        """Définit les termes de prêt si la demande est approuvée."""
        if not approved:
            return None
        base_rate = 0.03
        adjustment_factor = (750 - credit_score) / 1100
        interest_rate = base_rate + adjustment_factor
        return {
            "loan_amount": loan_amount,
            "interest_rate": round(interest_rate, 4),
            "term_years": 30
        }


class ApprovalDecisionService(ServiceBase):
    """Service SOAP pour l'évaluation de la demande de crédit."""

    @rpc(Unicode, Float, Float, Float, Float, _returns=Unicode)
    def make_decision(ctx, client_name, credit_score, debt_to_income_ratio, property_value, loan_amount):
        # Vérification des critères de base
        meets_policies = CreditPolicies.meets_basic_requirements(
            credit_score, debt_to_income_ratio, property_value, loan_amount
        )

        # Analyse des risques et probabilité de défaut
        risk_score = RiskAnalyzer.calculate_risk_score(credit_score, debt_to_income_ratio, property_value, loan_amount)
        default_probability = RiskAnalyzer.predict_default_probability(credit_score, debt_to_income_ratio)

        # Décision d'approbation
        approved, reason = LoanDecisionMaker.decide_approval(risk_score, meets_policies, default_probability)

        # Termes du prêt si approuvé
        terms = LoanDecisionMaker.determine_loan_terms(approved, loan_amount, credit_score) if approved else None

        # Compilation des résultats dans un dictionnaire JSON
        result = {
            "client_name": client_name,
            "approved": approved,
            "reason": reason,
            "risk_score": risk_score,
            "default_probability": default_probability,
            "loan_terms": terms
        }

        return json.dumps(result)


# Configuration de l'application Spyne
application = Application(
    [ApprovalDecisionService],
    tns='approval_decision',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)


# Fonction de test pour vérifier le fonctionnement du service
def test_service():
    service = ApprovalDecisionService()
    result = service.make_decision(
        None,  # ctx
        "John Doe",  # client_name
        720,  # credit score
        0.35,  # debt to income ratio
        300000,  # property value
        250000  # loan amount
    )
    print("Résultat de la décision d'approbation :")
    print(result)


if __name__ == '__main__':
    # Exécuter le test
    test_service()

    # Démarrer le serveur SOAP
    wsgi_app = WsgiApplication(application)
    from wsgiref.simple_server import make_server

    server = make_server('0.0.0.0', 8000, wsgi_app)
    print("Service de Décision d'Approbation démarré sur http://0.0.0.0:8000")
    server.serve_forever()
