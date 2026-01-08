import requests
from infinitePay.models.paymentDetails import paymentDetails, itemDetail

class Transacao:

    def __init__(self):
        pass

    def sendPayment_InfinitePay(self) -> str:

        payLoad = paymentDetails(
            handle="caio-zion",
            items=[
                itemDetail(
                    quantity=1,
                    price=120,
                    description="Becks 330ml"
                ).__dict__
            ],
            order_nsu="8065"
        ).__dict__

        url = "https://api.infinitepay.io/invoices/public/checkout/links"

        headers = {
            "Content-Type": "application/json"
        }

        response = requests.post(
            url, 
            json=payLoad, 
            headers=headers
        )

        if response.status_code == 200:
            url = response.json()['url']

            # Link de envio ao cliente para checkout.
            # Nesse link o cliente vai precisar se cadasrtar, formar endereço, email e telefone
            # E por fim escolher a forma de pagamento: ? credit, pix 
            # Ao final a InfinitePay manda o rsultado do pagamento para o url de webhook

            return url

        print("Erro ao criar pagamento:", response.text)

        return ''

    def getPaymentResult(self, url: str):
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "handle": "caio-zion",
            "order_nsu": "8065",
            "transaction_nsu": '',
            "slug": "codigo-da-fatura"
        }

        status_response = requests.get(
            url, 
            headers=headers,
            params=payload
        )

        if status_response.status_code == 200:
            status_info = status_response.json()

            print("Status do pagamento:", status_info["status"])
        else:
            print("Erro ao consultar status:", status_response.text)
