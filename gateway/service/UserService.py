from Exception.DataBaseException import DataBaseException
from Exception.InvalidTokenException import InvalidTokenException
from Exception.PasswordIncorrectException import PasswordIncorrectException
from Exception.TokenExpiredException import TokenExpiryException
from gateway.dao.UserDaoInterface import UserDaoInterface
from gateway.dao.UserDaoOrm import UserDaoOrm
from gateway.orm.UserOrm import UserOrm
from pojo.User import TokenResponse,UserLoginRequest
from utils.JWTTokenTool import generateTokens,refreshAccessToken
from Exception.UserNotFoundException import UserNotFoundException
from gateway.Singleton import Singleton,singletonInit

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
            raise UserNotFoundException("No user")
        if user.hashedPassword != userLoginForm.hashedPassword:
            raise PasswordIncorrectException()
        return generateTokens(user.uid)

    # def login(self, userLoginForm: UserLoginForm):
    #     try:
    #         user: User = self.userDao.login(userLoginForm)
    #     except Exception as e:
    #         raise DataBaseException(str(e))
    #     if user:
    #         if user.hashedPassword == userLoginForm.hashedPassword:
    #             # 登陆成功
    #             # 生成token
    #             newToken: Tokens = generateTokens(user.userId)
    #             try:
    #                 # 删除旧token
    #                 self.userDao.deleteTokensByUserId(user.userId)
    #                 # 存储新token
    #                 self.userDao.insertTokens(user.userId, newToken.refreshToken)
    #             except Exception as e:
    #                 raise DataBaseException(str(e))
    #             return newToken
    #         raise PasswordIncorrectException()
    #     raise UserNotFoundException("No user ")
    #
    # def logout(self, userId: int):
    #     try:
    #         self.userDao.deleteTokensByUserId(userId)
    #     except Exception as e:
    #         raise DataBaseException(str(e))
    #
    #
    # def refresh(self, token: Tokens) -> Tokens:
    #     try:
    #         userId: int = self.userDao.checkRefreshToken(token.refreshToken)
    #     except Exception as e:
    #         raise DataBaseException(str(e))
    #
    #     # 这里的token是前端传来的refreshToken
    #     res = refreshAccessToken(token.refreshToken)
    #     #uid有效，但是过期了
    #     if userId is None and res[1] :
    #         raise TokenExpiryException()
    #     # 确保check出来的userid和refresh token里的一样
    #     if res[1] != userId:
    #         raise InvalidTokenError("The token does not match the user")
    #     token.accessToken = res[0]
    #     return token
    #
    #
    #





