from .models import (
    User,
    Message,
    Level,
    Lottery,
    ShopItem,
    LotteryUser,
    Word,
    Match,
    MatchGame,
    CoinCode,
    SellAccount,
    Log,
    MatchEmoji,
    LevelTrack,
    InviteCode
)
from rest_framework.response import Response
from django.conf import settings
import json
import random
from django.db.models.functions import Length
from django.utils import timezone
from .utils import serialize, create_match, get_time, send_email
from .texts import TEXTS, get_text
from django.db.models import Q
from rest_framework.authtoken.models import Token
from constance import config
import requests

def send_sms(phone, text):
    req = requests.post('https://rest.payamak-panel.com/api/SendSMS/SendSMS', data={
        'username': '09381878227',
        'password': 'Kh^123456',
        'from': '50001060669741',
        'to': phone,
        'text': text
    })
    print (req.text)

def get_country(request):
    try:
        req = requests.get(
            "https://get.geojs.io/v1/ip/country/{}".format(
                get_client_ip(request)
            )
        )
        return req.text.strip()
    except:
        return "Ir"

def get_match_total_score():
    return Level.objects.get(level_id=0).get_total_words()


class Handler:
    def __init__(self, request):
        self.request = request

    def to_json(self, cmd, params=None):
        context = {}
        context["cmd"] = cmd
        if params:
            params = serialize(params)
            context.update(params)
        return context

    def response(self, cmd, params=None):
        return Response(self.to_json(cmd, params))

    def get_params(self):
        params = None
        if "params" in self.request.data:
            params = json.loads(self.request.data["params"])
        return params

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class GameInfoHandler(Handler):
    def want(self, q):
        return self.question == q


    def get_lotteries(user):
        ls = []
        lotteries = Lottery.objects.all()
        for lottery in lotteries:
            l = {}
            l["name"] = lottery.name
            l["pk"] = lottery.pk
            l["participated"] = (
                lottery.users.filter(user=user).count() > 0
            )
            l["min_level"] = lottery.min_level
            l["max_level"] = lottery.max_level
            ls.append(l)
        return ls
    def handle(self):
        params = self.get_params()
        self.question = params["question"]
        client_version = params.get("version", None)
        context = {}
        context["question"] = self.question
        context["level_reached"] = self.request.user.level_reached
        if self.want("all"):
            self.request.user.messages.all().update(hidden=False)
            if config.ESTIMATED_TIME > 0:
                context['estimated_time'] = config.ESTIMATED_TIME
            else:
                context['country'] = 'ir'
                context['has_parent'] = self.request.user.parent is not None
                context["ad_coins"] = config.AD_COINS
                context["email_verify_coins"] = config.EMAIL_VERIFY_REWARD
                context["invite_friend_coins"] = config.INVITE_CODE_PARENT_REWARD
                context['invite_code_child_reward'] = config.INVITE_CODE_CHILD_REWARD
                context["prices"] = PurchaseHandler.get_prices()
                context['update_reward'] = config.UPDATE_REWARD_COINS
                if config.MOTD_TITLE != '':
                    context["motd"] = config.MOTD_TITLE + "&" + config.MOTD + "&" + config.MOTD_PERCENT
                # reset in-progress matches
                idle_games = self.request.user.games.filter(state="PLAYING").update(state="WAITING")
                # for game in idle_games:
                #     LevelCompleteHandler.complete_game(game, 0)
                context["email"] = (
                    self.request.user.email is None or self.request.user.email == ""
                ) and (self.request.user.phone is None or self.request.user.phone == "")
                context["lotteries"] = GameInfoHandler.get_lotteries(self.request.user)
                context["shop_items"] = []
                shop_items = ShopItem.objects.filter(active=True).order_by('price', 'price_coins')
                for shop_item in shop_items:
                    si = {}
                    si["name"] = shop_item.name
                    si["coins"] = shop_item.coins
                    si["copouns"] = shop_item.copouns
                    si["boost"] = shop_item.boost
                    si["boost_time"] = int(shop_item.boost_time)
                    si["price"] = shop_item.price
                    si["price_coins"] = shop_item.price_coins
                    si["icon"] = shop_item.icon
                    si["off"] = shop_item.off
                    si["pk"] = shop_item.pk
                    si["category"] = shop_item.category
                    context["shop_items"].append(si)
                
                for i in range(1, 11):
                    context['video_{}'.format(i)] = getattr(config, 'VIDEO_LINK_{}'.format(i))

                context["version"] = config.VERSION
                if (
                    self.request.user.last_client_version
                    and self.request.user.last_client_version != client_version
                ):
                    p1 = self.request.user.last_client_version.split(".")
                    p2 = client_version.split(".")
                    if p2[1] > p1[1] or p2[0] > p1[0]:
                        self.request.user.coins += config.UPDATE_REWARD_COINS
                        self.request.user.copouns += config.UPDATE_REWARD_COPOUNS
                        self.request.user.boost = max(
                            config.UPDATE_REWARD_BOOST, self.request.user.boost
                        )
                        # self.request.user.boost_expire = max(
                        #     get_time()
                        #     + timezone.timedelta(hours=config.UPDATE_REWARD_BOOST_TIME),
                        #     self.request.user.boost_expire or get_time(),
                        # )
                        context["updated"] = True
                self.request.user.last_client_version = client_version
                self.request.user.ip_address = get_client_ip(self.request)
                self.request.user.push_notification_id = params["push_notification_id"]
                self.request.user.device_id = params["device_id"]
                self.request.user.store = params.get("store", "-")
                self.request.user.save()

                if context["email"]:
                    from .tasks import send_notification
                    send_notification.delay(self.request.user.id, TEXTS["complete_profile_title"], TEXTS["complete_profile"])

                sell_accounts = SellAccount.objects.filter(approved=True)
                context["sell_accounts"] = []
                for sell_account in sell_accounts:
                    sa = {}
                    sa["name"] = sell_account.account.username
                    sa["level"], sa["xp"] = sell_account.account.get_level()
                    sa["copouns"] = sell_account.account.copouns
                    sa["price"] = sell_account.price
                    context["sell_accounts"].append(sa)

        if self.want("levels"):
            context['wanted_part'] = params['wanted_part']
            context["seasons"] = {}
            for i in range(1, 5):
                context["seasons"][str(i)] = {}
                season_levels = Level.objects.filter(season=i).exclude(level_id=0)
                print(season_levels, flush=True)
                for level in season_levels:
                    if level.part != params['wanted_part']:
                        continue
                    if str(level.part) not in context["seasons"][str(i)]:
                        context["seasons"][str(i)][str(level.part)] = []
                    stars = 0
                    try:
                        stars = LevelTrack.objects.get(user=request.user, level=level).stars
                    except:
                        pass
                    context["seasons"][str(i)][str(level.part)].append(
                        {
                            "id": level.level_id,
                            "h": level.reach_reward > 0,
                            "s": stars
                            "c": self.request.user.collected_reach_reward <= level.level_id,
                        }
                    )
        from .tournoment import Tournoment

        if self.want("tournoments"):
            context["tournoments"] = []
            tournoments = Tournoment.objects.all()
            for tournoment in tournoments:
                t = {}
                t["background"] = tournoment.background
                t["pk"] = tournoment.pk
                t["name"] = tournoment.name
                t["cost"] = tournoment.cost
                t["reward_coins"] = tournoment.reward_coins
                t["reward_copouns"] = tournoment.reward_copouns
                t["level_min"] = tournoment.level_min
                t["level_max"] = tournoment.level_max
                t["max_wins"] = tournoment.max_wins
                t["max_loses"] = tournoment.max_loses
                t["participated"] = (
                    tournoment.users.filter(user=self.request.user).count() > 0
                )
                if t["participated"]:
                    t_user = tournoment.users.filter(user=self.request.user).first()
                    t["wins"] = t_user.wins
                    t["loses"] = t_user.loses
                    t["_reward_coins"] = int(tournoment.reward_coins*(t_user.wins/tournoment.max_wins))
                    t["_reward_copouns"] = int(tournoment.reward_copouns*(t_user.wins/tournoment.max_wins))
                context["tournoments"].append(t)
        return self.response("game_info", context)

