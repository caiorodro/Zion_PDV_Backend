
import base64
import os
from typing import List
import qrcode

from base.qBase import qBase

import base.qModel as ctx
from models.filtroPedido import filtroPedido

from cfg.config import Config

class cupomFiscal:
    def __init__(self):
        self.qBase = qBase()
        self.totalTributos = 0.00
        self.config = Config()

    async def getPDF(self, filtro: filtroPedido) -> str:
        p = ctx.mapPedido
        ip = ctx.mapItemPedido
        pg = ctx.mapPedidoPagamento
        nf = ctx.mapPedidoNFe
        e = ctx.mapEmpresa

        empresa = ctx.session.query(e).first()

        numeroPedido = int(filtro.FILTRO)

        pedido = ctx.session.query(p).filter(
            p.NUMERO_PEDIDO == numeroPedido
            ).first()
        
        items = ctx.session.query(ip).filter(
            ip.NUMERO_PEDIDO == numeroPedido
            ).all()
        
        pagamentos = ctx.session.query(pg).filter(
            pg.NUMERO_PEDIDO == numeroPedido
            ).all()
        
        nfce = ctx.session.query(nf).filter(*(
            nf.NUMERO_PEDIDO == numeroPedido,
            nf.PROCESSADO == 10
            )).all()

        if len(nfce) == 0:
            raise Exception('nota fiscal não encontrada para esse pedido')
        
        conteudo = [
            "<table style='width: 90%; font-family: tahoma; font-size: 11pt; text-align: center;'>"
        ]

        conteudo.extend(
            await self._getContentPedido(
                pedido,
                empresa
            ))
        
        conteudo.extend(
            await self._getContentItemPedido(
                items
            )
        )

        space1 = 15

        if float(pedido.TAXA_ENTREGA) > 0.00:
            s4 = 'Taxa de entrega'.rjust(space1, '.')

            conteudo.extend([
                "<tr>",
                f"<td style=\"width: 100%;\" colspan=3><b>{s4}</b>: {self.qBase.currency(float(pedido.TAXA_ENTREGA))}</td>",
                "</tr>"
                ])

        s1 = 'SubTotal'.rjust(space1+3, '.')
        s2 = 'Desconto'.rjust(space1+3, '.')
        s3 = 'Total'.rjust(space1+4, '.')

        conteudo.extend([
            "<tr>",
            f"<td style=\"width: 100%;\" colspan=3><b>{s1}</b>: {self.qBase.currency(float(pedido.TOTAL_PRODUTOS))}</td>",
            "</tr>",
            "<tr>",
            f"<td style=\"width: 100%;\" colspan=3><b>{s2}</b>: {self.qBase.currency(float(pedido.DESCONTO))}</td>",
            "</tr>",
            "<tr>",
            f"<td style=\"width: 100%;\" colspan=3><b>{s3}</b>: {self.qBase.currency(float(pedido.TOTAL_PEDIDO))}</td>",
            "</tr>"
        ])

        conteudo.extend(
            self._linhaPontilhada()
            )

        pg = "|".join(
            [item.FORMA_PAGTO for item in pagamentos]
        )

        conteudo.extend([
            "<tr>",
            f"<td colspan=3 style=\"width: 100%;\"><b>Forma de pagamento:</b> {pg}</td>",
            "</tr>",
            "<tr>",
            f"<td colspan=3 style=\"width: 100%;\"><b>Troco:</b>{self.qBase.currency(float(pedido.TROCO))}</td>",
            "</tr>"
        ])

        conteudo.extend(
            self._linhaPontilhada()
            )

        conteudo.extend([
            "<tr>",
            f"<td colspan=3 style=\"width: 100%;\">Tributos totais (lei federal 12.741/12): {self.qBase.currency(self.totalTributos)}</td>",
            "</tr>"
        ])

        conteudo.extend(
            self._linhaPontilhada()
            )

        conteudo.extend([
            "<tr>",
            f"<td colspan=3 style=\"width: 100%;\">Valor aproximado dos tributos: {self.qBase.currency(self.totalTributos)} Fonte IBPT / FECOMERCIO ({empresa.UF}) 02c353</td>",
            "</tr>"
        ])

        conteudo.extend([
            "<tr>",
            "<td colspan=3 style=\"width: 100%; text-align: left;\">&nbsp;</td>",
            "</tr>",
            "<tr>",
            f"<td colspan=3 style=\"width: 100%;\"><b>{self.qBase.TrataDataHora(pedido.DATA_HORA)}</b></td>",
            "</tr>"
            ])

        conteudo.extend([
            "<tr>",
            "<td colspan=3 style=\"width: 100%; text-align: left;\">&nbsp;</td>",
            "</tr>",
            "<tr>",
            "<td colspan=3 style=\"width: 100%;\">OBRIGADO, VOLTE SEMPRE!</td>",
            "</tr>"
        ])

        conteudo.extend(
            self._linhaPontilhada()
            )

        nf = str(nfce[0].NUMERO_NF).zfill(9)

        conteudo.extend([
            "<tr>",
            "<td colspan=3 style=\"width: 100%; text-align: left;\">&nbsp;</td>",
            "</tr>",
            "<tr>",
            f"<td colspan=3 style=\"width: 100%;\"><b>NFC-e nr:</b> {nf}</td>",
            "</tr>"
        ])

        chave = nfce[0].CHAVE_ACESSO_NF
        chave = self.trataChave(chave)

        conteudo.extend([
            "<tr>",
            "<td colspan=3 style=\"width: 100%; text-align: left;\">&nbsp;</td>",
            "</tr>",
            "<tr>",
            f"<td colspan=6 style=\"width: 100%;\">{chave}</td>",
            "</tr>"
        ])

        retorno = await self._generatePDF(
            conteudo,
            nf,
            nfce[0].ASSINATURA_NFCE
            )

        return retorno
    
    async def _getContentPedido(self, pedido: ctx.mapPedido, empresa: ctx.mapEmpresa) -> List:
        
        linhas = [
            "<tr>",
            "<td style=\"width: 25%;\"></td>",
            f"<td style=\"width: 50%;\">{empresa.RAZAO_SOCIAL}</td>",
            "<td style=\"width: 25%;\"></td>",
            "</tr>"
        ]

        linhas.extend([
            "<tr>",
            "<td style=\"width: 25%;\"></td>",
            f"<td style=\"width: 50%;\">{empresa.ENDERECO}</td>",
            "<td style=\"width: 25%;\"></td>",
            "</tr>"
        ])

        linhas.extend([
            "<tr>",
            "<td style=\"width: 25%;\"></td>",
            f"<td style=\"width: 50%;\">CNPJ:{empresa.CNPJ} - I.E: {empresa.IE}</td>",
            "<td style=\"width: 25%;\"></td>",
            "</tr>"
        ])

        linhas.extend(
            self._linhaPontilhada()
        )

        linhas.extend([
            "<tr>",
            f"<td colspan=3 style=\"width: 100%; font-weight: bold;\">DOCUMENTO AUXILIAR DE NOTA FISCAL ELETRONICA AO CONSUMIDOR</td>",
            "</tr>"       
        ])

        linhas.extend(
            self._linhaPontilhada()
        )

        linhas.extend([
            "<tr>",
            f"<td colspan=3 style=\"width: 100%;\">CPF/CNPJ do consumidor: {pedido.CPF}</td>",
            "</tr>",
            "<tr>",
            f"<td colspan=3 style=\"width: 100%; font-weight: bold;\">{pedido.NOME_CLIENTE}</td>",
            "</tr>"
            ])

        linhas.extend(
            self._linhaPontilhada()
        )

        return linhas

    async def _getContentItemPedido(self, items: List[ctx.mapItemPedido]) -> List:
        linhas = [
            "<tr>",
            "<td colspan=3>",
            "<table style=\"width: 100%; font-family: tahoma; font-size: 11pt;\">",
            "<tr>",
            "<td style=\"width: 30%; font-weight: bold;\"></td>",
            "<td style=\"width: 15%; font-weight: bold;\">Qtde</td>",
            "<td style=\"width: 30%; font-weight: bold;\">Produto</td>",
            "<td style=\"width: 5%; font-weight: bold;\">Un</td>",
            "<td style=\"width: 20%;\"></td>",
            "</tr>",
            "</table>",
            "</td>",
            "</tr>"
        ]

        linhas.extend([
            "<tr>",
            "<td colspan=3>",
            "<table style=\"width: 100%; font-family: tahoma; font-size: 11pt;\">",
            "<tr>",
            "<td style=\"width: 30%;\"></td>",
            "<td style=\"width: 5%; font-weight: bold;\"</td>",
            "<td style=\"width: 10%; font-weight: bold;\">Vl Un</td>",
            "<td style=\"width: 10%; font-weight: bold;\">Vl Tr</td>",
            "<td style=\"width: 25%; font-weight: bold;\">Total</td>",
            "<td style=\"width: 20%;\"></td>",
            "</tr>",
            "</table>",
            "</td>",
            "</tr>"
        ])

        linhas.extend(
            self._linhaPontilhada()
            )

        for i, item in enumerate(items):
            valorTributos = round(float(item.VALOR_TOTAL) * .1638, 2)
            self.totalTributos += valorTributos

            linhas.extend([
                "<tr>",
                "<td colspan=3>",
                "<table style=\"width: 100%; font-family: tahoma; font-size: 11pt;\">",
                "<tr>",
                "<td style=\"width: 30%;\"></td>",
                f"<td style=\"width: 15%;\">{int(item.QTDE)}</td>",
                f"<td style=\"width: 30%;\">{await self._getDescricaoitem(item.ID_PRODUTO)}</td>",
                f"<td style=\"width: 5%;\">{i + 1}</td>",
                "<td style=\"width: 20%;\"></td>",
                "</tr>",
                "</table>",
                "</td>",
                "</tr>"
            ])

            linhas.extend([
                "<tr>",
                "<td colspan=3>",
                "<table style=\"width: 100%; font-family: tahoma; font-size: 11pt;\">",
                "<tr>",
                "<td style=\"width: 30%;\"></td>",
                "<td style=\"width: 5%;\"></td>",
                f"<td style=\"width: 10%;\">{self.qBase.currency(float(item.PRECO_UNITARIO))}</td>",
                f"<td style=\"width: 10%;\">{self.qBase.currency(valorTributos)}</td>",
                f"<td style=\"width: 25%;\">{self.qBase.currency(float(item.VALOR_TOTAL))}</td>",
                "<td style=\"width: 20%;\"></td>",
                "</tr>",
                "</table>",
                "</td>",
                "</tr>"
            ])

            linhas.extend(
                self._linhaPontilhada()
                )
        
        return linhas

    async def _getDescricaoitem(self, ID_PRODUTO: int) -> str:
        p = ctx.mapProduto

        descricao = ctx.session.query(p).filter(
            p.ID_PRODUTO == ID_PRODUTO
        ).first().DESCRICAO_PRODUTO

        return descricao

    def trataChave(self, chave: str) -> str:
        retorno = ''

        for i, item in enumerate(chave):
            if i%4 == 0:
                retorno += ' '

            retorno += item

        return retorno 
    
    def _linhaPontilhada(self) -> List:
        linha = "." * 164

        return ["<tr>",
            f"<td colspan=3 style=\"width: 100%;\">{linha}</td>",
            "</tr>"
        ]

    async def _generatePDF(self, conteudo: List[str], numeroNF: str, qrContent: str) -> str:

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=4,
        )

        qr.add_data(qrContent)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")

        qrFile = os.path.join(
            os.getcwd(),
            self.config.PDF_FILES,
            'qrcode.png'
        )

        qrFile = os.path.normpath(qrFile)

        if os.path.exists(qrFile):
            os.remove(qrFile)

        img.save(qrFile)

        bytes = None

        with open(qrFile, 'rb') as fi:
            bytes = fi.read()

        base64_string = base64.b64encode(bytes)
        ba = base64_string.decode('utf-8')

        conteudo.extend([
            "<tr>",
            "<td colspan=3 style=\"width: 100%; text-align: left;\">&nbsp;</td>",
            "</tr>",
            "<tr>",
            f"<td colspan=3 style=\"width: 100%;\"><img src='data:image/jpg;base64, {ba}' /></td>",
            "</tr>",
            "</table>"
            ])

        htmlFile = os.path.join(
            os.getcwd(),
            self.config.PDF_FILES,
            f'NFCe_{numeroNF}.html'
        )

        htmlFile = os.path.normpath(htmlFile)

        if os.path.exists(htmlFile):
            os.remove(htmlFile)

        with open(htmlFile, 'w', encoding='utf-8') as fi:
            fi.write(''.join(
                conteudo
            ))

        return htmlFile
