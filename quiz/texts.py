from django.conf import settings


TEXTS_TR = {
    "user_dont_exist": "oyuncu bulunmadı",
    "user_exist": "Bu kullanıcı adı zaten kayıtlı",
    "cant_invite_self": "Kendini davet edemezsin",
    "cant_invite_again": "{} İle bir oyununuz var",
    "your_turn": "نوبت بازی شماست.",
    "wrong_code": "Kod yanlış",
    "wrong_invite_code": "Kod yanlış",
    "wrong_verify_code": "Kod yanlış",
    "not_enough_coins": "Yeteince kadar oyun paran yok",
    "email_exist": "Bu e-posta zaten kayıtlı",
    "email_dont_exist": "This email doesnt exist in the server",
    "invite_player": "{}i Oynamaya davet ettin",
    "invite_received": "{} Seni oynamaya davet etti",
    "username_short": "Kullanıcı adı kısa",
    "invalid_input": "GEÇERSİZ GİRİŞ",
    "invalid_email": "E-posta geçerli değil",
    "invalid_phone": "Cep telefonu numarası 11 rakam olmalıdır",
    "phone_exist": "Girilen numara zaten kayıtlı",
    "friend_added_title": "Oynama davetiyesi",
    "friend_added": "{} Davet kodunuzu girdi",
    "added_as_friend": "{} in Arkadaş listesine eklendin ve {} oyun para kazandın.",
    "lottery_dont_exist": "Kura Çekilişi mevcut değil",
    "not_enough_copouns": "Yeterli kuponunuz yok",
    "lottery_already_participated": "Bu Kura Çekilişine zaten katıldınız",
    "tournoment_already_participated": "",
    "tournoment_level_range": "Bu Çekişmeye katılmak için en azından {} seviyede olmalısınız",
    "coin_duplicate": "Bu şarj kodu zaten kullanılmış.",
    "welcome_message": "Can Cepper oyununa hoş geldiniz ve şimdiden oyuna başlayabilirsiniz",
    "tournoment_match_exist": "Bu kura çekilimine zaten katıldınız.",
    "bought_boost": "Satın alma işleminiz başarıyla tamamlandı",
    'lottery_participate_title':'çekilişmeye katıl',
    'lottery_participate':'siz {} çekilişmesine katıldınız',
    'lottery_reward_title':'çekilişme sonuçları',
    'lottery_reward':'siz {1} çekilişmesinde, {0} oyun parası kazandınız',
    "complete_profile_title": "Tam profile",
    "complete_profile": "Lütfen kendi hesabını tamamla ve oyunun faydalarından faydalan",
    'starter_boost_title':'Odül',
    'starter_boost':'24 Saate kadar Hızlandırıcı odül aldın ve şimdi puan alma süren daha hızlanacak',
    'matches_limit_reached': '',

    'your_verify_code': 'Your verify code : {}'
}

TEXTS_FA = {
    "user_dont_exist": "این اسم وجود ندارد",
    "user_exist": "این اسم قبلا ثبت شده",
    "cant_invite_self": "خودتو نمی تونی دعوت کنی",
    "cant_invite_again": "قبلا {} رو دعوت کردی",
    "your_turn": "نوبت بازی شماست.",
    "wrong_code": "کد اشتباه است",
    "wrong_invite_code": "کد اشتباه است",
    "wrong_verify_code": "کد اشتباه است",
    "not_enough_coins": "سکه کافی ندارید",
    "email_exist": "ایمیل قبلا ثبت شده است",
    "email_dont_exist": "ایمیل وجود ندارد",
    "invite_player": "{} را به بازی دعوت کردید",
    "invite_received": "{} به بازی دعوتت کرد",
    "username_short": "اسم کوتاه است",
    "invalid_input": "خطایی رخ داده است",
    "invalid_email": "ایمیل صحیح نیست",
    "invalid_phone": "شماره تلفن صحیح نیست",
    "phone_exist": "شماره تلفن قبلا ثتب شده است",
    "friend_added_title": "دعوت به بازی",
    "friend_added": "{} رو به بازی دعوت کردید",
    "added_as_friend": "شما به عنوان دوست {} اضافه شدید و {} سکه برنده شدید",
    "lottery_dont_exist": "لاتاری منقضی شده است",
    "not_enough_copouns": "کوپن کافی ندارید",
    "lottery_already_participated": "قبلا در این لاتاری شرکت کردید",
    "tournoment_already_participated": "",
    "tournoment_level_range": "برای شرکت در این چالش حداقل باید سطح {} باشید",
    "coin_duplicate": "کد تکراری",
    "welcome_message": "Can Cepper oyununa hoş geldiniz ve şimdiden oyuna başlayabilirsiniz",
    "tournoment_match_exist": "یک بازی باز داری",
    "bought_boost": "خرید شما باموفقیت انجام شد",
    'lottery_participate_title':'قرعه کشی',
    'lottery_participate':'در قرعه کشی {} شرکت کردید',
    'lottery_reward_title':'جایزه',
    'lottery_reward':'شما {1} سکه از قرعه کشی {0} بردید',
    "complete_profile_title": "تکمیل پروفایل",
    "complete_profile": "برای دریافت جایزه پروفایل خود را تکمیل کنید",
    
    'starter_boost_title':'جایزه',
    'starter_boost':'تبریک، شتاب دهنده برنده شدی. به مدت 24 ساعت می تونی سریع تر امتیاز بگیری.',

    'your_verify_code': 'کد تایید شما : {}',
}

TEXTS = TEXTS_TR
if settings.LANGUAGE == 'FA':
    TEXTS = TEXTS_FA

def get_text(key):
    if TEXTS[key] == "":
        return key
    return TEXTS[key]
