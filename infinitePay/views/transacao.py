import requests
from infinitePay.models.paymentDetails import paymentDetails

class Transacao:
    def __init__(self):
        pass

    def enviarPagamento(self, payment_details: paymentDetails):
        url = "infinitepaydash://infinitetap-app"

        payload = payment_details.__dict__

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(url, params=payload, headers=headers)

        return response.json()
