from users.models import User


class UserRepository:
    def is_exists(self, user_id: int) -> bool:
        return User.objects.filter(pk=user_id).exists()