from django.contrib.auth.validators import UnicodeUsernameValidator
class SetPlayerInfoHandler(Handler):
    def validate(params):
        if "username" not in params:
            return TEXTS["invalid_input"], None
        u = params["username"]
        if len(u) < 2:
            return TEXTS["username_short"], None
        if User.objects.filter(username=u).count() > 0:
            suggestion = u
            while User.objects.filter(username=suggestion).count() > 0:
                suggestion = "{}{}".format(u, random.randint(1000, 9999))
            return TEXTS["user_exist"], suggestion
        try:
            UnicodeUsernameValidator()(u)
        except:
            return TEXTS["invalid_input"], None
        return None, None

    def handle_invite_code(self, code, username=''):
        from .tasks import send_notification
        if code == "" or self.request.user.parent is not None:
            return TEXTS["wrong_invite_code"]
        invite_code = InviteCode.objects.filter(code=code)
        coin_code = CoinCode.objects.filter(code=code)
        if invite_code.count() > 0:
            invite_code =  invite_code.first()
            user = invite_code.user
            if user == self.request.user:
                return TEXTS["wrong_invite_code"]
            if not invite_code.perminent:
                invite_code.delete()
            user.coins += config.INVITE_CODE_PARENT_REWARD
            send_notification.delay(user.id, TEXTS["friend_added_title"], TEXTS["friend_added"].format(username))
            user.save()
            self.request.user.parent = user
            self.request.user.coins += config.INVITE_CODE_CHILD_REWARD
            self.request.user.save()
        elif coin_code.count() > 0:
            coin_code =  coin_code.first()
            self.request.user.coins += coin_code.coin_amount
            self.request.user.save()
            return (
                None,
                get_text('coin_code').format(coin_code.coin_amount)
            )
        else:
            return TEXTS["wrong_invite_code"], None
        return (
            None,
            TEXTS["added_as_friend"].format(user, config.INVITE_CODE_CHILD_REWARD),
        )

    def handle(self):
        params = self.get_params()
        context = {}
        error, suggestion = SetPlayerInfoHandler.validate(params)
        msg = None
        if error is None:
            if params["invite_code"]:
                error, msg = self.handle_invite_code(params["invite_code"], username=params["username"])
            if error is None:
                self.request.user.logged_in = True
                self.request.user.last_daily_reward = get_time()
                self.request.user.username = params["username"]
                context["welcome_message"] = get_text("welcome_message")
                if msg:
                    context["message"] = msg
                context["succeed"] = True
                context["username"] = self.request.user.username
                self.request.user.save()
        if error is not None:
            context["succeed"] = False
            context["error"] = error
            if suggestion:
                context["suggestion"] = suggestion
        return self.response("set_playerinfo", context)


class SubmitEmailVerifyHandler(Handler):
    def handle(self):
        params = self.get_params()
        code = params["code"]
        email = params["email"]
        phone = params["phone"]
        context = {}
        if (
            len(self.request.user.verify_code) > 0
            and self.request.user.verify_code == code
        ):
            self.request.user.email = params["email"]
            self.request.user.phone = params["phone"]
            self.request.user.coins += config.EMAIL_VERIFY_REWARD
            self.request.user.verify_code = ""
            self.request.user.save()
            context["coins"] = config.EMAIL_VERIFY_REWARD
            context["succeed"] = True
        else:
            context["succeed"] = False
            context["error"] = get_text("wrong_verify_code")
        return self.response("submit_email_verify", context)


