from django.apps import AppConfig


class QuizConfig(AppConfig):
    name = "quiz"

    def ready(self):
        from .tournoment import Tournoment

        return super().ready()
