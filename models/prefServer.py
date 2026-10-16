from dataclasses import dataclass

@dataclass
class prefServer:
    SERVER: str
    PORT: int
    PORT_MYSQL: int
    # Default pra não quebrar cfg/prefServer.json existentes que ainda
    # não têm esse campo -- mesmo default do frontend (models/prefServer.py).
    PROTOCOL: str = 'http'