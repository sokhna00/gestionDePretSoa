from spyne import Application, rpc, ServiceBase, ComplexModel, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication


class DictionaryItem(ComplexModel):
    __namespace__ = 'Client_solvency_status'
    key = Unicode
    value = Unicode


class CreditBureauDatabase:
    # sample credit data for clients
    data = {
        # dettes en cours, nombre de payement en retard et antécédent de faillite
        "client-001": (5000, 2, False),
        "client-002": (2000, 0, False),
        "client-003": (10000, 5, True)
    }

    @classmethod
    def get_client_credit_data(cls, client_id):
        """Retrieve credit data for a specific client"""
        return cls.data.get(client_id, (0, 0, False))


class clientFinancialDatabase:
    data = {
        "client-001": {"nom": "John Doe", "adresse": "123 Neuilly St", "revenu_mensuel": 4000, "depense_mensuel": 3000},
        "client-002": {"nom": "Alice Smith", "adresse": "456 Elm St", "revenu_mensuel": 3000, "depense_mensuel": 2500},
        "client-003": {"nom": "Bob Johnson", "adresse": "789 MaOakin St", "revenu_mensuel": 6000, "depense_mensuel": 5500}
    }

    @classmethod
    def client_details_data(cls, client_id):
        client_data = cls.data.get(client_id, {})
        nom = client_data.get("nom", "N/A")
        adresse = client_data.get("adresse", "N/A")
        return nom, adresse

    @classmethod
    def get_client_financial_data(cls, client_id):
        client_data = cls.data.get(client_id, {})
        revenu_mensuel = client_data.get("revenu_mensuel", 0)
        depense_mensuel = client_data.get("depense_mensuel", 0)
        return revenu_mensuel, depense_mensuel
