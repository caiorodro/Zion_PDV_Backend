from datetime import datetime
import logging

class manageLog:

    def __init__(self):
        pass 

    def writeLog(self, message: str, trace: str):

        message = f'Message: {message} - Trace: {trace}'

        logging.basicConfig(
            filename='C:\\Projetos\\Zion_PDV_Nativo\\backend\\logs\\logPDV.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        logging.info(message)

    def setLogInfo(self, message: str, trace: str):
        message = f'Message: {message} - Trace: {trace}'

        d1 = datetime.strftime(
            datetime.now(),
            '%d%m%Y%H%M%S'
            )
        fileInfo = 'logs/log_{d1}.txt'
        
        with open(fileInfo, 'w', encoding='utf-8') as fi:
            fi.write(message)
