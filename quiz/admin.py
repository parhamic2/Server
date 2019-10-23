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
    SendGroupNotification
)
from .tournoment import Tournoment, TournomentUser
from django.utils import timezone
from .utils import get_time
from django.http import HttpResponse
from django.utils.html import format_html
import csv

admin.site.register(Message)
admin.site.register(SendGroupNotification)
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


def give_xp(model, request, queryset):
    for obj in queryset:
        obj.give_xp(2000)
        obj.save()


from rangefilter.filter import DateRangeFilter
from django.utils.html import mark_safe
from django.urls import reverse, path
from django.http import JsonResponse


@admin.register(User)
class UserAdmin(admin.ModelAdmin, ExportCsvMixin):
    def get_urls(self):
        urls = super().get_urls()
        extra_urls = [
            path("chart_data/", self.admin_site.admin_view(self.chart_data_endpoint))
        ]
        return extra_urls + urls

    def chart_data_endpoint(self, request):
        chart_data = self.chart_data()
        return JsonResponse(list(chart_data), safe=False)

    def chart_data(self):
        return (
            User.objects.annotate(x=TruncDay("date_joined"))
            .values("x")
            .annotate(y=Count("id"))
            .order_by("-x")
        )
    
    list_display = (
        "_username",
        "coins",
        "xp",
        "date_joined",
        "last_alive_message",
        "_parent",
        "device"
    )
    list_filter = (
        OnlineStatusFilter,
        "is_bot",
        "date_joined",
        ("date_joined", DateRangeFilter),
    )
    readonly_fields = ["childs_list", "level_reached_detail"]
    search_fields = ["username"]
    actions = ["export_as_csv", give_xp]
    def device(self, obj):
        if obj.is_bot:
            return 'BOT'
        if '-' in obj.device_id:
            return 'iOS'
        return 'Android'
    def get_queryset(self, request):
        self.request = request      
        return super().get_queryset(request)
    
    def _username(self, obj):
        qs = (*self.get_queryset(self.request), )
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

