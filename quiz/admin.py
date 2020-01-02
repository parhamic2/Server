from django.contrib import admin
from .models import (
    User,
    Message,
    Word,
    Level,
    Match,
    MatchGame,
    CoinCode,
    GlobalReward,
    Ticket,
    TicketMessage,
    LotteryUser,
    Lottery,
    ShopItem,
    SellAccount,
    Log,
    Badge,
    LevelTrack,
    ZarinPayment,
    InviteCode,
    SendNotification,
    PlayRecord,
    LEVELS_XPS
)
from .tournoment import Tournoment, TournomentUser
from django.utils import timezone
from .utils import get_time
from django.http import HttpResponse
from django.utils.html import format_html
import csv

admin.site.register(Message)
admin.site.register(SendNotification)
admin.site.register(MatchGame)
admin.site.register(CoinCode)
admin.site.register(Tournoment)
admin.site.register(TournomentUser)
admin.site.register(Badge)
admin.site.register(ZarinPayment)

admin.site.register(GlobalReward)
admin.site.register(ShopItem)
admin.site.register(SellAccount)


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        field_names = [field for field in self.model.export_fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename={}.csv".format(
            self.model._meta.verbose_name_plural
        )
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export Selected"


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    search_fields = ("word",)


class OnlineStatusFilter(admin.SimpleListFilter):
    title = "Online status"
    parameter_name = "status"

    def lookups(self, request, model_admin):
        return (("online", "online"), ("offline", "offline"))

    def queryset(self, request, queryset):
        if self.value() == "online":
            return queryset.filter(
                last_alive_message__gt=get_time() - timezone.timedelta(seconds=3)
            )
        if self.value() == "offline":
            return queryset.filter(
                last_alive_message__lte=get_time() - timezone.timedelta(seconds=3)
            )
        return queryset
class LevelFilter(admin.SimpleListFilter):
    title = "Level"
    parameter_name = "level"

    def lookups(self, request, model_admin):
        return [[x, x] for x in range(0, 11)]

    def queryset(self, request, queryset):
        v = self.value()
        if v is not None:
            v = int(v)
            return queryset.filter(xp__gte=LEVELS_XPS()[v], xp__lte=LEVELS_XPS()[v+1])
        return queryset

class PartFilter(admin.SimpleListFilter):
    title = "Part"
    parameter_name = "part"

    def lookups(self, request, model_admin):
        return [[x, x] for x in range(1, 11)]

    def queryset(self, request, queryset):
        v = self.value()
        if v is not None:
            ids = []
            for obj in queryset:
                if str(obj.level_reached)[1] == str(int(v)-1):
                    ids.append(obj.pk)
            return queryset.filter(id__in=ids)
        return queryset

def give_xp(model, request, queryset):
    for obj in queryset:
        obj.give_xp(2000)
        obj.save()


from rangefilter.filter import DateRangeFilter
from django.utils.html import mark_safe
from django.urls import reverse, path
from django.http import JsonResponse
from django.db.models.functions import TruncDay
from django.db.models import Count

