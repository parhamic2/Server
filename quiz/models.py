from django.db import models
from django.contrib.auth.models import AbstractUser
import json
import requests
import random
from constance import config
import socket
from django.utils import timezone


def LEVELS_XPS():
    return list(map(int, config.LEVELS_XPS.split(",")))


class User(AbstractUser):
    export_fields = ["username", "xp", "coins", "trophy", "copouns", "parent", "is_bot"]

    marked_for_notification = models.BooleanField(default=False)
    store = models.CharField(max_length=128, blank=True, null=True)
    is_bot = models.BooleanField(default=False)
    in_queue = models.BooleanField(default=False)
    queued_time = models.DateTimeField(blank=True, null=True)
    ip_address = models.CharField(blank=True, null=True, max_length=16)
    queued_tournoment = models.ForeignKey(
        "Tournoment",
        blank=True,
        null=True,
        related_name="queues",
        on_delete=models.SET_NULL,
    )
    last_alive_message = models.DateTimeField(blank=True, null=True)
    last_chosen_words = models.TextField(blank=True, null=True)
    push_notification_id = models.CharField(
        max_length=48, default="", null=True, blank=True
    )
    device_id = models.CharField(max_length=45)

    phone = models.CharField(max_length=16, default="", null=True, blank=True)
    parent = models.ForeignKey(
        "quiz.User",
        null=True,
        blank=True,
        related_name="childs",
        on_delete=models.SET_NULL,
    )
    last_daily_reward = models.DateTimeField(blank=True, null=True)
    daily_reward = models.PositiveIntegerField(default=0)
    verify_code = models.CharField(max_length=16, blank=True, null=True)
    logged_in = models.BooleanField(default=False)
    level_reached = models.PositiveIntegerField(default=10001)
    collected_reach_reward = models.PositiveIntegerField(default=1001)
    hidden_words = models.PositiveIntegerField(default=0)
    boost = models.FloatField(default=1)
    boost_expire = models.DateTimeField(blank=True, null=True)
    reroll = models.BooleanField(default=False)
    last_client_version = models.CharField(max_length=10, blank=True, null=True)
    spent = models.FloatField(default=0)

    xp = models.PositiveIntegerField(default=0)
    coins = models.PositiveIntegerField(default=400)
    trophy = models.PositiveIntegerField(default=0)
    trophy_week = models.PositiveIntegerField(default=0)
    trophy_month = models.PositiveIntegerField(default=0)
    trophy_year = models.PositiveIntegerField(default=0)

    copouns = models.PositiveIntegerField(default=0)

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        self.pre_xp = self.xp
        self.pre_coins = self.coins
        self.pre_trophy = self.trophy
        self.pre_boost = self.boost

    def save(self, update_message=True, *args, **kwargs):
        from .message_handlers import UserProfileHandler

        super(AbstractUser, self).save(*args, **kwargs)
        if update_message and (
            self.pre_xp != self.xp
            or self.pre_coins != self.coins
            or self.pre_trophy != self.trophy
            or self.pre_boost != self.boost
        ):
            self.send_message(
                "user_profile", UserProfileHandler.get_user_profile(self.username)
            )

    def check_boost_expire(self):
        from .utils import get_time

        if self.boost_expire and self.boost_expire < get_time():
            self.boost_expire = None
            self.boost = 1
            self.save()
            self.send_message("boost_expired", None)

    def give_xp(self, xp):
        self.check_boost_expire()
        prev_level = self.get_level()[0]
        self.xp += xp * self.boost
        cur_level = self.get_level()[0]

        if cur_level > prev_level:
            for lottery in Lottery.objects.all():
                if cur_level >= lottery.min_level and prev_level < lottery.min_level:
                    self.send_message("lottery_available", {"name": lottery.name})
                    break

    def can_buy(self, coins, commit=False):
        if self.coins >= coins:
            if commit:
                self.coins -= coins
            return True
        return False

    def get_level(self):
        level = 0
        xp = self.xp
        while xp >= LEVELS_XPS()[level]:
            xp -= LEVELS_XPS()[level]
            level += 1
        return level, xp

    def calculate_trophy(self, won, opponent, commit=True):
        if self.is_bot:
            return
        if won:
            self.trophy += 30
            self.trophy_week += 30
            self.trophy_month += 30
            self.trophy_year += 30
        else:
            self.trophy -= 30
            self.trophy_week -= 30
            self.trophy_month -= 30
            self.trophy_year -= 30

        self.trophy = max(0, self.trophy)
        self.trophy_week = max(0, self.trophy_week)
        self.trophy_month = max(0, self.trophy_month)
        self.trophy_year = max(0, self.trophy_year)
        if commit:
            self.save()

    def send_message(self, cmd, params=None, perminent=False):
        if self.is_bot:
            return

        from .utils import serialize

        context = {}
        context["cmd"] = cmd
        if params:
            params = serialize(params)
            context.update(params)
        data = json.dumps(context, ensure_ascii=False)
        Message.objects.create(user=self, data=data, perminent=perminent)

        if self.ip_address is None:
            return
        # print ('send socket msg')
        # s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # s.connect((self.ip_address, 8301))
        # s.send(bytes(data.encode('utf-8')))
        # s.close()

    def send_mail(self, title, text):
        params = {}
        params["title"] = title
        params["text"] = text
        self.send_message("mail", params, perminent=True)

    def send_notification(self, title, content, image=None):
        if self.is_bot or self.push_notification_id == "":
            return
        data = {
            "app_ids": ["com.dreamwings.jaanjibi",],
            "data": {
                "title": title,
                "content": content,
                "sound_url": "http://5.253.24.104/static/notif2.mp3",
            },
            "filters": {"pushe_id": [self.push_notification_id]},
        }
        if image is not None:
            data["data"]['icon'] = 'http://5.253.24.104/{}'.format(image)
        req = requests.post(
            "https://api.pushe.co/v2/messaging/notifications/",
            json=data,
            headers={
                "Authorization": "Token 3d258a0f5e6d5d3eb6cdc0a0f028493cf97ce750",
                "Content-Type": "application/json",
            },
        )

        # One Signal
        # header = {
        #     "Content-Type": "application/json; charset=utf-8",
        #     "Authorization": "Basic ZWI5ODBiZDctNWIyMS00ZDM3LTk1MTctMDk2YjVhYTU5MWJk",
        # }

        # payload = {
        #     "app_id": "6cc33c87-b167-4863-a6b9-2ed884872e79",
        #     "contents": {"en": content},
        #     "include_player_ids": [self.push_notification_id],
        # }

        # req = requests.post(
        #     "https://onesignal.com/api/v1/notifications",
        #     headers=header,
        #     data=json.dumps(payload),
        # )
        # print (req.text)

        # url = "https://api.pushe.co/v2/messaging/notifications/"
        # payload = {
        #     "app_ids": ["com.dreamwings.john"],
        #     # pid_0586-357c-4d
        #     "filters": {"pushe_id": [self.push_notification_id]},
        #     "data": {
        #         "title": title,
        #         "content": content,
        #         "action": {"action_type": "A", "url": ""},
        #     },
        # }
        # headers = {
        #     "authorization": "Token d0fecba9514ccb428c34ed73a0b6d43e35d3c98e",
        #     "content-type": "application/json",
        # }
        # try:
        #     requests.post(url, data=json.dumps(payload), headers=headers)
        # except:
        #     pass


