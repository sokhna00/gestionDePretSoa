from spyne.util.wsgi_wrapper import run_twisted
from spyne.server.wsgi import WsgiApplication
from spyne.protocol.soap import Soap11
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Iterable
import sys
import logging

# Configuration de base du journal de débogage
logging.basicConfig(level=logging.DEBUG)


class LitigeVerifier:
    """Classe pour vérifier si une adresse est associée à des litiges."""

    _adresses_avec_litiges = {
        "45 boulevard de mousse, Neuilly-Plaisance",
        "19 Rue de la republique, Versailles",
        "11 rue des saints, Paris"
    }

    @classmethod
    def verifier(cls, adresse_logement):
        """Vérifie si l'adresse fournie est dans la liste des adresses avec litiges."""
        return adresse_logement in cls._adresses_avec_litiges


class EstimationPropriete:
    """Classe pour estimer la valeur d'une propriété."""

    _valeurs_reference = {
        "Versailles": 300,
        "Paris": 350,
        "Bordeaux": 200
    }

    def __init__(self, taille_logement, ville, adresse):
        self.taille_logement = taille_logement
        self.ville = ville
        self.adresse = adresse

    def calculer_valeur(self):
        """Calcule la valeur estimée de la propriété."""
        valeur_par_metre_carre = self._valeurs_reference.get(self.ville, 200)
        return self.taille_logement * valeur_par_metre_carre

    def generer_estimation(self):
        """Génère un dictionnaire avec la valeur estimée et le statut des litiges."""
        return {
            "valeur": self.calculer_valeur(),
            "litiges": LitigeVerifier.verifier(self.adresse)
        }


class EvaluationProprieteService(ServiceBase):
    """Service SOAP pour évaluer les propriétés."""

    @rpc(Unicode, Integer, Unicode, _returns=Iterable(Unicode))
    def evaluer_propriete(ctx, ville, taille_logement, adresse):
        estimation = EstimationPropriete(taille_logement, ville, adresse)
        valeur_estimee = estimation.generer_estimation()
        yield f"{valeur_estimee}"


# Configuration de l'application Spyne
application = Application(
    [EvaluationProprieteService],
    tns='spyne.examples.hello',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

if __name__ == '__main__':
    # Création et démarrage de l'application WSGI
    wsgi_app = WsgiApplication(application)
    twisted_apps = [(wsgi_app, b'evaluationProprieteService')]

    # Démarrage du serveur sur le port 8004
    sys.exit(run_twisted(twisted_apps, 8004))
