from spyne.util.wsgi_wrapper import run_twisted
from spyne.server.wsgi import WsgiApplication
from spyne.protocol.soap import Soap11
from spyne import Application, rpc, ServiceBase, Unicode, Iterable
import sys
import logging
from utils import database

# Configuration du niveau de journalisation
logging.basicConfig(level=logging.DEBUG)

class ClientSolvency:
    """Classe représentant l'évaluation de la solvabilité d'un client."""

    def __init__(self, client_id):
        self.client_id = client_id
        self.credit_data = database.CreditBureauDatabase.get_client_credit_data(client_id)
        self.revenu_mensuel, self.depense_mensuel = database.clientFinancialDatabase.get_client_financial_data(client_id)

    def calculate_score(self):
        """Calcule le score de solvabilité basé sur les données de crédit du client."""
        if self.credit_data == (0, 0, False):
            return 100
        if self.credit_data[1] >= 2 and self.credit_data[2]:  # Retards importants et antécédent de faillite
            return 0
        if self.credit_data[1] < 2 and self.credit_data[0] < 1000:
            return 80
        if self.credit_data[1] < 2 and self.credit_data[0] > 1000:
            return 60
        return 50  # Score par défaut pour les cas non couverts

    def calculate_financial_capacity(self):
        """Calcule la capacité financière du client."""
        return self.revenu_mensuel - self.depense_mensuel

    def get_solvency_info(self):
        """Récupère les informations de solvabilité complètes sous forme de dictionnaire."""
        return {
            'financial_cap': self.calculate_financial_capacity(),
            'score': self.calculate_score()
        }

class SolvabiliteService(ServiceBase):
    @rpc(Unicode, _returns=Iterable(Unicode))
    def etudier_solvabilite(ctx, clientId):
        """Étudie la solvabilité d'un client et retourne les informations calculées."""
        client_solvency = ClientSolvency(clientId)
        solvency_info = client_solvency.get_solvency_info()
        yield f'{solvency_info}'

# Configuration de l'application Spyne
application = Application(
    [SolvabiliteService],
    tns='spyne.examples.hello',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

if __name__ == '__main__':
    # Création et démarrage de l'application WSGI
    wsgi_app = WsgiApplication(application)
    twisted_apps = [(wsgi_app, b'solvabiliteService')]

    # Démarrage du serveur sur le port 8003
    sys.exit(run_twisted(twisted_apps, 8003))