class CoinCode(models.Model):
    coin_amount = models.PositiveIntegerField(default=0)
    code = models.CharField(max_length=8, unique=True, blank=True)
    number = models.PositiveIntegerField(default=0)
    created = models.DateTimeField(blank=True, null=True)
    users = models.ManyToManyField(User, blank=True)

    def save(self, *args, **kwargs):
        from .utils import get_time

        chrs = [chr(i) for i in range(ord("1"), ord("9") + 1)]
        chrs.extend([chr(i) for i in range(ord("a"), ord("z") + 1)])
        chrs.extend([chr(i) for i in range(ord("A"), ord("Z") + 1)])
        time = get_time()
        for j in range(self.number):
            code = ""
            while code == "" or CoinCode.objects.filter(code=code).count() > 0:
                code = ""
                for i in range(8):
                    code += random.choice(chrs)
            CoinCode.objects.create(
                coin_amount=self.coin_amount, code=code, created=time
            )
        if self.number > 0:
            return
        super(CoinCode, self).save(*args, **kwargs)


class Ticket(models.Model):
    CATEGORIES = (("BR", "Bug Report"), ("SA", "Sell Account"), ("FB", "Feedback"))
    STATES = (("OP", "Open"), ("CL", "Closed"))
    title = models.CharField(max_length=32)
    category = models.CharField(max_length=32)
    state = models.CharField(choices=STATES, max_length=4)
    user = models.ForeignKey(User, related_name="tickets", on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class TicketMessage(models.Model):
    ticket = models.ForeignKey(
        Ticket, related_name="messages", on_delete=models.CASCADE
    )
    is_admin = models.BooleanField(default=False)
    message = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-date",)

    def __str__(self):
        return self.ticket.title


class Match(models.Model):
    users = models.ManyToManyField(User, related_name="matches")
    user_created = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="matches_created",
        on_delete=models.SET_NULL,
    )
    winner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="matches_won",
        on_delete=models.SET_NULL,
    )
    STATES = (("PENDING", "Pending"), ("STARTED", "Started"), ("FINISHED", "Finished"))
    state = models.CharField(max_length=8, choices=STATES, default="STARTED")
    created = models.DateTimeField(auto_now_add=True)
    turned_base = models.BooleanField(default=False)
    tournoment = models.ForeignKey(
        "Tournoment",
        blank=True,
        null=True,
        related_name="matches",
        on_delete=models.SET_NULL,
    )

    def played_all_games(self, user):
        return self.games.filter(user=user).exclude(state="FINISHED").count() == 0

    def other_user(self, user):
        tmp = self.users.exclude(id=user.id)
        return tmp.first()

    def get_scores_dict(self):
        scores = {}
        for match_game in self.games.all():
            if match_game.user.pk not in scores:
                scores[match_game.user.pk] = 0
            scores[match_game.user.pk] += match_game.score
        return scores

    def give_rewards(self):
        if self.state == "FINISHED":
            return
        scores = self.get_scores_dict()
        # choose the winner
        winner = None
        loser = None
        draw = False
        m = -1
        for key in scores:
            if scores[key] > m:
                m = scores[key]
                winner = key
            elif scores[key] == m:
                draw = True
            else:
                loser = key
            if loser is None:
                loser = key

        user = User.objects.get(pk=winner)
        loser = User.objects.get(pk=loser)
        if self.tournoment is None:
            level = Level.objects.get(level_id=0)
            if not draw:
                user.give_xp(level.score)
                user.coins += level.coin
                user.calculate_trophy(True, loser, False)
                loser.calculate_trophy(False, user)
            else:
                user.give_xp(level.score // 2)
                user.coins += level.coin // 2
                loser.give_xp(level.score // 2)
                loser.coins += level.coin // 2
                loser.save()
            user.save()
        else:
            if not draw:
                tournoment_user_winner = self.tournoment.users.filter(user=user).first()
                tournoment_user_loser = self.tournoment.users.filter(user=loser).first()
                tournoment_user_winner.wins += 1
                tournoment_user_winner.save()
                tournoment_user_loser.loses += 1
                tournoment_user_loser.save()
        if not draw:
            self.winner = user
        self.state = "FINISHED"
        self.save()

        self.games.update(state="FINISHED")


class MatchEmoji(models.Model):
    match = models.ForeignKey(Match, related_name="emojis", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="emojis", on_delete=models.CASCADE)
    target = models.ForeignKey(
        User, related_name="emojis_target", on_delete=models.CASCADE
    )
    emoji = models.CharField(max_length=4)


class MatchGame(models.Model):
    match = models.ForeignKey(Match, related_name="games", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="games", on_delete=models.CASCADE)
    row = models.PositiveIntegerField(default=0)
    STATES = (
        ("DEACTIVE", "Deactive"),
        ("WAITING", "Waiting"),
        ("PLAYING", "Playing"),
        ("FINISHED", "Finished"),
    )
    state = models.CharField(max_length=8, choices=STATES, default="DEACTIVE")
    score = models.PositiveIntegerField(default=0)
    start_time = models.DateTimeField(blank=True, null=True)

    generated = models.BooleanField(default=False)
    questions = models.CharField(max_length=128, blank=True, null=True)
    letters = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        unique_together = ("match", "user", "row")
        ordering = ("row",)


class Message(models.Model):
    user = models.ForeignKey(User, related_name="messages", on_delete=models.CASCADE)
    data = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    perminent = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)

    class Meta:
        ordering = ("created",)


class Word(models.Model):
    word = models.CharField(max_length=16)
    simple_word = models.CharField(max_length=16)

    def __str__(self):
        return self.word


class RewardPackage(models.Model):
    kind = models.CharField(max_length=16, blank=True, null=True)
    coins = models.PositiveIntegerField(default=0)
    copouns = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)


