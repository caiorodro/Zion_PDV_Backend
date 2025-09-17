import uvicorn
from fastapi import FastAPI

from multiprocessing import cpu_count, freeze_support

from cfg.config import Config as config

from routes.routePedido import router

app = FastAPI(
    title="Zion PDV Service",
    description="Micro-serviço de back-end ao sistema de PDV",
    version="1.3.3",
    terms_of_service="",
    contact={
        "name": "Zion Software",
        "url": "https://portalziondelivery.com.br/pdv",
        "email": "caiorodro@gmail.com",
    },
    license_info={"name": "Zion PDV", "url": "https://portalziondelivery.com.br/pdv"}
)

app.include_router(router)

if __name__ == "__main__":

    freeze_support()
    _workers = int(cpu_count() * 0.75)

    uvicorn.run(
        "main:app", 
        host=config.URL_SERVER, 
        port=config.PORT_SERVER,
        workers=_workers
    )
