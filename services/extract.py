from xml.sax.saxutils import escape
from spyne.util.wsgi_wrapper import run_twisted
from spyne.server.wsgi import WsgiApplication
from spyne.protocol.soap import Soap11
from spyne import Application, rpc, ServiceBase, Unicode, Integer, Iterable
import sys
import openai
import os
import re
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY


def getLoanInformations(letter):
    print(letter)

    assistant_prompt = 'You are a helpful assistant.'

    user_request = f"""I need to extract details regarding the tenant from this letter, 
        including their name, customer ID, the description of the property they intend to purchase, 
        address, monthly income and expenses, property price, etc. 
        Here’s the text: {letter}. The extracted result should be formatted as JSON. For the keys, 
        please apply camelCase formatting. In the description, for instance, format as JSON with the accommodation type 
        (e.g., home or apartment), the area size (e.g., 300m2), and address information such as town, postal code, 
        and any additional relevant property details.
        Do not return any text with the result.
        Only return JSON containing these elements.
        Here’s the schema you should follow for the response:
          {{{{"name": "John Doe",
            "customerId": "client-00X",
            "description": {{
                "accommodationType": "apartment",
                "surfaceArea": "300m2",
                "address": {{
                "town": "Paris",
                "postalCode": "75015",
                "completeAddress":"6e arrondissement de Paris"
                }}
            }},
            "contact": {{
                "phone": "+33 5 67784890",
                "email": "johndoe@gmail.com"
            }},
            "loanAmount": 12000,
            "monthlyIncome": 3700,
            "monthlyExpenses": 2400,
            "propertyPrice": 20000
            }}}}"""

    response = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                            messages=[{"role": "system", "content": assistant_prompt},
                                                      {"role": "user", "content": user_request}])
    status_code = response["choices"][0]["finish_reason"]
    assert status_code == "stop", f"The status code was {status_code}."
    return response["choices"][0]["message"]["content"]


class extractInformationsService(ServiceBase):
    @rpc(Unicode, _returns=Iterable(Unicode))
    def extraire_information(ctx, demande):
        infos = escape(getLoanInformations(demande))
        yield f'''{infos}'''


application = Application([extractInformationsService],
                          tns='spyne.examples.hello',
                          in_protocol=Soap11(validator='lxml'),
                          out_protocol=Soap11()
                          )


if __name__ == '__main__':

    wsgi_app = WsgiApplication(application)

    twisted_apps = [
        (wsgi_app, b'extractInformationsService'),
    ]

    sys.exit(run_twisted(twisted_apps, 8002))