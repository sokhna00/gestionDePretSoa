import os
import ast
import json
import re
import requests
import textract
import xml.etree.ElementTree as ET
from flask import Flask, request, render_template, flash
from dotenv import load_dotenv
import logging

# Configuration
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Pour utiliser flash

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# URLs des services
SERVICE_EXTRACT_INFO_URL = "http://localhost:8002/extractInformationsService"
SERVICE_SOLVABILITE_URL = "http://localhost:8003/solvabiliteService"
SERVICE_EVAL_PROPRIETE_URL = "http://localhost:8004/evaluationProprieteService"


def getResults(data):
    try:
        namespaces = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                      'tns': 'spyne.examples.hello'}
        root = ET.fromstring(data)
        response_element = root.find('.//tns:string', namespaces)
        if response_element is None:
            logger.warning("Élément de réponse non trouvé dans le XML")
            return None
        return response_element.text
    except ET.ParseError as e:
        logger.error(f"Erreur lors de l'analyse XML: {e}")
        return None


def aproval(url, demande):
    headers = {'content-type': 'application/soap+xml; charset=utf-8'}
    try:
        response = requests.post(url, data=demande, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"Erreur lors de la requête au service {url}: {e}")
        return None


def decision(valeur, propertyPrice, litiges, score, financial_cap, name):
    if (valeur <= propertyPrice) and (not litiges) and (score > 50) and (financial_cap > 0):
        return f"""Cher Monsieur {name},

Votre demande de prêt immobilier a été APPROUVÉE.

Points clés :
• Valeur du bien adéquate
• Absence de litiges
• Score de crédit satisfaisant
• Capacité financière suffisante

Prochaines étapes :
1. Visitez notre agence pour finaliser le dossier
2. Apportez : pièce d'identité, justificatifs de revenus, avis d'imposition, compromis de vente

Notre conseiller est à votre disposition pour toute question.

Cordialement,
L'équipe des prêts immobiliers"""
    else:
        raisons = []
        if valeur > propertyPrice:
            raisons.append("• Valeur estimée/prix d'achat")
        if litiges:
            raisons.append("• Présence de litiges potentiels")
        if score <= 50:
            raisons.append("• Score de crédit insuffisant")
        if financial_cap <= 0:
            raisons.append("• Capacité financière limitée")

        return f"""Cher Monsieur {name},

Nous regrettons de vous informer que votre demande de prêt immobilier n'a pas été approuvée.

Raisons principales :
{chr(10).join(raisons)}

Recommandations pour les 6 prochains mois :
1. Améliorez votre score de crédit
2. Augmentez votre épargne
3. Stabilisez votre situation professionnelle
4. Réévaluez le bien immobilier visé

Contactez-nous pour un rendez-vous de conseil personnalisé.

Cordialement,
L'équipe des prêts immobiliers"""


def extract_text(file_path):
    try:
        text = textract.process(file_path).decode("utf-8")
        return clean_text(text)
    except Exception as e:
        logger.error(f"Erreur lors de l'extraction du texte: {e}")
        return None


def clean_text(text):
    pattern = r'[^\x00-\x7F]+'
    return re.sub(pattern, '', text)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Aucun fichier n\'a été sélectionné', 'error')
            return render_template('upload.html')

        file = request.files['file']
        if file.filename == '':
            flash('Aucun fichier n\'a été sélectionné', 'error')
            return render_template('upload.html')

        if file:
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)

            letter_text = extract_text(file_path)
            if not letter_text:
                flash('Impossible d\'extraire le texte du fichier', 'error')
                return render_template('upload.html')

            # Extraction des informations
            extract_enveloppeSOAP = f'''\
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:spy="spyne.examples.hello">
                    <soapenv:Header/>
                    <soapenv:Body>
                        <spy:extraire_information>
                            <spy:demande>{letter_text}</spy:demande>
                        </spy:extraire_information>
                    </soapenv:Body>
                </soapenv:Envelope>'''

            extract_data_result = aproval(SERVICE_EXTRACT_INFO_URL, extract_enveloppeSOAP)
            if not extract_data_result:
                flash('Erreur lors de l\'extraction des informations', 'error')
                return render_template('upload.html')

            result = getResults(extract_data_result)
            if not result:
                flash('Erreur lors du traitement des informations extraites', 'error')
                return render_template('upload.html')

            client_infos = json.loads(result)

            # Vérification de la solvabilité
            if 'customerId' not in client_infos:
                flash('ID client manquant dans les informations extraites', 'error')
                return render_template('upload.html')

            solvabilite_enveloppeSOAP = f'''\
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:spy="spyne.examples.hello">
                    <soapenv:Header/>
                    <soapenv:Body>
                        <spy:etudier_solvabilite>
                            <spy:clientId>{client_infos['customerId']}</spy:clientId>
                        </spy:etudier_solvabilite>
                    </soapenv:Body>
                </soapenv:Envelope>'''

            solvabilite_data_result = aproval(SERVICE_SOLVABILITE_URL, solvabilite_enveloppeSOAP)
            if not solvabilite_data_result:
                flash('Erreur lors de la vérification de solvabilité', 'error')
                return render_template('upload.html')

            result = getResults(solvabilite_data_result)
            if not result:
                flash('Erreur lors du traitement des données de solvabilité', 'error')
                return render_template('upload.html')

            solvabilite_result = ast.literal_eval(result)

            # Évaluation de la propriété
            if 'description' not in client_infos or 'address' not in client_infos['description']:
                flash('Informations sur la propriété manquantes', 'error')
                return render_template('upload.html')

            address = client_infos['description']['address']
            complete_address = address.get('completeAdress') or address.get('completeAddress')
            if not complete_address:
                flash('Adresse complète manquante', 'error')
                return render_template('upload.html')

            evalPropriete_enveloppeSOAP = f'''\
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:spy="spyne.examples.hello">
                    <soapenv:Header/>
                    <soapenv:Body>
                        <spy:evaluer_propriete>
                            <spy:ville>{address['town']}</spy:ville>
                            <spy:taille_logement>{int(client_infos['description']['surfaceArea'].split('m')[0])}</spy:taille_logement>
                            <spy:adresse>{complete_address}</spy:adresse>
                        </spy:evaluer_propriete>
                    </soapenv:Body>
                </soapenv:Envelope>'''

            evalPropriete_data_result = aproval(SERVICE_EVAL_PROPRIETE_URL, evalPropriete_enveloppeSOAP)
            if not evalPropriete_data_result:
                flash('Erreur lors de l\'évaluation de la propriété', 'error')
                return render_template('upload.html')

            result = getResults(evalPropriete_data_result)
            if not result:
                flash('Erreur lors du traitement des données d\'évaluation de la propriété', 'error')
                return render_template('upload.html')

            evalPropriete_result = ast.literal_eval(result)

            # Prise de décision
            decision_message = decision(
                evalPropriete_result['valeur'],
                client_infos['propertyPrice'],
                evalPropriete_result['litiges'],
                solvabilite_result['score'],
                solvabilite_result['financial_cap'],
                client_infos['name']
            )

            return render_template('upload.html', result="Traitement terminé avec succès", decision=decision_message)

    return render_template('upload.html')


if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)