class SubmitEmailHandler(Handler):
    def validate_phone(phone):
        if len(phone) != 11 or phone[0] != '0':
            raise Exception('')
    
    def handle(self):
        from django.core.validators import validate_email

        params = self.get_params()
        context = {}
        email = params.get('email', '')
        phone = params.get('phone', '')
        if len(email) > 0:
            try:
                validate_email(email)
            except:
                context["succeed"] = False
                context["error"] = TEXTS["invalid_email"]
            else:
                if (
                    User.objects.exclude(pk=self.request.user.pk)
                    .filter(email=email)
                    .count()
                    > 0
                ):
                    context["succeed"] = False
                    context["error"] = TEXTS["email_exist"]
                else:
                    code = ""
                    for i in range(4):
                        code += chr(random.randint(ord("1"), ord("9")))
                    self.request.user.verify_code = code
                    self.request.user.save()
                    send_email(
                        email,
                        "Verify code",
                        get_text('your_verify_code').format(code)
                    )
                    context["succeed"] = True
        elif len(phone) > 0:
            try:
                SubmitEmailHandler.validate_phone(phone)
            except:
                context["succeed"] = False
                context["error"] = TEXTS["invalid_phone"]
            else:
                if (
                    User.objects.exclude(pk=self.request.user.pk)
                    .filter(phone=phone)
                    .count()
                    > 0
                ):
                    context["succeed"] = False
                    context["error"] = TEXTS["phone_exist"]
                else:
                    code = ""
                    for i in range(4):
                        code += chr(random.randint(ord("1"), ord("9")))
                    self.request.user.verify_code = code
                    self.request.user.save()
                    send_sms(phone, get_text('your_verify_code').format(code))
                    # send sms here
                    # send_mail(
                    #     "کد تایید",
                    #     "کد تایید شما : {}".format(code),
                    #     "parhamic@gmail.com",
                    #     [email],
                    # )
                    context["succeed"] = True
        return self.response("submit_email", context)


class MatchesListHandler(Handler):
    def get_matches_list(user):
        context = {}
        context["matches"] = []
        for match in user.matches.all().order_by('-created'):
            m = {}
            users = match.users.all()
            users = sorted(users, key=lambda x: x.pk != match.user_created.pk)
            if len(users) < 2:
                match.delete()
                continue
            match_info = MatchInfoHandler.get_match_info(user, match.pk)
            m["user1"] = users[0]
            m["user2"] = users[1]
            m["state"] = match.state
            m["won"] = match.winner == user
            m["draw"] = match.winner is None
            m["reward_coins"] = match_info.get('reward_coins', 0)
            m["id"] = match.pk
            context["matches"].append(m)
        priority = {
            'STARTED': 0,
            'PENDING': 1,
            'FINISHED': 2
        }
        context["matches"].sort(key=lambda x: priority[x["state"]])
        return context

    def handle(self):
        params = self.get_params()
        context = MatchesListHandler.get_matches_list(self.request.user)
        return self.response("matches_list", context)


class MatchInfoHandler(Handler):
    def get_match_info(user, pk):
        match = None
        try:
            match = Match.objects.get(pk=pk)
        except:
            return {"match_deleted": True}
        context = {}
        if match.emojis.filter(target=user).count() > 0:
            emojies = match.emojis.filter(target=user)[:5]
            context['emojies'] = []
            for emoji in emojies:
                e = {}
                e['emoji'] = emoji.emoji
                e['emoji_sender'] = emoji.user
                e['delay'] = (random.random()*3.5) if emoji.user.is_bot else 0
                context['emojies'].append(e)
                emoji.delete()
            
            # match.emojis.filter(target=user).delete()

        users = match.users.all()
        users = sorted(users, key=lambda x: x.pk != user.pk)
        context["user1"] = users[0]
        context["user2"] = users[1]
        context["winner"] = match.winner
        if match.tournoment is None:
            scale = 1
            trophy_scale = 1
            if match.winner is None:
                scale = 0.5
                trophy_scale = 0
            elif match.winner.pk != user.pk:
                scale = 0
                trophy_scale = -1
            match_level = Level.objects.get(level_id=0)
            context["reward_coins"] = int(match_level.coin * scale)
            context["reward_score"] = int(match_level.score * scale)
            context["reward_trophy"] = int(match_level.trophy * trophy_scale)
        else:
            tournoment_user = match.tournoment.users.filter(user=user).first()
            context['wins'] = tournoment_user.wins
            context['loses'] = tournoment_user.loses

        context["state"] = match.state
        if match.state == 'FINISHED':
            scores = match.get_scores_dict()
            for key in scores:
                if key == user.pk:
                    context["your_words"] = scores[key]
                else:
                    context["their_words"] = scores[key]
        context["games"] = []
        for game in match.games.all():
            g = {}
            g["user"] = game.user
            g["state"] = game.state
            g["score"] = game.score
            g["total"] = get_match_total_score()
            g["row"] = game.row
            g["id"] = game.pk
            context["games"].append(g)
        return context

    def handle(self):
        params = self.get_params()
        context = MatchInfoHandler.get_match_info(self.request.user, params["match_id"])
        return self.response("match_info", context)

class MatchEmojiHandler(Handler):
    def handle(self):
        params = self.get_params()
        match = Match.objects.get(pk=params["match_id"])
        MatchEmoji.objects.create(emoji=params['emoji'], user=self.request.user, target=self.request.user, match=match)
        if match.other_user(self.request.user).is_bot:
            is_in_lobby = match.games.filter(user=match.other_user(self.request.user), state='PLAYING').count() == 0
            if random.randint(0, 100) < 35 and is_in_lobby:
                MatchEmoji.objects.create(emoji=random.choice([':)', 'Nice', 'BLD', '#1', ':))', '#3', '#4']), user=match.other_user(self.request.user), target=self.request.user, match=match)
        else:
            MatchEmoji.objects.create(emoji=params['emoji'], user=self.request.user, target=match.other_user(self.request.user), match=match)
        return self.response("match_emoji", None)

class MatchSorroundHandler(Handler):
    def handle(self):
        params = self.get_params()
        match = Match.objects.get(pk=params["match_id"])
        context = {}
        context["succeed"] = True
        match.games.filter(user=self.request.user).update(score=0, state="FINISHED")
        match.games.exclude(user=self.request.user).update(
            score=get_match_total_score(), state="FINISHED"
        )
        match.give_rewards()
        context.update(MatchInfoHandler.get_match_info(self.request.user, match.pk))

        other_user = match.other_user(self.request.user)
        other_user.send_message('match_result', 
                    MatchInfoHandler.get_match_info(other_user, match.pk))
        return self.response("match_sorround", context)


class MatchGameHandler(Handler):
    def handle(self):
        params = self.get_params()
        match_game = MatchGame.objects.get(pk=params["game_id"])
        context = {}
        context["succeed"] = False
        if match_game.state == "WAITING" and match_game.user == self.request.user:
            match_game.state = "PLAYING"
            match_game.save()
            context["succeed"] = True
        return self.response("match_game", context)


