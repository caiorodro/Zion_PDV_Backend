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


    def __del__(self):
        ctx.session.close_all()