@admin.register(User)
class UserAdmin(admin.ModelAdmin, ExportCsvMixin):
    def get_urls(self):
        urls = super().get_urls()
        extra_urls = [
            path("installs_chart_data/", self.admin_site.admin_view(self.installs_chart_data_endpoint)),
            path("online_chart_data/", self.admin_site.admin_view(self.online_chart_data_endpoint)),
            path("stores_chart_data/", self.admin_site.admin_view(self.stores_chart_data_endpoint)),
        ]
        return extra_urls + urls

    def installs_chart_data_endpoint(self, request):
        chart_data = self.installs_chart_data()
        return JsonResponse(list(chart_data), safe=False)
    
    def online_chart_data_endpoint(self, request):
        chart_data = self.online_chart_data()
        return JsonResponse(list(chart_data), safe=False)
    
    def stores_chart_data_endpoint(self, request):
        chart_data = self.stores_chart_data()
        return JsonResponse(list(chart_data), safe=False)

    def installs_chart_data(self):
        return []
        return (
            User.objects.filter(is_bot=False, logged_in=True).annotate(x=TruncDay("date_joined"))
            .values("x")
            .annotate(y=Count("id"))
            .order_by("-x")
        )
    def online_chart_data(self):
        return []
        return (
            PlayRecord.objects.all().annotate(x=TruncDay("date"))
            .values("x")
            .annotate(y=Count("id"))
            .order_by("-x")
        )
    def stores_chart_data(self):
        return [[]]
        return [
            [User.objects.filter(store__icontains="bazaar").count()],
            [User.objects.filter(store__icontains="google").count()],
            [User.objects.filter(store__icontains="apple").count()]
        ]
    
    list_display = (
        "_username",
        "coins",
        "_xp",
        "_level_reached",
        "date_joined",
        "last_alive_message",
        "_parent",
        "device"
    )
    list_filter = (
        OnlineStatusFilter,
        LevelFilter,
        PartFilter,
        "marked_for_notification",
        "is_bot",
        "date_joined",
        ("date_joined", DateRangeFilter),
    )
    readonly_fields = ["childs_list", "level_reached_detail"]
    search_fields = ["username"]
    actions = ["export_as_csv", give_xp, "mark_for_notification", "unmark_for_notification"]

    def _xp(self, obj):
        lvl, xp = obj.get_level()
        return '{} + {}xp'.format(lvl, xp)
    _xp.admin_order_field = 'xp'
    def _level_reached(self, obj):
        lvl = str(obj.level_reached)
        return 'S:{} P:{}: L:{}'.format(lvl[0], int(lvl[1]) + 1, int(lvl[2:]))
    def mark_for_notification(self, request, queryset):
        queryset.update(marked_for_notification=True)
    def unmark_for_notification(self, request, queryset):
        queryset.update(marked_for_notification=False)
    def device(self, obj):
        if obj.is_bot:
            return 'BOT'
        if '-' in obj.device_id:
            return 'iOS'
        return 'Android'
    def get_queryset(self, request):
        self.request = request
        self.query_set_cached = super().get_queryset(request)
        return self.query_set_cached
    
    def _username(self, obj):
        qs = (*self.query_set_cached, )
        return str(len(qs) - qs.index(obj)) + '. ' + obj.username
    @mark_safe
    def _parent(self, obj):
        if not obj.parent:
            return "-"
        return '<a href="{}">{}</a>'.format(
            reverse(
                "admin:%s_%s_change"
                % (obj.parent._meta.app_label, obj.parent._meta.model_name),
                args=[obj.parent.id],
            ),
            obj.parent.username,
        )

    @mark_safe
    def level_reached_detail(self, obj):
        lvl = str(obj.level_reached)
        return "Season : {}<br>Part : {}<br>Level : {}".format(
            lvl[0], int(lvl[1]) + 1, int(lvl[2:])
        )

    def childs_list(self, obj):
        return format_html(
            "".join(
                [format_html("<p><b>{}</b></p>", child) for child in obj.childs.all()]
            )
        )


class TicketMessageAdmin(admin.TabularInline):
    model = TicketMessage
    extra = 1


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("category", "user", "title", "state")
    list_filter = ("state", "category")
    inlines = [TicketMessageAdmin]


@admin.register(LotteryUser)
class LotteryUserAdmin(admin.ModelAdmin):
    list_display = ("user", "lottery", "copouns")
    list_filter = ("user",)


@admin.register(Lottery)
class LotteryAdmin(admin.ModelAdmin):
    list_display = ("name", "num_users")

    def num_users(self, obj):
        return obj.users.count()


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ("user", "lottery", "created")
    list_filter = ("user", "lottery")

    search_fields = ("user__username",)


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("season", "part", "level_id", "extra_letters")


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ("state", "tournoment")


@admin.register(LevelTrack)
class LevelTrackAdmin(admin.ModelAdmin):
    list_display = ("user", "level_id", "help_used", "time_format")
    list_filter = ("level__level_id", "user")

    def time_format(self, obj):
        return round(obj.time)

    def level_id(self, obj):
        return round(obj.level.level_id)


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ["user", "code", "perminent"]

    list_filter = ["perminent"]

@admin.register(PlayRecord)
class PlayRecordAdmin(admin.ModelAdmin):
    list_display = ["player", "date", "played_time"]
