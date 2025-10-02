from sqlalchemy import text

import base.qModel as ctx

class checkTables:
    def __init__(self):
        pass

    async def impactDatabase(self):

        sql = '''create table if not exists tb_numero_nota (
            ID_NUMERO bigint not null AUTO_INCREMENT,
            NUMERO_NF bigint,
            SERIE_NF varchar(10),
            PRIMARY KEY (ID_NUMERO)
        );'''

        ctx.session.execute(text(sql))

        try:
            tributo = [
                'alter table tb_tributo add IBS numeric(10,2);',
                'alter table tb_tributo add CBS numeric(10,2);',
                'alter table tb_tributo add ISERV numeric(10,2);'
            ]

            [ctx.session.execute(item) for item in tributo]

        except:
            pass

        codigoIFood = 'alter table tb_produto modify column CODIGO_IFOOD VARCHAR(50) null;'
        ctx.session.execute(codigoIFood)

    def __del__(self):
        ctx.session.close_all()