class Level(models.Model):
    SEASONS = (
        ("1", "Season 1"),
        ("2", "Season 2"),
        ("3", "Season 3"),
        ("4", "Season 4"),
    )
    season = models.CharField(choices=SEASONS, max_length=1)
    part = models.PositiveIntegerField(default=0)
    trophy = models.PositiveIntegerField(default=0)
    level_id = models.PositiveIntegerField(unique=True, blank=True)
    time = models.PositiveIntegerField(default=30)
    reach_reward = models.PositiveIntegerField(default=0)
    reach_reward_package = models.ForeignKey(
        RewardPackage,
        related_name="levels",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    extra_letters = models.PositiveIntegerField(default=0)

    score = models.PositiveIntegerField(default=0)
    coin = models.PositiveIntegerField(default=0)

    num_questions_length1 = models.PositiveIntegerField(default=0)
    num_questions_length2 = models.PositiveIntegerField(default=0)
    num_questions_length3 = models.PositiveIntegerField(default=0)
    num_questions_length4 = models.PositiveIntegerField(default=0)
    num_questions_length5 = models.PositiveIntegerField(default=0)
    num_questions_length6 = models.PositiveIntegerField(default=0)
    num_questions_length7 = models.PositiveIntegerField(default=0)
    num_questions_length8 = models.PositiveIntegerField(default=0)

    def get_total_words(self):
        return sum(
            [getattr(self, "num_questions_length{}".format(i)) for i in range(1, 9)]
        )

    def save(self, *args, **kwargs):
        levels = Level.objects.all()
        if self.pk:
            levels = levels.exclude(pk=self.pk)
        if self.level_id is None:
            for i in range(1, 999):
                self.level_id = int(self.season) * 10000 + self.part * 1000 + i
                if levels.filter(level_id=self.level_id).count() == 0:
                    break
        super(Level, self).save(*args, **kwargs)

    class Meta:
        ordering = ("level_id",)


class Lottery(models.Model):
    name = models.CharField(max_length=50)
    days = models.IntegerField(default=1)
    automatic = models.BooleanField(default=False)
    add_all = models.BooleanField(default=False)
    start_time = models.TimeField()
    min_level = models.IntegerField(default=0)
    max_level = models.IntegerField(default=0)
    last_active_time = models.DateTimeField(auto_now_add=True)

    STATES = (("STARTED", "Started"), ("OPEN", "Open"), ("CLOSED", "Closed"))
    number = models.IntegerField(default=0)
    state = models.CharField(max_length=7, choices=STATES, default="STARTED")
    give_rewards = models.BooleanField(default=False)
    coin_reward = models.IntegerField(default=0)
    copoun_reward = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        from .utils import get_time

        online_users = list(
            self.users.filter(
                user__last_alive_message__gt=get_time() - timezone.timedelta(seconds=5)
            )
        )
        if self.state == "STARTED":
            self.users.all().delete()
            # add users if add_all is on
            if self.add_all:
                all_users = User.objects.all()
                for user in all_users:
                    level, _ = user.get_level()
                    if level >= self.min_level and level <= self.max_level:
                        # TODO
                        LotteryUser.objects.create(user=user, lottery=self, copouns=1)

            self.last_active_time = get_time()
            self.state = "OPEN"
        elif self.state == "CLOSED":
            all_users = list(self.users.all().values_list("pk", "copouns"))
            counted_users = []
            for u in all_users:
                for i in range(u[1]):
                    counted_users.append(u[0])
            selected_users = []
            while len(selected_users) < self.number and len(counted_users) > 0:
                u = random.choice(counted_users)
                if u not in selected_users:
                    selected_users.append(u)
            for u in self.users.all().values_list("pk", flat=True):
                if u not in selected_users:
                    LotteryUser.objects.get(pk=u).delete()

            from .message_handlers import GameInfoHandler

            for user in online_users:
                user.user.send_message(
                    "lotteries", {"lotteries": GameInfoHandler.get_lotteries(user.user)}
                )

        if self.give_rewards:
            for user in self.users.all():
                user.user.coins += self.coin_reward
                user.user.copouns += self.copoun_reward
                from .texts import get_text

                user.user.send_mail(
                    get_text("lottery_reward_title"),
                    get_text("lottery_reward").format(self.name, self.coin_reward),
                )
                user.user.save()
                log = Log()
                log.user = user.user
                log.lottery = self
                log.category = "Lottery Win"
                log.description = "User {} won {} coins and {} copouns from lottery {}".format(
                    user.user, self.coin_reward, self.copoun_reward, self
                )
                log.save()

                from .message_handlers import GameInfoHandler

                cache_user = user.user
                user.delete()
                user.user.send_message(
                    "game_info_live",
                    {"lotteries": GameInfoHandler.get_lotteries(cache_user)},
                )
            self.give_rewards = False
            from .message_handlers import GameInfoHandler

            for user in online_users:
                user.user.send_message(
                    "lotteries", {"lotteries": GameInfoHandler.get_lotteries(user.user)}
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class LotteryUser(models.Model):
    lottery = models.ForeignKey(Lottery, related_name="users", on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, related_name="lottery_users", on_delete=models.CASCADE
    )
    copouns = models.IntegerField(default=1)


class ShopItem(models.Model):
    active = models.BooleanField(default=True)
    name = models.CharField(max_length=32)
    CATEGORIES = (
        ("COINS", "Coins"),
        ("BOOST", "Boost"),
        ("THEME", "Theme"),
        ("PACKAGE", "Package"),
    )
    category = models.CharField(max_length=8, choices=CATEGORIES, default="COINS")
    icon = models.CharField(max_length=12, blank=True, null=True)
    price = models.FloatField(default=0)
    price_coins = models.PositiveIntegerField(default=0)
    off = models.PositiveIntegerField(default=0)
    coins = models.PositiveIntegerField(default=0)
    copouns = models.PositiveIntegerField(default=0)
    boost = models.FloatField(default=0)
    boost_time = models.FloatField(default=0)

    def __str__(self):
        return self.name


class GlobalReward(models.Model):
    coins = models.PositiveIntegerField(default=0)
    copouns = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=128)
    description = models.TextField()

    def save(self):
        # don't save ^^
        for user in User.objects.all():
            user.coins += self.coins
            user.copouns += self.copouns
            user.save()
            user.send_mail(self.title, self.description)


class SellAccount(models.Model):
    account = models.ForeignKey(User, related_name="sells", on_delete=models.CASCADE)
    price = models.PositiveIntegerField(default=0)
    text = models.TextField(blank=True, null=True)
    approved = models.BooleanField(default=False)


class Log(models.Model):
    user = models.ForeignKey(
        User, null=True, blank=True, related_name="logs", on_delete=models.SET_NULL
    )
    lottery = models.ForeignKey(
        Lottery, null=True, blank=True, related_name="logs", on_delete=models.SET_NULL
    )
    category = models.CharField(max_length=16, verbose_name="Type")
    created = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.description + str(self.created)


class Badge(models.Model):
    name = models.CharField(max_length=32)
    players = models.ManyToManyField(User, blank=True, related_name="badges")

    def __str__(self):
        return self.name


class LevelTrack(models.Model):
    user = models.ForeignKey(User, related_name="tracks", on_delete=models.CASCADE)
    level = models.ForeignKey(Level, related_name="tracks", on_delete=models.CASCADE)
    start_coin = models.PositiveIntegerField(default=0)
    finish_coin = models.PositiveIntegerField(default=0)
    time = models.FloatField(default=0)
    help_used = models.PositiveSmallIntegerField(default=0)
    stars = models.PositiveSmallIntegerField(default=0)


class ZarinPayment(models.Model):
    authority = models.CharField(max_length=64)
    amount = models.PositiveIntegerField(default=0)
    user = models.ForeignKey(User, related_name="payments", on_delete=models.CASCADE)
    item = models.CharField(max_length=32, blank=True, null=True)
    is_done = models.BooleanField(default=False)


class InviteCode(models.Model):
    code = models.CharField(max_length=16)
    user = models.ForeignKey(
        User, related_name="invite_codes", on_delete=models.CASCADE
    )
    perminent = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        from .views import generate_password

        if not self.code:
            self.code = generate_password(5)
            while InviteCode.objects.filter(code=self.code).count() > 0:
                self.code = generate_password(5)
        super().save(*args, **kwargs)


class SendNotification(models.Model):
    title = models.CharField(blank=True, max_length=64)
    message = models.TextField(blank=True)
    in_game_notification = models.BooleanField(default=False)
    image = models.ImageField(upload_to="notifications", blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for user in User.objects.filter(marked_for_notification=True):
            if self.in_game_notification:
                user.send_mail(self.title, self.message)
            else:
                from .tasks import send_notification
                image_url = None
                if self.image:
                    image_url = self.image.url
                send_notification.delay(user.pk, self.title, self.message, self.image.url)
                # user.send_notification(self.title, self.message)

    class Meta:
        verbose_name = "Send group notification"
        verbose_name_plural = "Send group notification"


class PlayRecord(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    player = models.ForeignKey(User, related_name="records", on_delete=models.CASCADE)
    played_time = models.FloatField(default=0)
