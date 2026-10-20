from dataclasses import dataclass

@dataclass
class filtroFormasPagtoCaixa:
    ID_CAIXA: int
    FORMA_PAGTO: str
    NUMERO_IMPRESSORA: int
    # Preenchido só na verificação antes de abrir caixa (verificaCaixaAberto)
    ID_USUARIO: int = 0
