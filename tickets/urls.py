from django.urls import path
from . import views  # import relativo: evita la collisione con django.contrib.auth
# NB: se la cartella della tua app si chiama letteralmente "auth", ti consiglio
# comunque di rinominarla (es. "helpdesk" o "tickets") per evitare ambiguita'
# con l'app "django.contrib.auth" gia' presente in INSTALLED_APPS.

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("login/", views.user_login, name="login"),
    path("registrati/", views.register, name="register"),
    path("logout/", views.user_logout, name="logout"),
    path("ticket/nuovo/", views.create_ticket, name="create_ticket"),
    path("ticket/cerca/", views.ticket_search, name="ticket_search"),
    path("ticket/<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
    path("faq/", views.faq, name="faq"),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
]
