from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Count
from .models import Ticket, TicketUpdate, CATEGORIA_CHOICES, TicketReadStatus, TicketRecording
from .forms import (
    TicketForm, TicketStatusForm, CustomerRegistrationForm,
    TicketReplyForm, TicketFeedbackForm, TicketRecordingUploadForm
)
from . import emails
from . import utils

TICKETS_PER_PAGE = 25

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registrazione completata! Benvenuto su Afterbit.')
            request.session.pop('captcha_question', None)
            request.session.pop('captcha_answer', None)
            return redirect('dashboard')
        else:
            messages.error(request, 'Controlla i campi evidenziati e riprova.')
            utils.generate_captcha(request)
            form.fields['captcha'].label = f"Verifica di sicurezza: quanto fa {request.session.get('captcha_question')}?"
    else:
        utils.generate_captcha(request)
        form = CustomerRegistrationForm(request=request)

    return render(request, 'auth/register.html', {'form': form})

def ticket_search(request):
    code = request.GET.get('code', '').strip()
    verify_contact = request.GET.get('verify_contact', '').strip()
    ticket = None
    searched = bool(code or verify_contact)
    error_message = None

    if searched:
        if not code or not verify_contact:
            error_message = (
                "Per tutelare la privacy e la sicurezza delle informazioni, "
                "è necessario inserire sia il codice del ticket che l'email, "
                "il nome azienda/referente o il numero di telefono associato."
            )
        else:
            clean_code = code.lstrip('#')
            candidate = None
            if clean_code.isdigit():
                candidate = Ticket.objects.filter(Q(id=int(clean_code)) | Q(codice_riferimento__iexact=code)).first()
            else:
                candidate = Ticket.objects.filter(codice_riferimento__iexact=code).first()

            if candidate and utils.verify_ticket_ownership(candidate, verify_contact):
                ticket = candidate
            else:
                error_message = (
                    "Nessun ticket trovato o dati di verifica non corrispondenti. "
                    "Assicurati di aver inserito correttamente il codice del ticket e il dato di contatto "
                    "(email aziendale, nominativo referente/azienda o telefono) associato alla richiesta."
                )

    return render(request, 'ticket_search.html', {
        'ticket': ticket,
        'searched': searched,
        'code': code,
        'verify_contact': verify_contact,
        'error_message': error_message,
    })

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remember_me = request.POST.get('remember_me')

        user = authenticate(request, username=login_input, password=password)
        if user is None and '@' in login_input:
            matched_user = User.objects.filter(email__iexact=login_input).first()
            if matched_user:
                user = authenticate(request, username=matched_user.username, password=password)

        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            return redirect('dashboard')
        else:
            messages.error(request, 'Credenziali non valide.')

        return render(request, 'auth/login.html', {'username': login_input})

    return render(request, 'auth/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    base_qs = Ticket.objects.all() if request.user.is_staff else Ticket.objects.filter(created_by=request.user)

    # Calculate Tab Counts
    open_count = base_qs.filter(status__in=['open', 'in_progress']).count()
    closed_count = base_qs.filter(status__in=['resolved', 'closed']).count()
    total_count = base_qs.count()

    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    categoria_filter = request.GET.get('categoria', '').strip()
    per_page = int(request.GET.get('per_page', TICKETS_PER_PAGE))

    # Read tab filter (default: 'open' unless status filter specifies closed status)
    active_tab = request.GET.get('tab', '').strip()
    if not active_tab:
        if status_filter in ['resolved', 'closed']:
            active_tab = 'closed'
        elif status_filter in ['open', 'in_progress']:
            active_tab = 'open'
        elif status_filter:
            active_tab = 'all'
        else:
            active_tab = 'open'

    tickets_qs = base_qs

    if active_tab == 'open':
        tickets_qs = tickets_qs.filter(status__in=['open', 'in_progress'])
    elif active_tab == 'closed':
        tickets_qs = tickets_qs.filter(status__in=['resolved', 'closed'])
    # active_tab == 'all' shows all

    if q:
        clean_q = q.replace('#', '')
        tickets_qs = tickets_qs.filter(
            Q(id__icontains=clean_q) |
            Q(codice_riferimento__icontains=q) |
            Q(title__icontains=q) |
            Q(description__icontains=q) |
            Q(referente__icontains=q) |
            Q(servizio__icontains=q) |
            Q(categoria__icontains=q)
        )

    if status_filter:
        tickets_qs = tickets_qs.filter(status=status_filter)

    if categoria_filter:
        tickets_qs = tickets_qs.filter(categoria=categoria_filter)

    tipo_intervento_filter = request.GET.get('tipo_intervento', '').strip()
    if tipo_intervento_filter:
        tickets_qs = tickets_qs.filter(tipo_intervento=tipo_intervento_filter)

    # Annotate comments/updates count
    tickets_qs = tickets_qs.annotate(num_updates=Count('updates')).select_related('created_by', 'assigned_to')

    # Sorting logic
    sort_by = request.GET.get('sort', 'created_at').strip()
    order = request.GET.get('order', 'desc').strip()
    if order not in ['asc', 'desc']:
        order = 'desc'

    sort_field_map = {
        'id': 'id',
        'title': 'title',
        'servizio': 'servizio',
        'categoria': 'categoria',
        'user': 'created_by__username',
        'created_at': 'created_at',
        'status': 'status',
        'num_updates': 'num_updates',
    }

    db_sort_field = sort_field_map.get(sort_by, 'created_at')
    order_expression = db_sort_field if order == 'asc' else f"-{db_sort_field}"
    tickets_qs = tickets_qs.order_by(order_expression)

    paginator = Paginator(tickets_qs, per_page)
    page_number = request.GET.get('page')
    tickets = paginator.get_page(page_number)

    # Calcolo stato di lettura stile Outlook (richieste da gestire) per i ticket della pagina corrente
    page_ticket_ids = [t.id for t in tickets.object_list]
    read_map = {
        rs.ticket_id: rs.last_read_at
        for rs in TicketReadStatus.objects.filter(user=request.user, ticket_id__in=page_ticket_ids)
    }

    latest_updates = {}
    for upd in TicketUpdate.objects.filter(ticket_id__in=page_ticket_ids).select_related('author').order_by('created_at'):
        latest_updates[upd.ticket_id] = upd

    for t in tickets.object_list:
        latest_upd = latest_updates.get(t.id)
        if latest_upd:
            latest_time = latest_upd.created_at
            latest_author = latest_upd.author
        else:
            latest_time = t.last_activity_at or t.created_at
            latest_author = t.created_by

        if request.user.is_staff:
            # Lato Staff: i ticket da gestire (prima di essere assegnati o di ricevere risposta)
            # devono rimanere in grassetto (meglio visibili tipo outlook).
            if t.status in ['resolved', 'closed']:
                # Se risolto/chiuso, è da gestire solo se il cliente ha inviato una nuova replica dopo la chiusura
                if latest_author and not latest_author.is_staff:
                    t.is_unread = True
                else:
                    t.is_unread = False
            else:
                # Ticket aperti o in lavorazione:
                # Rimane in grassetto se non è ancora assegnato, se è in stato 'open',
                # o se l'ultimo messaggio è del cliente (in attesa di risposta dello staff)
                if not t.assigned_to or t.status == 'open':
                    t.is_unread = True
                elif not latest_author or not latest_author.is_staff:
                    t.is_unread = True
                else:
                    # Assegnato, in lavorazione e con ultima risposta dello staff
                    t.is_unread = False
        else:
            # Lato Cliente: in grassetto se c'è una risposta/aggiornamento dello staff non ancora letto
            if latest_author and latest_author.is_staff:
                last_read = read_map.get(t.id)
                if not last_read or last_read < latest_time:
                    t.is_unread = True
                else:
                    t.is_unread = False
            else:
                t.is_unread = False

    return render(request, 'tickets/dashboard.html', {
        'tickets': tickets,
        'q': q,
        'active_tab': active_tab,
        'open_count': open_count,
        'closed_count': closed_count,
        'total_count': total_count,
        'selected_status': status_filter,
        'selected_categoria': categoria_filter,
        'status_choices': Ticket.STATUS_CHOICES,
        'categoria_choices': CATEGORIA_CHOICES,
        'per_page': per_page,
        'sort_by': sort_by,
        'order': order,
    })

def faq(request):
    return render(request, 'faq.html')

@login_required
def create_ticket(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user

            client_ip = utils.get_client_ip(request)
            ticket.created_from_ip = client_ip
            ticket.created_from_location = utils.get_ip_location(client_ip)
            ticket.last_activity_at = timezone.now()

            ticket.save()
            ticket.genera_codice_riferimento()
            ticket.save()

            TicketReadStatus.objects.update_or_create(
                ticket=ticket,
                user=request.user,
                defaults={'last_read_at': timezone.now()}
            )

            emails.notifica_nuovo_ticket_staff(ticket)
            emails.ricevuta_apertura_ticket_cliente(ticket)

            messages.success(request, f'Ticket #{ticket.id} ({ticket.codice_riferimento}) aperto con successo!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Controlla i campi evidenziati e riprova.')
    else:
        initial_referente = request.user.get_full_name() or request.user.username
        form = TicketForm(initial={'referente': initial_referente})

    return render(request, 'tickets/create_ticket.html', {'form': form})

@login_required
def ticket_detail(request, ticket_id):
    if request.user.is_staff:
        ticket = get_object_or_404(Ticket, id=ticket_id)
    else:
        ticket = get_object_or_404(Ticket, id=ticket_id, created_by=request.user)

    # Segna il ticket come visualizzato dall'utente corrente
    TicketReadStatus.objects.update_or_create(
        ticket=ticket,
        user=request.user,
        defaults={'last_read_at': timezone.now()}
    )

    status_form = None
    if request.user.is_staff:
        status_form = TicketStatusForm(instance=ticket)
    reply_form = TicketReplyForm()
    feedback_form = TicketFeedbackForm()

    if request.method == 'POST':
        action = request.POST.get('action', '').strip()

        # 1. Invio Valutazione / Feedback (1-5 stelle) da parte del cliente
        if action == 'submit_feedback' or 'rating' in request.POST:
            if ticket.created_by == request.user and ticket.status in ['resolved', 'closed']:
                feedback_form = TicketFeedbackForm(request.POST)
                if feedback_form.is_valid():
                    ticket.rating = int(feedback_form.cleaned_data['rating'])
                    ticket.rating_comment = feedback_form.cleaned_data.get('rating_comment', '').strip()
                    ticket.rated_at = timezone.now()
                    ticket.save()
                    messages.success(request, 'Grazie! La tua valutazione a 5 stelle è stata registrata con successo.')
                    return redirect('ticket_detail', ticket_id=ticket.id)
                else:
                    messages.error(request, 'Seleziona una valutazione da 1 a 5 stelle prima di inviare.')
            else:
                messages.error(request, 'Non è possibile rilasciare un feedback per questo ticket.')

        # 2. Invio Replica / Messaggio con eventuale allegato
        elif action == 'reply':
            reply_form = TicketReplyForm(request.POST, request.FILES)
            if reply_form.is_valid():
                update = reply_form.save(commit=False)
                update.ticket = ticket
                update.author = request.user
                update.save()

                ticket.last_activity_at = timezone.now()

                if not request.user.is_staff:
                    # Se il cliente risponde a un ticket risolto/chiuso, lo riapriamo
                    if ticket.status in ['resolved', 'closed']:
                        ticket.status = 'in_progress'
                    ticket.save()
                    emails.notifica_risposta_cliente(ticket, update)
                    messages.success(request, 'Il tuo messaggio e gli allegati sono stati inviati allo staff!')
                else:
                    ticket.save()
                    emails.aggiornamento_stato_ticket_cliente(ticket, ticket.status, update.note)
                    messages.success(request, 'Risposta inviata ed email recapitata al cliente con successo!')

                return redirect('ticket_detail', ticket_id=ticket.id)
            else:
                messages.error(request, 'Impossibile inviare la risposta. Controlla il messaggio e l\'allegato.')

        # 3. Gestione Stato e Risposta da parte dello Staff
        elif request.user.is_staff and ('status' in request.POST or 'assigned_to' in request.POST or action in ['save_only', 'save_and_notify']):
            stato_precedente = ticket.status
            status_form = TicketStatusForm(request.POST, instance=ticket)
            if status_form.is_valid():
                updated_ticket = status_form.save(commit=False)
                stato_cambiato = updated_ticket.status != stato_precedente

                if updated_ticket.assigned_to and not updated_ticket.codice_riferimento:
                    updated_ticket.save()
                    updated_ticket.genera_codice_riferimento()

                updated_ticket.last_activity_at = timezone.now()
                updated_ticket.save()

                note_text = request.POST.get('note', '').strip()
                attachment_file = request.FILES.get('attachment')
                if note_text or attachment_file:
                    TicketUpdate.objects.create(
                        ticket=updated_ticket,
                        author=request.user,
                        note=note_text or "Aggiornamento pratiche e lavorazione ticket.",
                        attachment=attachment_file
                    )

                send_to_customer = (action == 'save_and_notify')

                if send_to_customer and (stato_cambiato or note_text or attachment_file):
                    if updated_ticket.status == 'closed' and stato_cambiato:
                        emails.chiusura_ticket_cliente(updated_ticket, note_text or None)
                    else:
                        emails.aggiornamento_stato_ticket_cliente(updated_ticket, stato_precedente, note_text or None)
                    messages.success(request, f'Ticket #{ticket.id} salvato ed email inviata al cliente!')
                else:
                    messages.success(request, f'Ticket #{ticket.id} aggiornato con successo (modifica interna).')

                return redirect('ticket_detail', ticket_id=ticket.id)
            else:
                messages.error(request, 'Impossibile aggiornare il ticket, controlla i campi.')

        # 4. Chiusura del Ticket da parte del Cliente in qualsiasi momento
        elif action == 'close_by_customer':
            if ticket.created_by == request.user and ticket.status != 'closed':
                ticket.status = 'closed'
                ticket.last_activity_at = timezone.now()
                ticket.save()

                close_reason = request.POST.get('close_reason', '').strip()
                note_text = "Ticket chiuso direttamente dal richiedente."
                if close_reason:
                    note_text += f" Motivazione: {close_reason}"

                TicketUpdate.objects.create(
                    ticket=ticket,
                    author=request.user,
                    note=note_text
                )
                emails.chiusura_ticket_cliente(ticket, nota=note_text)
                messages.success(request, 'Ticket chiuso con successo! Se desideri, puoi lasciare una valutazione del servizio qui sotto.')
                return redirect('ticket_detail', ticket_id=ticket.id)
            else:
                messages.error(request, 'Questo ticket è già chiuso o non hai i permessi per chiuderlo.')

        # 5. Caricamento / Salvataggio Registrazione Audio/Video (USO ESCLUSIVO STAFF)
        elif action == 'upload_recording' and request.user.is_staff:
            recording_form = TicketRecordingUploadForm(request.POST, request.FILES)
            if recording_form.is_valid():
                rec = recording_form.save(commit=False)
                rec.ticket = ticket
                rec.author = request.user
                rec.status = 'pending'

                # Se non c'è un file allegato da input ma c'è la registrazione live (audio o video) in base64
                base64_data = recording_form.cleaned_data.get('media_blob_base64') or recording_form.cleaned_data.get('audio_blob_base64')
                if not rec.recording_file and base64_data:
                    import base64
                    from django.core.files.base import ContentFile
                    if ';base64,' in base64_data:
                        header, imgstr = base64_data.split(';base64,')
                        if 'video' in header:
                            rec.media_type = 'video'
                    else:
                        imgstr = base64_data

                    file_bytes = base64.b64decode(imgstr)
                    prefix = 'registrazione_video' if rec.media_type == 'video' else 'registrazione_vocale'
                    filename = f"{prefix}_{int(timezone.now().timestamp())}.webm"
                    rec.recording_file.save(filename, ContentFile(file_bytes), save=False)

                rec.save()

                # Accoda la trascrizione automatica locale in background
                try:
                    from .service_transcription import queue_recording_transcription
                    queue_recording_transcription(rec.id)
                except Exception as e:
                    pass

                messages.success(request, f'Registrazione interna "{rec.title or rec.get_media_type_display()}" allegata! Elaborazione locale avviata.')
                return redirect('ticket_detail', ticket_id=ticket.id)
            else:
                error_msg = 'Errore nel caricamento della registrazione.'
                if recording_form.errors:
                    first_err = next(iter(recording_form.errors.values()))[0]
                    error_msg += f" {first_err}"
                messages.error(request, error_msg)

    updates = ticket.updates.select_related('author').all()

    # Le registrazioni interne sono caricate SOLO se l'utente è staff
    staff_recordings = []
    recording_form = None
    if request.user.is_staff:
        staff_recordings = ticket.recordings.select_related('author').all()
        recording_form = TicketRecordingUploadForm()

    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket,
        'status_form': status_form,
        'reply_form': reply_form,
        'feedback_form': feedback_form,
        'updates': updates,
        'staff_recordings': staff_recordings,
        'recording_form': recording_form,
    })

def privacy_policy(request):
    return render(request, 'privacy_policy.html')
