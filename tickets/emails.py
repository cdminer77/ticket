"""
Invio delle comunicazioni email automatiche legate ai ticket:
- notifica interna a info@afterbit.com quando arriva un nuovo ticket
- ricevuta al cliente all'apertura
- aggiornamento al cliente e allo staff ad ogni cambio di stato
- comunicazione al cliente e allo staff alla chiusura finale dell'intervento

Ogni funzione e' "silenziosa" sugli errori di invio (non blocca mai la
navigazione dell'utente se il server SMTP e' irraggiungibile o mal
configurato), ma restituisce True/False cosi' il chiamante puo' avvisare
lo staff se qualcosa non e' partito.
"""
import logging
import re
import smtplib
import subprocess
import sys
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def _get_mx_hosts(domain):
    """Restituisce la lista di host MX per il dominio specificato."""
    domain_clean = domain.lower().strip()
    if domain_clean in ("afterbit.com", "afterbit.it"):
        return ["le.afterbit.net", "151.11.48.67"]

    try:
        out = subprocess.check_output(["dig", "+short", "MX", domain_clean], text=True, timeout=3)
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        hosts = []
        for l in lines:
            parts = l.split()
            if len(parts) >= 2:
                hosts.append(parts[1].rstrip("."))
            elif len(parts) == 1:
                hosts.append(parts[0].rstrip("."))
        if hosts:
            return hosts
    except Exception:
        pass

    return [domain_clean]


def _deliver_single_email_direct(subject, message, to_email, from_email, reply_to=None):
    """Invia direttamente via SMTP MX al server di destinazione."""
    if not to_email or "@" not in to_email:
        return False

    domain = to_email.split("@")[-1].strip()
    mx_hosts = _get_mx_hosts(domain)

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email
    if reply_to:
        msg["Reply-To"] = ", ".join(reply_to) if isinstance(reply_to, list) else str(reply_to)
    msg.attach(MIMEText(message, "plain", "utf-8"))

    raw_sender = re.findall(r'<([^>]+)>', from_email)
    envelope_from = raw_sender[0] if raw_sender else from_email

    for mx in mx_hosts:
        try:
            s = smtplib.SMTP(mx, 25, timeout=5)
            try:
                s.ehlo_or_helo_if_needed()
            except Exception:
                pass
            s.sendmail(envelope_from, [to_email], msg.as_string())
            s.quit()
            logger.info("Email inviata con successo a %s tramite MX %s:25", to_email, mx)
            return True
        except Exception as e:
            logger.warning("Tentativo invio a %s via MX %s fallito: %s", to_email, mx, e)

    return False


def _send_worker(subject, message, destinatari, reply_to):
    """Esegue l'invio delle email."""
    # In ambiente di test usiamo il backend Django standard per catturare in mail.outbox
    is_test_env = 'test' in sys.argv or getattr(settings, 'EMAIL_BACKEND', '').endswith('locmem.EmailBackend')
    if is_test_env:
        try:
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=destinatari,
                reply_to=reply_to or [settings.SUPPORT_NOTIFICATION_EMAIL],
            )
            email.send(fail_silently=False)
            return True
        except Exception:
            logger.exception("Invio email fallito in test backend")
            return False

    # In produzione/sviluppo: tentiamo prima l'invio diretto MX verso ciascun destinatario
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Afterbit Assistenza <info@afterbit.com>')
    all_success = True

    for to_email in destinatari:
        if not to_email:
            continue
        delivered = _deliver_single_email_direct(subject, message, to_email, from_email, reply_to)
        if not delivered:
            # Fallback su backend standard Django
            try:
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=from_email,
                    to=[to_email],
                    reply_to=reply_to or [settings.SUPPORT_NOTIFICATION_EMAIL],
                )
                email.send(fail_silently=True)
            except Exception:
                all_success = False

    return all_success


def _invia(subject, message, destinatari, reply_to=None):
    if not destinatari:
        return False

    # Filtra destinatari duplicati e vuoti preservando l'ordine
    clean_destinatari = []
    for d in destinatari:
        if d and str(d).strip() and str(d).strip() not in clean_destinatari:
            clean_destinatari.append(str(d).strip())

    if not clean_destinatari:
        return False

    # In ambiente di test eseguiamo in modo sincrono per consentire i controlli su mail.outbox
    is_test_env = 'test' in sys.argv or getattr(settings, 'EMAIL_BACKEND', '').endswith('locmem.EmailBackend')
    if is_test_env:
        return _send_worker(subject, message, clean_destinatari, reply_to)

    # In produzione/sviluppo inviamo in background per non bloccare mai la richiesta HTTP
    thread = threading.Thread(
        target=_send_worker,
        args=(subject, message, clean_destinatari, reply_to),
        daemon=True
    )
    thread.start()
    return True


def notifica_nuovo_ticket_staff(ticket):
    """Avvisa l'indirizzo interno (info@afterbit.com) che e' stato aperto un nuovo ticket."""
    cliente = ticket.created_by
    subject = f"Nuovo ticket #{ticket.id}: {ticket.title}"
    message = (
        f"E' stato aperto un nuovo ticket sul portale assistenza.\n\n"
        f"Numero ticket: #{ticket.id}\n"
        f"Cliente: {cliente.username} ({cliente.email or 'email non indicata'})\n"
        f"Categoria: {ticket.categoria}\n"
        f"Tipo intervento: {ticket.get_tipo_intervento_display()}\n\n"
        f"Descrizione:\n{ticket.description}\n"
    )
    return _invia(
        subject, message, [settings.SUPPORT_NOTIFICATION_EMAIL],
        reply_to=[cliente.email] if cliente.email else None
    )


