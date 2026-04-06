import jwt
import datetime
from pojo.Tokens import Tokens
from Exception.TokenExpiredException import TokenExpiryException
from Exception.InvalidTokenException import InvalidTokenException

# 秘钥（密钥用来加密和解密JWT）
SECRET_KEY = "test_secret_key"

def getUserId(accessToken) -> int:
    try:
        decodedAccessToken = jwt.decode(accessToken, SECRET_KEY, algorithms=["HS256"])
        return decodedAccessToken["userId"]
    except jwt.ExpiredSignatureError:
        raise TokenExpiryException(userMessage="token expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenException(userMessage="invalid token")
# 生成 Access Token 和 Refresh Token 的函数
def generateTokens(userId) -> Tokens:
    # Access Token 有效期： 15 分钟
    accessTokenExpiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    accessToken = jwt.encode({"userId": userId, "exp": accessTokenExpiry}, SECRET_KEY, algorithm="HS256")

    # Refresh Token 有效期： 7 天
    refreshTokenExpiry = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    refreshToken = jwt.encode({"userId": userId, "exp": refreshTokenExpiry}, SECRET_KEY, algorithm="HS256")

    return Tokens(accessToken=accessToken, refreshToken=refreshToken)

# 刷新 Access Token 的函数
def refreshAccessToken(refreshToken):
    try:
        # 解码 Refresh Token，验证是否有效
        decoded_refresh_token = jwt.decode(refreshToken, SECRET_KEY, algorithms=["HS256"])

        # 生成新的 Access Token
        userId = decoded_refresh_token["userId"]
        newAccessTokenExpiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
        newAccessToken = jwt.encode({"userId": userId, "exp": newAccessTokenExpiry}, SECRET_KEY, algorithm="HS256")

        return newAccessToken,userId
    except jwt.ExpiredSignatureError:
        raise TokenExpiryException(userMessage="token expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenException(userMessage="invalid token")
