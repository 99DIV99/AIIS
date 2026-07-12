from django.db import close_old_connections
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        close_old_connections()
        
        # Get the token from query string
        query_string = parse_qs(scope["query_string"].decode("utf8"))
        token = query_string.get("token")

        if not token:
            scope["user"] = AnonymousUser()
        else:
            try:
                # Validate the token
                UntypedToken(token[0])
                decoded_data = jwt_decode(token[0], settings.SECRET_KEY, algorithms=["HS256"])
                user_id = decoded_data["user_id"]
                scope["user"] = await get_user(user_id)
            except (InvalidToken, TokenError, KeyError):
                scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
