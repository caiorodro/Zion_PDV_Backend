import base64
import datetime
import json
import math
from decimal import Decimal

from base.authentication import authentication
from utils import currency_formatter

class qBase:
    def __init__(self, keep=None):
        if keep is not None:
            b1 = bytes(keep, encoding="raw_unicode_escape")
            result = authentication.decode_auth_token(b1)

    def threatColunms(self, row):
        isStr = type(row) is str

        if not isStr:
            retorno = list(row)

            for i, item in enumerate(retorno):
                if type(retorno[i]) == str:
                    retorno[i] = retorno[i].replace('"', '"')
                elif type(retorno[i]) == int:
                    pass
                elif type(retorno[i]) == Decimal:
                    retorno[i] = float(item)
        elif isStr:
            retorno = row.replace('"', '"')

        return retorno

    def toJson(self, lista):
        lista1 = []

        lista1.extend(list(map(self.threatColunms, lista)))

        return json.dumps(lista1)

    def toDict(self, lista):
        dict1 = []

        [dict1.append(item._asdict()) for item in lista]

        return dict1

    def toDict1(self, lista):
        dict1 = []

        dict1.extend(list(map(self.threatColunms, lista)))

        return [dict1]

    def classToDict(self, lista):
        dict1 = [item.__dict__ for item in lista]

        return dict1

    def queryToDict(self, query):
        dict1 = []

        for item in query:
            dict1.append(item._asdict())

        return str(dict1)

    def toRoute(self, message, status: int):
        return {"message": message}, status

    def TrataData(self, dt1=None):
        if dt1 is None:
            dt1 = datetime.datetime.today()

        retorno = "{0}/{1}/{2}".format(
            str(dt1.day).rjust(2, "0"), str(dt1.month).rjust(2, "0"), str(dt1.year)
        )

        return retorno

    def TrataDataHora(self, dt1=None):
        if dt1 is None:
            dt1 = datetime.datetime.now()

        retorno = "{0}-{1}-{2} {3}:{4}".format(
            str(dt1.day).rjust(2, "0"),
            str(dt1.month).rjust(2, "0"),
            str(dt1.year),
            str(dt1.hour).rjust(2, "0"),
            str(dt1.minute).rjust(2, "0"),
        )

        return retorno

    def currency(self, _number):

        _number = currency_formatter.format_currency(_number)

        x = _number.split(" ")

        _sign = ""
        _value = ""

        for item in x:
            if len(self.onlyNumbers(item)) == 0:
                _sign = item
            elif len(self.onlyNumbers(item)) > 0:
                _value = item

        return " ".join((_sign, _value)).strip()

    def percent(self, _number):
        retorno = str(float(_number)).replace(".", ",")

        return retorno + "%"

    def onlyNumbers(self, _str):
        digits = "0123456789"
        retorno = ""

        for i in range(0, len(_str)):
            if _str[i : i + 1] in digits:
                retorno += _str[i : i + 1]

        return retorno

    def onlyNumbersDot(self, _str):
        digits = "0123456789,."
        retorno = ""

        for i in range(0, len(_str)):
            if _str[i : i + 1] in digits:
                retorno += _str[i : i + 1]

        return retorno

    def onlyNumbersComma(self, _str):
        _nums = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ","]

        return "".join([item for item in _str if item in _nums])

    def onlyNumbersDotMinus(self, _str):
        digits = "0123456789,.-"
        retorno = ""

        for i in range(0, len(_str)):
            if _str[i : i + 1] in digits:
                retorno += _str[i : i + 1]

        return retorno

    def distanciaEntre2Pontos(self, lat1, lng1, lat2, lng2):
        coords_1 = (float(lat1), float(lng1))
        coords_2 = (lat2, lng2)

        try:
            p1 = coords_1
            p2 = coords_2

            distance = math.sqrt(((p1[0] - p2[0]) ** 2) + ((p1[1] - p2[1]) ** 2))

            if distance > 0:
                distance = distance * 1.25

            return round(distance * 100, 3)
        except:
            return 0.000

    def cleanSpecialChars(self, str1):
        retorno = str1

        retorno = retorno.replace("´", "")
        retorno = retorno.replace("'", "")
        retorno = retorno.replace("°", " ")
        retorno = retorno.replace("º", " ")
        retorno = retorno.replace("ª", " ")
        retorno = retorno.replace("À", "A")
        retorno = retorno.replace("Á", "A")
        retorno = retorno.replace("Ã", "A")
        retorno = retorno.replace("Â", "A")
        retorno = retorno.replace("É", "E")
        retorno = retorno.replace("Ê", "E")
        retorno = retorno.replace("Í", "I")
        retorno = retorno.replace("Ó", "O")
        retorno = retorno.replace("Õ", "O")
        retorno = retorno.replace("Ô", "O")
        retorno = retorno.replace("Ú", "U")
        retorno = retorno.replace("Ç", "C")
        retorno = retorno.replace("À", "A")
        retorno = retorno.replace("&", " ")

        retorno = retorno.replace("à", "a")
        retorno = retorno.replace("á", "a")
        retorno = retorno.replace("ã", "a")
        retorno = retorno.replace("â", "a")
        retorno = retorno.replace("é", "e")
        retorno = retorno.replace("ê", "e")
        retorno = retorno.replace("í", "i")
        retorno = retorno.replace("ó", "o")
        retorno = retorno.replace("õ", "o")
        retorno = retorno.replace("ô", "o")
        retorno = retorno.replace("ú", "u")
        retorno = retorno.replace("ç", "c")

        retorno = retorno.replace("%", "")
        retorno = retorno.replace("'", "")
        retorno = retorno.replace("-", "")
        retorno = retorno.replace("/", "")
        retorno = retorno.replace("\\", "")
        retorno = retorno.replace(".", "")
        retorno = retorno.replace("(", "")
        retorno = retorno.replace(")", "")
        retorno = retorno.replace(":", "")
        retorno = retorno.replace("", "")
        retorno = retorno.replace("  ", " ")
        retorno = retorno.replace("   ", " ")
        retorno = retorno.replace("    ", " ")

        return retorno

    def getStringBytesFromImage(self, imageBytes):
        retorno = ""

        if isinstance(imageBytes, str):
            with open(imageBytes, "rb") as f:
                retorno = base64.b64encode(f.read())
                f.close()

        elif isinstance(imageBytes, bytes):
            retorno = base64.b64encode(imageBytes)

        return str(retorno)[2:-1]

    def dictToClass(self, _dict, _object):
        retorno = json.loads(
            str(_dict).replace("'", '"'), object_hook=lambda x: _object(**x)
        )

        return retorno

    def maxString(self, str1: str, max: int) -> str:
        retorno = str1[0:max] if len(str1) > max else str1

        return retorno
