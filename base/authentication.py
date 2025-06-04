from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, status
from werkzeug.security import check_password_hash, generate_password_hash

from cfg.config import Config
from models.Token import Token


class authentication:
    def __init__(self):
        self.config = Config()

    def generateNewToken(self) -> str:
        palavraPasse = "zionPDV"

        passe = generate_password_hash(palavraPasse)

        if not check_password_hash(passe, palavraPasse):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Credenciais inválidas para autenticação",
            )

        auth = authentication.encode_auth_token(passe)

        return Token(token=auth).__dict__

    @staticmethod
    def verify_Token_Is_Active(token: str):
        b1 = bytes(token, encoding="raw_unicode_escape")
        result = authentication.decode_auth_token(b1)

        if result == False:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Token inválido"
            )

    @staticmethod
    def encode_auth_token(user_id):
        try:
            payload = {
                "exp": datetime.now() + timedelta(days=2),
                "iat": datetime.now(),
                "sub": user_id,
            }

            return jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Falha na criação do token de autenticação",
            )

    @staticmethod
    def decode_auth_token(auth_token):
        try:
            payload = jwt.decode(auth_token, Config.SECRET_KEY, algorithms=["HS256"])

            return payload["sub"]

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Falha na autenticação de credenciais",
            )

        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token de autenticação inválido",
            )
