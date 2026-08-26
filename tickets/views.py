from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Ticket
from .forms import TicketForm, TicketStatusForm, CustomerRegistrationForm
from . import emails
from . import utils

TICKETS_PER_PAGE = 15


def home(request):
    """Pagina pubblica di benvenuto."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def register(request):
    """Registrazione pubblica self-service per nuovi clienti."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registrazione completata! Benvenuto su Afterbit.')
            # Rimuove il captcha risolto dalla sessione per sicurezza
            request.session.pop('captcha_question', None)
            request.session.pop('captcha_answer', None)
            return redirect('dashboard')
        else:
            messages.error(request, 'Controlla i campi evidenziati e riprova.')
            # Rigenera il captcha in caso di fallimento
            utils.generate_captcha(request)
            form.fields['captcha'].label = f"Verifica di sicurezza: quanto fa {request.session.get('captcha_question')}?"
    else:
        utils.generate_captcha(request)
        form = CustomerRegistrationForm(request=request)

    return render(request, 'auth/register.html', {'form': form})


def ticket_search(request):
    """Ricerca pubblica di un ticket tramite il suo codice (ID)."""
    code = request.GET.get('code', '').strip()
    ticket = None
    searched = bool(code)

    if code:
        # Il codice atteso e' l'ID numerico, eventualmente preceduto da '#'
        clean_code = code.lstrip('#')
        if clean_code.isdigit():
            ticket = Ticket.objects.filter(id=int(clean_code)).first()

    return render(request, 'ticket_search.html', {
        'ticket': ticket,
        'searched': searched,
        'code': code,
    })


def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            return redirect('dashboard')
        else:
            messages.error(request, 'Credenziali non valide.')

        # Ripopola lo username inserito (mai la password) cosi' l'utente
        # non deve riscrivere tutto dopo un errore
        return render(request, 'auth/login.html', {'username': username})

    return render(request, 'auth/login.html')


def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    if request.user.is_staff:
        tickets_qs = Ticket.objects.all()
    else:
        tickets_qs = Ticket.objects.filter(created_by=request.user)

    paginator = Paginator(tickets_qs, TICKETS_PER_PAGE)
    page_number = request.GET.get('page')
    tickets = paginator.get_page(page_number)

    return render(request, 'tickets/dashboard.html', {'tickets': tickets})


@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user

            # Geolocalizzazione dell'IP del cliente
            client_ip = utils.get_client_ip(request)
            ticket.created_from_ip = client_ip
            ticket.created_from_location = utils.get_ip_location(client_ip)

            ticket.save()

            emails.notifica_nuovo_ticket_staff(ticket)
            emails.ricevuta_apertura_ticket_cliente(ticket)

            messages.success(request, 'Ticket inviato con successo! Riceverai una email di conferma.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Controlla i campi evidenziati e riprova.')
    else:
        form = TicketForm()

    return render(request, 'tickets/create_ticket.html', {'form': form})


@login_required
def ticket_detail(request, ticket_id):
    """Dettaglio ticket. Lo staff puo' anche aggiornare stato/assegnazione."""
    if request.user.is_staff:
        ticket = get_object_or_404(Ticket, id=ticket_id)
    else:
        # Un utente normale vede solo i propri ticket
        ticket = get_object_or_404(Ticket, id=ticket_id, created_by=request.user)

    status_form = None
    if request.user.is_staff:
        if request.method == 'POST':
            stato_precedente = ticket.status  # va catturato PRIMA di validare il form
            status_form = TicketStatusForm(request.POST, instance=ticket)
            if status_form.is_valid():
                updated_ticket = status_form.save(commit=False)
                stato_cambiato = updated_ticket.status != stato_precedente

                # Prima volta che viene assegnato a qualcuno -> genera il codice di richiamo
                if updated_ticket.assigned_to and not updated_ticket.codice_riferimento:
                    updated_ticket.save()  # serve l'id se il ticket non l'aveva ancora
                    updated_ticket.genera_codice_riferimento()

                updated_ticket.last_activity_at = timezone.now()
                updated_ticket.save()

                if stato_cambiato:
                    if updated_ticket.status == 'closed':
                        emails.chiusura_ticket_cliente(updated_ticket)
                    else:
                        emails.aggiornamento_stato_ticket_cliente(updated_ticket, stato_precedente)

                messages.success(request, 'Ticket aggiornato con successo.')
                return redirect('ticket_detail', ticket_id=ticket.id)
            else:
                messages.error(request, 'Impossibile aggiornare il ticket, controlla i campi.')
        else:
            status_form = TicketStatusForm(instance=ticket)

    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket,
        'status_form': status_form,
    })


def privacy_policy(request):
    """Visualizza la pagina informativa della Privacy Policy."""
    return render(request, 'privacy_policy.html')
