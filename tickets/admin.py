from django.contrib import admin
from .models import Ticket, UserProfile


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'tipo_intervento', 'status', 'priority', 'codice_riferimento', 'created_by', 'assigned_to', 'created_at']
    list_filter = ['status', 'priority', 'tipo_intervento']
    search_fields = ['title', 'description', 'codice_riferimento', 'created_from_ip', 'created_from_location']
    readonly_fields = ['created_from_ip', 'created_from_location']



@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone']
