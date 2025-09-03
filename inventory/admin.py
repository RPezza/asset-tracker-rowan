from django.contrib import admin

from .forms import BookingForm
from .models import Asset, Booking, UserMessage


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "available")
    search_fields = ("name", "category")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingForm
    list_display = ("asset", "start_date", "end_date", "purpose", "user")
    list_filter = ("start_date", "end_date", "asset")
    search_fields = ("asset__name", "user__username", "purpose")
    ordering = ("-start_date",)


@admin.register(UserMessage)
class UserMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "timestamp", "message")
    search_fields = ("name", "email", "subject", "message")
