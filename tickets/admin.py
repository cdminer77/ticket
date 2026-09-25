# pyright: reportMissingModuleSource=false
from django.contrib import admin  # type: ignore[import-not-found]
from .models import Ticket, UserProfile, TicketUpdate, TicketReadStatus, TicketRecording


class TicketUpdateInline(admin.TabularInline):
    model = TicketUpdate
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'referente', 'tipo_intervento', 'status', 'priority', 'codice_riferimento', 'created_by', 'assigned_to', 'created_at']
    list_filter = ['status', 'priority', 'tipo_intervento']
    search_fields = ['title', 'referente', 'description', 'codice_riferimento', 'created_from_ip', 'created_from_location']
    readonly_fields = ['created_from_ip', 'created_from_location']
    inlines = [TicketUpdateInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone']


@admin.register(TicketUpdate)
class TicketUpdateAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['note']


@admin.register(TicketReadStatus)
class TicketReadStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'user', 'last_read_at']
    list_filter = ['last_read_at']
    search_fields = ['ticket__id', 'ticket__title', 'user__username']


@admin.register(TicketRecording)
class TicketRecordingAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'media_type', 'title', 'author', 'status', 'created_at']
    list_filter = ['media_type', 'status', 'created_at']
    search_fields = ['ticket__id', 'ticket__title', 'title', 'transcript', 'extracted_notes']
    readonly_fields = ['created_at', 'updated_at']

