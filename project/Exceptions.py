

class EntityNotFoundError(Exception):
    pass


class RevokedTokenError(Exception):
    pass


class TokenNotFoundError(Exception):
    pass


class AuthHederNotFound(Exception):
    pass


class ExpiredSignatureError(Exception):
    pass
