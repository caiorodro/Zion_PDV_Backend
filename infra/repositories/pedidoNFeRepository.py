"""Acesso a dados da tabela tb_pedido_nfe."""

from types import SimpleNamespace
from typing import List

from infra import db
from base.mapTable import mapPedidoNFe

_COLUNAS = (
    "ID_PEDIDO_NFE, NUMERO_PEDIDO, XML_NOTA, RESPOSTA_SEFAZ, NUMERO_NF, SERIE_NF, CHAVE_ACESSO_NF, "
    "PROTOCOLO_AUTORIZACAO, PROCESSADO, ASSINATURA_NFCE, DATA_AUTORIZACAO_NFCE, CHAVE_PEDIDO, "
    "XML_DEVOLUCAO, NUMERO_NF_DEVOLUCAO, GERAR_DANFE, ID_EMPRESA, CHAVE_NF_DEVOLUCAO, "
    "ID_PEDIDO_NFE_LOCAL, ID_TERMINAL"
)


class PedidoNFeRepository:
    def listar_processadas(self, numero_pedido: int, processado: int) -> List[mapPedidoNFe]:
        sql = (
            f"SELECT {_COLUNAS} FROM tb_pedido_nfe "
            "WHERE NUMERO_PEDIDO = %s AND PROCESSADO = %s"
        )
        return db.query_all(sql, (numero_pedido, processado), map_cls=mapPedidoNFe)

    def listar_por_status(self, numero_pedido: int, status: List[int]) -> List[mapPedidoNFe]:
        placeholders = ", ".join(["%s"] * len(status))
        sql = (
            f"SELECT {_COLUNAS} FROM tb_pedido_nfe "
            f"WHERE NUMERO_PEDIDO = %s AND PROCESSADO IN ({placeholders})"
        )
        return db.query_all(sql, (numero_pedido, *status), map_cls=mapPedidoNFe)

    def listar_por_pedido(self, numero_pedido: int) -> List[mapPedidoNFe]:
        sql = f"SELECT {_COLUNAS} FROM tb_pedido_nfe WHERE NUMERO_PEDIDO = %s"
        return db.query_all(sql, (numero_pedido,), map_cls=mapPedidoNFe)

    def listar_dados_autorizados(self, numero_pedido: int):
        sql = (
            "SELECT XML_NOTA, CHAVE_ACESSO_NF, PROTOCOLO_AUTORIZACAO FROM tb_pedido_nfe "
            "WHERE NUMERO_PEDIDO = %s AND PROCESSADO = 10"
        )
        return db.query_all(sql, (numero_pedido,), map_cls=SimpleNamespace)

    def inserir(
        self,
        numero_pedido: int,
        numero_nf: int,
        serie_nf: str,
        processado: int,
        chave_acesso_nf: str = "",
        protocolo_autorizacao: str = "",
        assinatura_nfce: str = "",
        id_empresa: int = 1,
        xml_nota: str = "",
        conn=None,
    ) -> int:
        sql = (
            "INSERT INTO tb_pedido_nfe (NUMERO_PEDIDO, XML_NOTA, RESPOSTA_SEFAZ, NUMERO_NF, SERIE_NF, "
            "CHAVE_ACESSO_NF, PROTOCOLO_AUTORIZACAO, PROCESSADO, ASSINATURA_NFCE, "
            "DATA_AUTORIZACAO_NFCE, CHAVE_PEDIDO, XML_DEVOLUCAO, NUMERO_NF_DEVOLUCAO, GERAR_DANFE, "
            "ID_EMPRESA, CHAVE_NF_DEVOLUCAO, ID_PEDIDO_NFE_LOCAL, ID_TERMINAL) "
            "VALUES (%s, %s, '', %s, %s, %s, %s, %s, %s, '', '', '', 0, 0, %s, '', 0, 0)"
        )
        params = (
            numero_pedido,
            xml_nota,
            numero_nf,
            serie_nf,
            chave_acesso_nf,
            protocolo_autorizacao,
            processado,
            assinatura_nfce,
            id_empresa,
        )
        if conn is not None:
            return db.execute_in(conn, sql, params)
        return db.execute(sql, params)

    def atualizar_finalizacao(
        self,
        numero_pedido: int,
        xml_nota: str,
        numero_nf: int,
        chave_acesso_nf: str,
        assinatura_nfce: str,
        data_autorizacao_nfce,
        processado: int,
    ) -> None:
        """Correção: o código anterior filtrava com
        `NUMERO_PEDIDO == X and PROCESSADO == 1` — em Python, `and` entre duas
        expressões do SQLAlchemy não combina as duas condições no SQL, só
        avalia a segunda (a primeira é sempre "truthy"). Na prática, o UPDATE
        rodava em QUALQUER pedido com PROCESSADO=1, não só no pedido pedido —
        risco real de gravar XML/chave de acesso de um pedido em outro."""
        sql = (
            "UPDATE tb_pedido_nfe SET XML_NOTA = %s, NUMERO_NF = %s, CHAVE_ACESSO_NF = %s, "
            "ASSINATURA_NFCE = %s, DATA_AUTORIZACAO_NFCE = %s, PROCESSADO = %s "
            "WHERE NUMERO_PEDIDO = %s AND PROCESSADO = 1"
        )
        params = (
            xml_nota, numero_nf, chave_acesso_nf, assinatura_nfce,
            data_autorizacao_nfce, processado, numero_pedido,
        )
        db.execute(sql, params)
