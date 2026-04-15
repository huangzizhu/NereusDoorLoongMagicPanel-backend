from Exception.DataBaseException import DataBaseException
from Exception.InvalidTokenException import InvalidTokenException
from Exception.PasswordIncorrectException import PasswordIncorrectException
from Exception.RefreshTokenExpiryException import RefreshTokenExpiryException
from gateway.dao.UserDaoInterface import UserDaoInterface
from gateway.dao.UserDaoOrm import UserDaoOrm
from gateway.orm.TokenOrm import TokenOrm
from gateway.orm.UserOrm import UserOrm
from pojo.User import TokenResponse, UserLoginRequest, TokenRefreshRequest
from utils.JWTTokenTool import generateTokens,refreshAccessToken
from Exception.UserNotFoundException import UserNotFoundException
from gateway.Singleton import Singleton,singletonInit
import datetime

class UserService(Singleton):

    @singletonInit
    def __init__(self):
        self.userDao: UserDaoInterface = UserDaoOrm()

    def login(self, userLoginForm: UserLoginRequest) -> TokenResponse:
        try:
            user: UserOrm | None = self.userDao.getUserByAccount(userLoginForm.account)
        except Exception as e:
            raise DataBaseException(str(e))

        if user is None:
            raise UserNotFoundException(f"No user {userLoginForm.account}")
        if user.hashedPassword != userLoginForm.hashedPassword:
            raise PasswordIncorrectException()
        token: TokenResponse = generateTokens(user.userId)
        tokenOrm: TokenOrm = TokenOrm(userId=user.userId,
                                      refreshToken=token.refreshToken,
                                      expireIn=datetime.datetime.now()+datetime.timedelta(days=7),# 7天之后过期
                                      status=1)
        try:
            self.userDao.insertTokens(tokenOrm)
        except Exception as e:
            raise DataBaseException(innerMessage="插入用户token失败", userMessage="服务器错误，请稍后再试",cause=e)
        return token

    def logout(self, token: TokenRefreshRequest):
        try:
            countRow: int = self.userDao.deleteTokensByRefreshToken(token.refreshToken)
        except Exception as e:
            raise DataBaseException(innerMessage="删除用户token失败", userMessage="服务器错误，请稍后再试", cause=e)
        if countRow == 0:
            raise InvalidTokenException(userMessage="token无效")

    def refreshToken(self, tokenRequest: TokenRefreshRequest) -> TokenResponse:
        # 检查相关的用户
        try:
            userOrm: UserOrm | None= self.userDao.getUserByRefreshToken(tokenRequest.refreshToken)
            if userOrm is None:
                raise InvalidTokenException(userMessage="token无效")
        except InvalidTokenException:
            raise
        except Exception as e:
            raise DataBaseException(innerMessage="查询用户失败", userMessage="服务器错误，请稍后再试", cause=e)

        try:
            newAccessToken = refreshAccessToken(tokenRequest.refreshToken)
        except RefreshTokenExpiryException as e:
            # 过期，到数据库注销
            try:
                countRow: int = self.userDao.deactivateTokensByRefreshToken(tokenRequest.refreshToken)
            except Exception as e:
                raise DataBaseException(innerMessage="注销过期token失败", userMessage="服务器错误，请稍后再试", cause=e)
            if countRow == 0:
                raise InvalidTokenException(userMessage="token无效")
            raise e
        except InvalidTokenException as e:
            raise e
        # 生成新的
        return TokenResponse(accessToken=newAccessToken[0], refreshToken=tokenRequest.refreshToken)