class QueueHandler(Handler):
    def handle(self):
        from .tournoment import Tournoment
        if self.request.user.matches.filter(state='PENDING').count() >= 4:
            return self.response('queue', {'error': get_text('matches_limit_reached')})
        params = self.get_params()
        tournoment = None
        if "tournoment" in params:
            tournoment = Tournoment.objects.get(pk=params["tournoment"])
            tournoment_matches = tournoment.matches.filter(users=self.request.user).exclude(state="FINISHED")
            if tournoment_matches.count() > 0:
                return self.response(
                    "queue", {"error": get_text("tournoment_match_exist"), "match_id": tournoment_matches.first().pk}
                )
        self.request.user.in_queue = params["in_queue"]
        self.request.user.queued_tournoment = tournoment
        if params["in_queue"]:
            self.request.user.queued_time = get_time()
        self.request.user.save()
        return self.response("queue", {"in_queue": self.request.user.in_queue})


class SubmitWordHandler(Handler):
    def handle(self):
        params = self.get_params()
        word_text = params["word"]
        context = {}
        context["succeed"] = True
        try:
            word = Word.objects.get(simple_word=word_text)
            self.request.user.coins += config.HIDDEN_WORDS_REWARD
            self.request.user.save()
        except:
            context["succeed"] = False
        return self.response("submit_word", context)


class LevelQuestionsHandler(Handler):
    def generate_words(level):
        all_words = Word.objects.values_list("simple_word", flat=True).distinct()
        all_words = list(all_words)
        random.shuffle(all_words)
        words_based_on_length = []
        total_questions = 0
        # TODO: Remove me
        setattr(
            level,
            "num_questions_length8",
            0,
        )
        for i in range(0, 9):
            words_based_on_length.append([])
            if i >= 1:
                total_questions += getattr(level, "num_questions_length{}".format(i))
        for word in all_words:
            if len(word) > 8:
                continue
            words_based_on_length[len(word)].append(word)

        questions = []
        max_ln = 0


        for i in range(8, 0, -1):
            if getattr(level, "num_questions_length{}".format(i)) > 0:
                max_ln = i
                break
        setattr(
            level,
            "num_questions_length{}".format(max_ln),
            getattr(level, "num_questions_length{}".format(max_ln)) - 1,
        )
        while len(questions) < total_questions:
            questions = []
            letters = []
            biggest_word = random.choice(words_based_on_length[max_ln])
            questions.append(biggest_word)
            from django.conf import settings
            alphabet = settings.ALPHABET
            for ch in biggest_word:
                if ch == "آ":
                    ch = "ا"
                letters.append(ch)
            for i in range(level.extra_letters):
                letters.append(random.choice(alphabet))
            for ln in range(1, 9):
                count = 0
                for word in words_based_on_length[ln]:
                    if count >= getattr(level, "num_questions_length{}".format(ln)):
                        break
                    if word == biggest_word:
                        continue
                    word.replace("آ", "ا")
                    can_make_word = True
                    letters_mark = [0] * len(letters)
                    for ch in word:
                        # search in the letters
                        found_letter = False
                        for i in range(len(letters)):
                            if letters_mark[i]:
                                continue
                            if letters[i] == ch:
                                letters_mark[i] = 1
                                found_letter = True
                                break
                        if not found_letter:
                            can_make_word = False
                            break
                    if can_make_word:
                        questions.append(word)
                        count += 1
                if count < getattr(level, "num_questions_length{}".format(ln)):
                    break
        return letters, questions

    def handle(self):
        params = self.get_params()
        level_id = params["level_id"]
        level = Level.objects.get(level_id=level_id)
        match_game = None
        if level_id == 0:
            match_game = MatchGame.objects.get(pk=params["game_id"])
            parral_match = match_game.match.games.filter(row=match_game.row).exclude(
                pk=match_game.pk
            )[0]
        if level_id != 0 or not parral_match.generated:
            letters, questions = LevelQuestionsHandler.generate_words(level)
            if level_id == 0:
                match_game.generated = True
                match_game.letters = ",".join(letters)
                match_game.questions = ",".join(questions)
        else:
            letters = parral_match.letters.split(",")
            questions = parral_match.questions.split(",")
        if match_game:
            match_game.start_time = get_time()
            match_game.save()
        self.request.user.last_chosen_words = json.dumps(questions)
        self.request.user.save()
        random.shuffle(letters)
        return self.response(
            "level_questions",
            {"letters": letters, "questions": questions, "time": level.time},
        )


