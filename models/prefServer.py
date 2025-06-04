from pydantic import BaseModel

class prefServer(BaseModel):
    SERVER: str
    PORT: int
    PORT_MYSQL: int