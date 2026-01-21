from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

class Login(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        username: có thể là username hoặc email người dùng nhập
        password: mật khẩu
        """

        try:
            # Tìm user theo username hoặc email
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
        except User.DoesNotExist:
            return None

        # Kiểm tra mật khẩu
        if user.check_password(password):
            return user

        return None