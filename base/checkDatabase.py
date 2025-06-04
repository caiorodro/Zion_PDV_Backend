# import mysql.connector
# from sqlalchemydiff import compare

from cfg.config import Config

class checkTables:
    def __init__(self):
        pass

    #self.baseZion = f"mysql+mysqlconnector://{Config.DB_USERNAME}:{Config.DB_SERVER_NAME}@{Config.DB_USERNAME}/{Config.DB_NAME}"

    async def verifyNewTables(self):
        pass
    
#         sql = '''
# create table if not exists tb_mesa (
#     ID_MESA bigint not null AUTO_INCREMENT,
#     NUMERO_MESA varchar(10),
#     NOME_MESA varchar(30),
#     MESA_FECHADA int,
#     NUMERO_PEDIDO bigint,

#     PRIMARY KEY (ID_MESA),
#     KEY IDX_MESA18 (NUMERO_MESA, MESA_FECHADA),
#     KEY IDX_NUMERO_PEDIDO18 (NUMERO_PEDIDO)
# );
# '''

#         try:
#             connection = mysql.connector.connect(
#                 host=Config.DB_SERVER_NAME[0 : Config.DB_SERVER_NAME.index(":")],
#                 user=Config.DB_USERNAME,
#                 password=Config.DB_PASSWORD,
#                 database=Config.DB_NAME,
#             )

#             cursor = connection.cursor()
#             cursor.execute(sql)

#         except mysql.connector.Error as err:
#             print(f"MySQL Error: {err}")

#         finally:
#             if connection.is_connected():
#                 cursor.close()
#                 connection.close()

# class checkDatabase:
#     def __init__(self):
#         pass

    # async def checkDatabaseIntegrity(self):
    #     connection = mysql.connector.connect(
    #         host=Config.DB_SERVER_NAME[0 : Config.DB_SERVER_NAME.index(":")],
    #         user=Config.DB_USERNAME,
    #         password=Config.DB_PASSWORD,
    #         database=Config.DB_NAME,
    #     )

    #     try:
    #         cursor = connection.cursor()

    #         cursor.execute("SHOW TABLES")

    #         tables = [table[0] for table in cursor.fetchall()]

    #         for table in tables:
    #             print(f"Checking table: {table}")
    #             cursor.execute(f"CHECK TABLE {table}")
    #             results = cursor.fetchall()

    #             for row in results:
    #                 print(row)

    #     except mysql.connector.Error as err:
    #         print(f"MySQL Error: {err}")

    #     finally:
    #         if connection.is_connected():
    #             cursor.close()
    #             connection.close()


# class compareDatabase:
#     def __init__(self):
#         self.baseZion = "mysql+mysqlconnector://root:56Runna01@localhost:3306/zion"
#         self.baseSchema = (
#             "mysql+mysqlconnector://root:56Runna01@localhost:3306/zion_schema"
#         )

#     def compareSchema(self):
#         differences = compare(self.baseZion, self.baseSchema)

#         if len(differences.errors) == 0:
#             print("Database schema is Ok!")
#             return

#         print(differences.errors)
