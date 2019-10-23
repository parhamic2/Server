from django.db import models
from .message_handlers import Handler
from .texts import get_text


class Tournoment(models.Model):

    name = models.CharField(max_length=32)
    cost = models.PositiveIntegerField(default=0)
    background = models.PositiveIntegerField(default=0)
    # rewards here
    level_min = models.PositiveIntegerField(default=0)
    level_max = models.PositiveIntegerField(default=0)
    max_loses = models.PositiveIntegerField(default=3)

    max_wins = models.PositiveIntegerField(default=12)
    reward_coins = models.PositiveIntegerField(default=0)
    reward_copouns = models.PositiveIntegerField(default=0)

    def give_rewards(self, user):
        if user.user.is_bot:
            return True
        reward_coins = int(self.reward_coins*(user.wins/self.max_wins))
        reward_copouns = int(self.reward_copouns*(user.wins/self.max_wins))
        user.user.coins += reward_coins
        user.user.copouns += reward_copouns
        context = {}
        context['wins'] = user.wins
        context['finished'] = user.wins >= self.max_wins
        context['reward_coins'] = reward_coins
        context['reward_copouns'] = reward_copouns
        user.user.send_message('tournoment_result', context)
        user.user.save()
        user.delete()
        return False

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        from .models import User
        if self.users.count() == 0:
            bots = User.objects.filter(is_bot=True)
            for bot in bots:
                TournomentUser.objects.create(tournoment=self, user=bot)


class TournomentUser(models.Model):
    from .models import User

    tournoment = models.ForeignKey(
        Tournoment, related_name="users", on_delete=models.CASCADE
    )
    user = models.ForeignKey(User, related_name="tournoments", on_delete=models.CASCADE)
    wins = models.PositiveIntegerField(default=0)
    loses = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        commit = True
        if self.wins >= self.tournoment.max_wins or self.loses >= self.tournoment.max_loses:
            commit = self.tournoment.give_rewards(self)

        if commit:
            super().save(*args, **kwargs)


class TournomentParticipateHandler(Handler):
    def handle(self):
        params = self.get_params()
        tournoment = Tournoment.objects.get(pk=params["pk"])
        context = {}
        context["succeed"] = False
        level, _ = self.request.user.get_level()
        if tournoment.users.filter(user=self.request.user).count() > 0:
            context["error"] = get_text("tournoment_already_participated")
        elif level < tournoment.level_min or level > tournoment.level_max:
            context["error"] = get_text("tournoment_level_range")
        elif self.request.user.coins < tournoment.cost:
            context["error"] = get_text("not_enough_coins")
        else:
            TournomentUser.objects.create(tournoment=tournoment, user=self.request.user)
            self.request.user.coins -= tournoment.cost
            self.request.user.save()
            context["succeed"] = True

        return self.response("tournoment_participate", context)


TOURNOMENT_MESSAGE_HANDLERS = {"tournoment_participate": TournomentParticipateHandler}
