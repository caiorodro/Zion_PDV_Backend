import json
import os
from models.statusDePedido import statusDePedido
from models.prefServer import prefServer
from infra.db import DB_HOST, DB_PORT, DB_NAME as _DB_NAME, DB_USER, DB_PASSWORD

class Config(object):
    DEBUG = False
    TESTING = False
    SECRET_KEY = (
        "B\xe58\xcf\x95\x91q\xde\xbf\x96lD\x1eA\x0fkC\xcaO\x10\xd6\x1a8\xf1\xfc"
    )

    # Credenciais de banco: nunca em texto puro aqui — vêm do .env via infra/db.py.
    PORT_MYSQL = DB_PORT
    DB_SERVER_NAME = f"{DB_HOST}:{DB_PORT}"
    DB_NAME = _DB_NAME
    DB_USERNAME = DB_USER
    DB_PASSWORD = DB_PASSWORD

    ZIP_ADDRESS = "http://192.168.0.110:1199/csv/"
    URL_PRODUTOS = "app/templates/assets/images/"

    PDF_FILES = 'PDF'

    SESSION_COOKIE_SECURE = False
    URL_SERVER = '0.0.0.0'
    PORT_SERVER = 1199

    filePref = 'cfg/prefServer.json'
    objPref = None

    try:
        if os.path.exists(filePref):
            with open(filePref, 'r', encoding='utf-8') as fi:
                objPref = prefServer(**json.loads(fi.read()))

            URL_SERVER = objPref.SERVER
            PORT_SERVER = objPref.PORT

            PORT_MYSQL = objPref.PORT_MYSQL
            DB_SERVER_NAME = f"localhost:{PORT_MYSQL}"
    except Exception as ex:
        print(ex.args)

    ORIGEM_DELIVERY = ("Zé delivery", "IFood", "AnotaAi", "Goomer", "Delivery próprio")

    ORIGEM = (
        "Todos",
        "Zé Delivery",
        "IFood",
        "AnotaAi",
        "Goomer",
        "Delivery próprio",
        "Balcão",
    )

    STATUS = [
        statusDePedido(ID_STATUS=3, DESCRICAO="Finalizado"),
        statusDePedido(ID_STATUS=5, DESCRICAO="Cancelado"),
        statusDePedido(ID_STATUS=8, DESCRICAO="Em rota"),
        statusDePedido(ID_STATUS=9, DESCRICAO="Motoboy retornando"),
        statusDePedido(ID_STATUS=1, DESCRICAO="Enviado"),
    ]

    def getStatus(item):
        list1 = list(filter(lambda e: e.ID_STATUS == item.STATUS_PEDIDO, Config.STATUS))

        return list1[0].DESCRICAO if len(list1) > 0 else ""


class ProductionConfig(Config):
    pass


class DevelopmentConfig(Config):
    DEBUG = False
    TESTING = False
    SECRET_KEY = (
        "B\xe58\xcf\x95\x91q\xde\xbf\x96lD\x1eA\x0fkC\xcaO\x10\xd6\x1a8\xf1\xfc"
    )

    # DB_SERVER_NAME / DB_NAME / DB_USERNAME / DB_PASSWORD: herdados de Config,
    # vindos do .env via infra/db.py — nunca texto puro aqui.

    ZIP_ADDRESS = "http://192.168.15.5:1199/csv/"

    SESSION_COOKIE_SECURE = False
    URL_PRODUTOS = "app/templates/assets/images/"

    URL_RELATORIOS = "app/templates/PDF/"


class TestingConfig(Config):
    TESTING = True

    # DB_NAME de teste é diferente do de produção ("zion_thermo"); ajuste via
    # a variável de ambiente DB_NAME no .env usado ao rodar os testes.
    DB_NAME = os.getenv("DB_NAME_TESTE", "zion_thermo")

    ZIP_ADDRESS = "http://192.168.15.5:1199/csv"

    SESSION_COOKIE_SECURE = False