class LevelCompleteHandler(Handler):
    def complete_game(match_game, corrects_number):
        match_game.state = "FINISHED"
        match_game.score = corrects_number
        match_game.save()

        # select next match
        if match_game.match.turned_base:
            next_match_game = (
                match_game.match.games.exclude(user=match_game.user)
                .filter(state="DEACTIVE")
                .first()
            )
        else:
            next_match_game = (
                match_game.match.games.filter(user=match_game.user)
                .filter(state="DEACTIVE")
                .first()
            )
        if next_match_game:
            next_match_game.state = "WAITING"
            # check for bot game
            if next_match_game.user.is_bot:
                # next_match_game.state = "PLAYING"
                next_match_game.start_time = get_time() + timezone.timedelta(seconds=10)
            next_match_game.save()
            # next_match_game.user.send_message(
            #     'notification', {'msg': TEXTS['your_turn'], 'type': 'turn'})
            # next_match_game.user.send_notification(
            #     'Your turn', 'its your turn to play now')
        # game is finished
        if match_game.match.games.exclude(state="FINISHED").count() == 0:
            match_game.match.give_rewards()
            other_user = match_game.match.other_user(match_game.user)
            other_user.send_message('match_result', 
                        MatchInfoHandler.get_match_info(other_user, match_game.match.pk))

    def handle(self):
        params = self.get_params()
        level_id = params["level_id"]
        game_id = params["game_id"]
        words = params["words"]
        corrects_number = params["corrects_number"]
        time = int(params["time"])
        context = {}

        level = Level.objects.get(level_id=level_id)
        track = LevelTrack.objects.create(level=level, user=self.request.user,
                start_coin=params['track_startcoin'], finish_coin=params['track_finishcoin'],
                time=params['track_time'], help_used=params['track_helpused'])
        
        if level_id == 0:  # match game
            try:  # the match may be deleted
                match_game = MatchGame.objects.get(pk=game_id, state="PLAYING")
                LevelCompleteHandler.complete_game(match_game, corrects_number)
            except:
                pass
        else:
            def calculate_reward(amount, turn):
                if turn == 2:
                    return round(amount/3*2)
                if turn == 3:
                    return round(amount/3)
                return amount
            which_third = 1
            coins = 0
            if time < (level.time // 3) * 2:
                which_third = 2
            if time < (level.time // 3):
                which_third = 3
            track.stars = which_third
            track.save()
            if level_id >= self.request.user.level_reached:
                self.request.user.give_xp(calculate_reward(level.score, which_third))
                coins = calculate_reward(level.coin, which_third)
                self.request.user.coins += coins
                try:
                    next_level = Level.objects.filter(level_id__gt=level_id)[0]
                    self.request.user.level_reached = max(
                        next_level.level_id, self.request.user.level_reached
                    )

                    # gift
                    if next_level.level_id == 11001: # start of part 2
                        self.request.user.boost = 1.2
                        self.request.user.boost_expire = get_time() + timezone.timedelta(days=1)
                        self.request.user.send_message("show_popup", {'title': get_text('starter_boost_title'), 'message': get_text('starter_boost')})
                except:
                    self.request.user.level_reached += 1
                self.request.user.save()
            context["coins"] = coins
            context["stars"] = 3 - which_third
            context["words"] = list(
                Word.objects.filter(simple_word__in=words)
                .values_list("simple_word", flat=True)
                .distinct()
            )
        context["level_reached"] = self.request.user.level_reached
        return self.response("level_complete", context)


class InviteRejectHandler(Handler):
    def handle(self):
        params = self.get_params()
        match = Match.objects.get(pk=params["match_id"])
        InvitePlayerHandler.reject(match.users.first(), match.users.last())


class InvitePlayerHandler(Handler):
    def reject(from_user, to_user):
        Match.objects.filter(users=to_user).filter(users=from_user).filter(
            state="PENDING"
        ).delete()
        from_user.send_message("rejected", {'owner':True})
        to_user.send_message("rejected", {'name':from_user.username})

    def invite(from_user, to_user, rematch=False, cancel=False, turned_base=False):
        context = {}
        user = to_user
        context["succeed"] = False
        if (
            Match.objects.exclude(state="FINISHED")
            .filter(users=user)
            .filter(users=from_user)
            .count()
            > 0
        ):
            if cancel:
                Match.objects.filter(state="PENDING").filter(users=user).filter(
                    users=from_user
                ).delete()
                context["succeed"] = True
            elif rematch:
                match = (
                    Match.objects.filter(state="PENDING")
                    .filter(users=user)
                    .filter(users=from_user)
                    .first()
                )
                if match:
                    match.state = "STARTED"
                    match.save()
                    user.send_message("play_next_match", {"pk": match.pk, "name":from_user.username})
                    context["succeed"] = True
                    context["pk"] = match.pk
            else:
                context["error"] = TEXTS["cant_invite_again"].format(user)
        elif user.is_bot and not rematch:
            context["error"] = TEXTS["user_dont_exist"]
        else:
            create_match([from_user, user], "PENDING", from_user, turned_base)
            user.send_message("invite_received", {"username": from_user})
            from .tasks import send_notification
            send_notification.delay(user.id, "دعوت جدید", TEXTS["invite_received"].format(from_user))
            context["succeed"] = True
            context["username"] = user
            context["message"] = TEXTS["invite_player"].format(user)
        return context

    def handle(self):
        params = self.get_params()
        rematch = params.get("rematch", False)
        cancel = params.get("cancel", False)
        turned_base = params.get("turned_base", False)

        context = {}
        context["succeed"] = False
        user = None
        try:
            user = User.objects.get(username=params["username"])
        except:
            context["error"] = TEXTS["user_dont_exist"]
        else:
            if user == self.request.user:
                context["error"] = TEXTS["cant_invite_self"]
            else:
                context = InvitePlayerHandler.invite(
                    from_user=self.request.user,
                    to_user=user,
                    rematch=rematch,
                    cancel=cancel,
                    turned_base=turned_base,
                )

        return self.response("invite_player", context)


class ReplyInviteHandler(Handler):
    def handle(self):
        params = self.get_params()
        accepted = params["accepted"]
        user = User.objects.get(username=params["username"])
        match = (
            Match.objects.filter(state="PENDING")
            .filter(users=user)
            .filter(users=self.request.user)[0]
        )
        if accepted:
            match.state = "STARTED"
            match.save()
            self.request.user.send_message("play_next_match", {"pk": match.pk, "owner": True})
            user.send_message("play_next_match", {"pk": match.pk, "name":self.request.user.username})
        else:
            match.delete()
            InvitePlayerHandler.reject(self.request.user, user)
        
        user.send_message('invite_reply_notif', {'accepted':accepted, 'user':self.request.user.username})
        context = MatchesListHandler.get_matches_list(self.request.user)
        return self.response("reply_invite", context)


class CoinCodeHandler(Handler):
    def handle(self):
        params = self.get_params()
        code = params["code"]
        context = {}
        context["succeed"] = True
        coin = CoinCode.objects.filter(code__iexact=code)
        if coin.count() > 0:
            coin = coin[0]
            if coin.users.filter(pk=self.request.user.pk).count() > 0:
                context["error"] = get_text("coin_duplicate")
                context["succeed"] = False
            else:
                context["coins"] = coin.coin_amount
                self.request.user.coins += coin.coin_amount
                self.request.user.save()
                coin.users.add(self.request.user)
                coin.save()
        else:
            context["error"] = TEXTS["wrong_code"]
            context["succeed"] = False
        return self.response("coin_code", context)


class PurchaseHandler(Handler):
    def get_prices():
        return {
            "help_1": config.HELP_1_LETTER_PRICE,
            "help_2": config.HELP_2_LETTER_PRICE,
            "timer_reset": config.TIMER_RESET_PRICE,
            "hidden_words": config.HIDDEN_WORDS_REWARD,
        }

    def handle(self):
        PRICES = PurchaseHandler.get_prices()
        params = self.get_params()
        purchase_id = params.get('purchase_id', 0)
        t = params["type"]
        price = PRICES[t]
        context = {}
        context["succeed"] = False
        if self.request.user.coins >= price:
            self.request.user.coins -= price
            self.request.user.save(update_message=False)
            context["succeed"] = True
            context["price"] = price
            if t == "timer_reset":
                self.request.user.games.filter(state="PLAYING").update(
                    start_time=get_time()
                )
        else:
            context["succeed"] = False
            context["error"] = TEXTS["not_enough_coins"]

        context["coins"] = self.request.user.coins
        context['purchase_id'] = purchase_id
        return self.response("purchase", context)


class LeaderBoardHandler(Handler):
    def convert_list_of_users(self, users, trophy_type):
        l = []
        for user in users:
            u = {}
            u["name"] = user.username
            u["level"], u["xp"] = user.get_level()
            u["trophy"] = getattr(user, trophy_type)
            l.append(u)
        return l

    def get_user_rank(self, user, users, trophy_type):
        rank = 0
        top_users = users[:20]
        for index, t in enumerate(top_users):
            if t.pk == user.pk:
                rank = index + 1
                break
        if rank == 0:
            kwargs = {"{}__gt".format(trophy_type): getattr(user, trophy_type)}
            rank = users.filter(**kwargs).count()
            rank += users.filter(**kwargs, pk__gt=user.pk).count()
        return rank

    def handle(self):
        params = self.get_params()
        context = {}
        # filter is_bot = True for these four
        users_alltime = User.objects.order_by("-trophy", "-pk")
        users_week = User.objects.order_by("-trophy_week", "-pk")
        users_month = User.objects.order_by("-trophy_month", "-pk")
        users_year = User.objects.order_by("-trophy_year", "-pk")
        context["rank_alltime"] = self.get_user_rank(
            self.request.user, users_alltime, "trophy"
        )
        context["rank_week"] = self.get_user_rank(
            self.request.user, users_week, "trophy_week"
        )
        context["rank_month"] = self.get_user_rank(
            self.request.user, users_month, "trophy_month"
        )
        context["rank_year"] = self.get_user_rank(
            self.request.user, users_year, "trophy_year"
        )

        context["users_alltime"] = self.convert_list_of_users(
            users_alltime[:20], "trophy"
        )
        context["users_week"] = self.convert_list_of_users(
            users_week[:20], "trophy_week"
        )
        context["users_month"] = self.convert_list_of_users(
            users_month[:20], "trophy_month"
        )
        context["users_year"] = self.convert_list_of_users(
            users_year[:20], "trophy_year"
        )
        return self.response("leader_board", context)


class UserProfileHandler(Handler):
    def get_user_profile(username, requested_by=None):
        from .models import LEVELS_XPS

        context = {}
        user = User.objects.get(username=username)
        context["is_self"] = username == requested_by
        context["username"] = user
        context["coins"] = user.coins
        context["hidden_words"] = user.hidden_words
        context["copouns"] = user.copouns
        context["invite_code"] = "1234"
        context["level"], context["xp"] = user.get_level()
        context["boost"] = user.boost
        if user.boost_expire:
            diff = (user.boost_expire - get_time())
            context["boost_time"] = diff.days * 24 * 3600 + diff.seconds
        else:
            context['boost_time'] = 0
        context["actual_xp"] = user.xp
        context["trophy"] = user.trophy
        context["level_reached"] = user.level_reached
        context["games"] = user.matches.filter(state="FINISHED").count()
        context["won"] = user.matches.filter(state="FINISHED", winner=user).count()
        context["max_xp"] = LEVELS_XPS()[context["level"]]
        context["badges"] = list(user.badges.all())
        context["friends"] = []
        friend_list = user.childs.all().order_by("username")
        for f in friend_list:
            context["friends"].append(
                {
                    "name": f.username,
                    "commission": int(
                        f.spent * config.FRIEND_SHARE_PERCENTAGE / 100
                    ),
                    "spent": f.spent,
                }
            )
        return context

    def handle(self):
        params = self.get_params()
        username = params["username"]
        context = UserProfileHandler.get_user_profile(
            username, self.request.user.username
        )
        return self.response("user_profile", context)


class DailyRewardHandler(Handler):
    def handle(self):
        import math

        params = self.get_params()
        reroll = params["reroll"] if params else False
        context = {}
        succeed = False
        context["succeed"] = False
        if not (
            self.request.user.last_daily_reward
            and get_time()
            < self.request.user.last_daily_reward + timezone.timedelta(days=1)
        ):
            self.request.user.reroll = True
            succeed = True

        if succeed or (reroll and self.request.user.reroll):
            RESULTS = config.DAILY_REWARDS.split(",")
            context["result"] = RESULTS[
                int(random.uniform(0, math.sqrt(len(RESULTS))) ** 2)
            ]
            context["results"] = RESULTS
            self.request.user.daily_reward = int(context["result"])
            if not succeed:
                self.request.user.reroll = False
            context["succeed"] = True
            self.request.user.save()
        return self.response("daily_reward", context)


class SubmitDailyRewardHandler(Handler):
    def handle(self):
        self.request.user.coins += self.request.user.daily_reward
        self.request.user.daily_reward = 0
        self.request.user.last_daily_reward = get_time()
        self.request.user.save()
        return self.response("submit_daily_reward", {})

class AutoLoginHandler(Handler):
    def handle(self):
        from .views import generate_password
        
        params = self.get_params()
        context = {}
        context['succeed'] = False

        user = User.objects.filter(device_id=params["device_id"])
        if user.count() > 0:
            context['succeed'] = True
            user = user.first()

            pw = generate_password()
            user.set_password(pw)
            user.last_daily_reward = get_time()
            user.save()
            context["username"] = user.username
            context["password"] = pw
            context["token"] = Token.objects.get_or_create(user=user)[0].key

        return self.response('auto_login', context)

class LoginVerifyEmailHandler(Handler):
    def send_verify_email(email=None, phone=None):
        context = {}
        code = ""
        context["succeed"] = True
        for i in range(4):
            code += chr(random.randint(ord("1"), ord("9")))
            user = None
        verify_type = 'email'
        try:
            user = User.objects.get(email=email)
        except:
            pass
        try:
            user = User.objects.get(phone=phone)
            verify_type = 'sms'
        except:
            print ('user not found with phone {}'.format(phone))
            pass
        if user is None:
            context["succeed"] = False
            context["error"] = TEXTS["email_dont_exist"]
        else:
            user.verify_code = code
            user.save()
            if verify_type == 'email':
                send_mail(
                    user.email,
                    "Email Verify",
                    "Your code is : {} ".format(code)
                )
            else:
                send_sms(user.phone, 'جان جیبی\nکد تایید شما : {}'.format(code))
        return context

    def handle(self):
        params = self.get_params()
        print ('logging in with email {} phone {}'.format(params["email"], params["phone"]))
        context = LoginVerifyEmailHandler.send_verify_email(params["email"], params["phone"])
        return self.response("verify_email", context)


class LoginVerifyEmailCodeHandler(Handler):
    def handle(self):
        from .views import generate_password

        params = self.get_params()
        context = {}
        context["succeed"] = True
        user = None
        try:
            user = User.objects.get(email=params["email"])
        except:
            pass
        try:
            user = User.objects.get(phone=params["phone"])
        except:
            pass
        if user is not None:
            if user.verify_code == params["code"]:
                pw = generate_password()
                user.set_password(pw)
                user.last_daily_reward = get_time()
                user.save()
                context["username"] = user.username
                context["password"] = pw
                context["token"] = Token.objects.get_or_create(user=user)[0].key
                if not self.request.user.logged_in:
                    self.request.user.delete()
            else:
                context["succeed"] = False
                context["error"] = TEXTS["wrong_verify_code"]
        else:
            context["succeed"] = False
            context["error"] = TEXTS["email_dont_exist"]
        return self.response("verify_email_code", context)


class TicketsListHandler(Handler):
    def get_tickets_list(user):
        context = []
        for ticket in user.tickets.all():
            t = {}
            t["title"] = ticket.title
            t["ticket_id"] = ticket.pk
            t["messages"] = []
            for msg in ticket.messages.all():
                m = {}
                m["is_admin"] = msg.is_admin
                m["message"] = msg.message
                t["messages"].append(m)
            t["messages"].reverse()
            context.append(t)
        return context

    def handle(self):
        params = self.get_params()
        context = {}
        context["tickets"] = TicketsListHandler.get_tickets_list(self.request.user)
        return self.response("tickets_list", context)


class AddTicketHandler(Handler):
    def handle(self):
        from .models import Ticket, TicketMessage

        params = self.get_params()
        title = params["title"]
        category = params["category"]
        text = params["text"]
        ticket = Ticket.objects.create(
            category=category, title=title, state="OP", user=self.request.user
        )
        TicketMessage.objects.create(ticket=ticket, message=text)

        self.request.user.send_message(
            "tickets_list",
            {"tickets": TicketsListHandler.get_tickets_list(self.request.user)},
        )
        return self.response("add_ticket", None)


class TicketMessageHandler(Handler):
    def handle(self):
        from .models import Ticket, TicketMessage

        params = self.get_params()
        msg = params["message"]
        ticket = params["ticket_id"]
        ticket = Ticket.objects.get(pk=ticket)
        TicketMessage.objects.create(ticket=ticket, message=msg)

        return self.response(
            "ticket_message",
            {"tickets": TicketsListHandler.get_tickets_list(self.request.user)},
        )


class LotteryParticipateHandler(Handler):
    def handle(self):
        params = self.get_params()
        pk = params["pk"]
        copouns = params["copouns"]
        context = {}
        context["succeed"] = False
        lottery = None
        try:
            lottery = Lottery.objects.get(pk=pk)
        except:
            context["error"] = TEXTS["lottery_dont_exist"]
        else:
            if lottery.users.filter(user=self.request.user).count() != 0:
                context["error"] = TEXTS["lottery_already_participated"]
            elif self.request.user.copouns >= copouns and copouns > 0:
                level, _ = self.request.user.get_level()
                if level >= lottery.min_level and level <= lottery.max_level:
                    LotteryUser.objects.create(
                        lottery=lottery, user=self.request.user, copouns=copouns
                    )
                    self.request.user.copouns -= copouns
                    self.request.user.save()
                    context["succeed"] = True
                    context["copouns"] = self.request.user.copouns
                    self.request.user.send_mail(
                        get_text('lottery_participate_title'), get_text('lottery_participate').format(lottery)
                    )
                else:
                    context["error"] = TEXTS["not_in_levelrange"]
            else:
                context["error"] = TEXTS["not_enough_copouns"]
        return self.response("lottery_participate", context)


class LotteryTimeHandler(Handler):
    def handle(self):
        params = self.get_params()
        pk = params["pk"]
        lottery = Lottery.objects.get(pk=pk)
        context = {}
        context["time"] = (
            lottery.last_active_time
            + timezone.timedelta(days=lottery.days)
            - get_time()
        ).seconds
        return self.response("lottery_time", context)


class ReadMailsHandler(Handler):
    def handle(self):
        self.request.user.messages.filter(hidden=True).delete()
        return self.response("read_mails", None)


class SellAccountHandler(Handler):
    def handle(self):
        if SellAccount.objects.filter(account=self.request.user).count() > 0:
            return self.response("account_sell", {"succeed": False, "error": "Exists"})
        params = self.get_params()
        SellAccount.objects.create(
            account=self.request.user,
            price=params["price"],
            text=params.get("text", ""),
        )
        return self.response("account_sell", {"succeed": True})


class HiddenWordHandler(Handler):
    def handle(self):
        params = self.get_params()
        collect = False
        if params:
            collect = params.get('collect', False)
        context = {}
        context['succeed'] = False
        if collect:
            if self.request.user.hidden_words >= 10:
                self.request.user.hidden_words -= 10
                self.request.user.coins += config.HIDDEN_WORDS_REWARD
                self.request.user.save()
                context['succeed'] = True
                context['coins'] = config.HIDDEN_WORDS_REWARD
        else:
            self.request.user.hidden_words += 1
            self.request.user.save()
            context['succeed'] = True

        context['hidden_words'] = self.request.user.hidden_words
        return self.response("hidden_word", context)


class ReachRewardHandler(Handler):
    def handle(self):
        params = self.get_params()
        level_id = int(params["level"])
        context = {}
        context["succeed"] = False
        if (
            self.request.user.level_reached >= level_id + 1
            and self.request.user.collected_reach_reward <= level_id
        ):
            level = Level.objects.get(level_id=level_id)
            coins = level.reach_reward
            context["succeed"] = True
            context["coins"] = coins
            context["has_next"] = (
                Level.objects.filter(
                    part=level.part, season=level.season, level_id__gt=level_id
                ).count()
                > 0
            )
            context["part"] = level.part

            context['has_package'] = (level.reach_reward_package is not None)
            if context['has_package']:
                context['package_coins'] = level.reach_reward_package.coins
                context['package_copouns'] = level.reach_reward_package.copouns
                context['package_score'] = level.reach_reward_package.score
                self.request.user.coins += context['package_coins']
                self.request.user.copouns += context['package_copouns']
                self.request.user.give_xp(context['package_score'])
            self.request.user.coins += coins
            self.request.user.collected_reach_reward = level_id + 1
            self.request.user.save()
        return self.response("reach_reward", context)


class AdRewardHandler(Handler):
    def handle(self):
        params = self.get_params()
        context = {}
        context["succeed"] = True
        context["coins"] = config.AD_COINS
        self.request.user.coins += config.AD_COINS
        self.request.user.save()
        return self.response("ad_reward", context)


class ShopPurchaseHandler(Handler):
    def handle(self):
        params = self.get_params()
        print (params, flush=True)
        paid = params.get('paid', False)
        pk = params["pk"]
        shop_item = ShopItem.objects.get(pk=pk)
        context = {}
        if paid:
            context["succeed"] = True
            context['coins'] = shop_item.coins
            self.request.user.spent += shop_item.price
            self.request.user.coins += shop_item.coins
            self.request.user.save()
            Log.objects.create(
                user=self.request.user,
                category="Purchase",
                description="time: {}, orderID: {}, package: {}, price: {}, signiture:{}".format(
                    get_time(),
                    params["id"],
                    shop_item.name,
                    shop_item.price,
                    params["sign"],
                ),
            )
        
        if self.request.user.can_buy(shop_item.price_coins, commit=True):
            context["succeed"] = True
            if shop_item.category == 'BOOST':
                self.request.user.boost = max(
                    shop_item.boost, self.request.user.boost
                )
                self.request.user.boost_expire = max(
                    get_time()
                    + timezone.timedelta(days=shop_item.boost_time),
                    self.request.user.boost_expire or get_time(),
                )
                context["msg"] = get_text('bought_boost').format(shop_item.boost_time, shop_item.boost)
            
            self.request.user.save()
        else:
            context["succeed"] = False
            context['error'] = get_text('not_enough_coins')
        return self.response("shop_purchase", context)


class PendingMatchesHandler(Handler):
    def handle(self):
        context = {}
        context['has_match'] = False
        pending_matches = self.request.user.matches.filter(state='STARTED')
        if pending_matches.count() > 0:
            for match in pending_matches:
                if match.played_all_games(self.request.user):
                    continue
                context['has_match'] = True
                context['match_id'] = match.id
                context['name'] = match.other_user(self.request.user)
                break
        return self.response('pending_matches', context)

class GetInviteCodeHandler(Handler):
    def handle(self):
        context = {}
        context["invite_code"] = InviteCode.objects.create(user=self.request.user).code
        return self.response('get_invite_code', context)

class SubmitInviteCodeHandler(Handler):
    def handle(self):
        context = {}
        context['succeed'] = True
        params = self.get_params()
        error, msg = SetPlayerInfoHandler(self.request).handle_invite_code(params['code'], self.request.user.username)
        if error is not None:
            context['succeed'] = False
            context['error'] = error
        else:
            context['msg'] = msg

        return self.response('submit_invite_code', context)

class AutoCompleteQueryHandler(Handler):
    def is_match(self, username, q):
        return q in username
    
    def handle(self):
        context = {}
        params = self.get_params()
        q = params['q']
        results = []
        
        for match in self.request.user.matches.all():
            for user in match.users.all():
                if self.is_match(user.username, q):
                    results.append(user.username)
        
        if self.request.user.parent and self.is_match(self.request.user.parent.username, q):
            results.append(self.request.user.parent.username)
        for child in self.request.user.childs.all():
            if self.is_match(child.username, q):
                results.append(child.username)
        
        for user in User.objects.all():
            if self.is_match(user.username, q):
                results.append(user.username)

        results = list(filter(lambda x: x != self.request.user.username, results)) # remove self
        results = results[:5]
        context['results'] = results
        return self.response('autocomplete_query', context)

MESSAGE_HANDLERS = {
    "game_info": GameInfoHandler,
    "get_invite_code": GetInviteCodeHandler,
    "matches_list": MatchesListHandler,
    "match_info": MatchInfoHandler,
    "match_sorround": MatchSorroundHandler,
    "match_game": MatchGameHandler,
    "queue": QueueHandler,
    "submit_word": SubmitWordHandler,
    "level_questions": LevelQuestionsHandler,
    "level_complete": LevelCompleteHandler,
    "set_playerinfo": SetPlayerInfoHandler,
    "submit_email": SubmitEmailHandler,
    "submit_email_verify": SubmitEmailVerifyHandler,
    "coin_code": CoinCodeHandler,
    "invite_player": InvitePlayerHandler,
    "reply_invite": ReplyInviteHandler,
    "purchase": PurchaseHandler,
    "leader_board": LeaderBoardHandler,
    "user_profile": UserProfileHandler,
    "daily_reward": DailyRewardHandler,
    "submit_daily_reward": SubmitDailyRewardHandler,
    "auto_login": AutoLoginHandler,
    "verify_email": LoginVerifyEmailHandler,
    "verify_email_code": LoginVerifyEmailCodeHandler,
    "tickets_list": TicketsListHandler,
    "add_ticket": AddTicketHandler,
    "ticket_message": TicketMessageHandler,
    "lottery_participate": LotteryParticipateHandler,
    "lottery_time": LotteryTimeHandler,
    "read_mails": ReadMailsHandler,
    "hidden_word": HiddenWordHandler,
    "reach_reward": ReachRewardHandler,
    "ad_reward": AdRewardHandler,
    "account_sell": SellAccountHandler,
    "shop_purchase": ShopPurchaseHandler,
    'pending_matches': PendingMatchesHandler,
    'match_emoji': MatchEmojiHandler,
    "autocomplete_query": AutoCompleteQueryHandler,
    "submit_invite_code": SubmitInviteCodeHandler,
}


def get_handlers():
    from .tournoment import TOURNOMENT_MESSAGE_HANDLERS

    MESSAGE_HANDLERS.update(TOURNOMENT_MESSAGE_HANDLERS)
    return MESSAGE_HANDLERS