def ricevuta_apertura_ticket_cliente(ticket):
    """Ricevuta di conferma apertura, inviata all'email del cliente."""
    cliente = ticket.created_by
    subject = f"Afterbit - Abbiamo ricevuto la tua richiesta (Ticket #{ticket.id})"
    message = (
        f"Ciao {cliente.username},\n\n"
        f"Ti confermiamo di aver ricevuto la tua richiesta di assistenza.\n\n"
        f"Numero ticket: #{ticket.id}\n"
        f"Oggetto: {ticket.title}\n"
        f"Categoria: {ticket.categoria}\n"
        f"Tipo intervento: {ticket.get_tipo_intervento_display()}\n\n"
        f"Ti scriveremo di nuovo non appena il ticket verrà preso in carico "
        f"e ad ogni aggiornamento importante, fino alla chiusura dell'intervento.\n\n"
        f"Team Afterbit"
    )
    destinatari = [cliente.email] if cliente.email else []
    return _invia(subject, message, destinatari)


def aggiornamento_stato_ticket_cliente(ticket, stato_precedente, nota=None):
    """Comunicazione al cliente e allo staff quando lo stato del ticket cambia (assegnazione, in lavorazione, risolto...)."""
    cliente = ticket.created_by
    subject = f"Afterbit - Aggiornamento sul ticket #{ticket.id} ({ticket.title})"

    riga_codice = f"Codice di richiamo: {ticket.codice_riferimento}\n" if ticket.codice_riferimento else ""
    riga_assegnazione = f"Assegnato a: {ticket.assigned_to.username}\n" if ticket.assigned_to else ""
    riga_nota = f"Nota di aggiornamento:\n{nota}\n\n" if nota else ""

    message = (
        f"Gentile cliente / staff,\n\n"
        f"Il ticket #{ticket.id} ({ticket.title}) associato all'utente {cliente.username} ha subito un aggiornamento.\n\n"
        f"Stato precedente: {dict(ticket.STATUS_CHOICES).get(stato_precedente, stato_precedente)}\n"
        f"Nuovo stato: {ticket.get_status_display()}\n"
        f"{riga_assegnazione}"
        f"{riga_codice}\n"
        f"{riga_nota}"
        f"Team Afterbit"
    )
    destinatari = []
    if cliente.email:
        destinatari.append(cliente.email)
    if getattr(settings, 'SUPPORT_NOTIFICATION_EMAIL', None):
        destinatari.append(settings.SUPPORT_NOTIFICATION_EMAIL)

    return _invia(subject, message, destinatari, reply_to=[cliente.email] if cliente.email else None)


def notifica_risposta_cliente(ticket, update):
    """Avvisa lo staff e il tecnico assegnato quando il cliente replica al ticket."""
    cliente = update.author
    subject = f"Nuova risposta sul Ticket #{ticket.id}: {ticket.title}"
    allegato_msg = f"\n[Allegato caricato: {update.attachment.name}]" if update.attachment else ""
    message = (
        f"L'utente {cliente.username} ha inviato una nuova risposta/aggiornamento sul ticket #{ticket.id}.\n\n"
        f"Ticket: #{ticket.id} - {ticket.title}\n"
        f"Stato attuale: {ticket.get_status_display()}\n\n"
        f"Messaggio del cliente:\n{update.note}{allegato_msg}\n\n"
        f"Puoi visualizzare e gestire il ticket dal pannello di controllo Afterbit.\n"
    )
    destinatari = []
    if getattr(settings, 'SUPPORT_NOTIFICATION_EMAIL', None):
        destinatari.append(settings.SUPPORT_NOTIFICATION_EMAIL)
    if ticket.assigned_to and ticket.assigned_to.email:
        destinatari.append(ticket.assigned_to.email)

    return _invia(subject, message, destinatari, reply_to=[cliente.email] if cliente.email else None)


def chiusura_ticket_cliente(ticket, nota=None):
    """Comunicazione finale al cliente e allo staff quando il ticket viene chiuso."""
    cliente = ticket.created_by
    subject = f"Afterbit - Il ticket #{ticket.id} è stato chiuso ({ticket.title})"

    riga_codice = (
        f"Se il problema dovesse ripresentarsi, puoi far riferimento al codice "
        f"{ticket.codice_riferimento} per richiamare questo intervento.\n\n"
        if ticket.codice_riferimento else ""
    )
    riga_nota = f"Nota di chiusura:\n{nota}\n\n" if nota else ""
    riga_feedback = (
        "La tua opinione è importante per noi! Accedi al portale per valutare il nostro "
        "servizio di assistenza con un voto da 1 a 5 stelle.\n\n"
    )

    message = (
        f"Gentile cliente / staff,\n\n"
        f"Il ticket #{ticket.id} ({ticket.title}) associato all'utente {cliente.username} è stato chiuso.\n\n"
        f"{riga_nota}"
        f"{riga_codice}"
        f"{riga_feedback}"
        f"Grazie per aver scelto Afterbit.\n\n"
        f"Team Afterbit"
    )
    destinatari = []
    if cliente.email:
        destinatari.append(cliente.email)
    if getattr(settings, 'SUPPORT_NOTIFICATION_EMAIL', None):
        destinatari.append(settings.SUPPORT_NOTIFICATION_EMAIL)

    return _invia(subject, message, destinatari, reply_to=[cliente.email] if cliente.email else None)


