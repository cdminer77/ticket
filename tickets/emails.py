"""
Invio delle comunicazioni email automatiche legate ai ticket:
- notifica interna a info@afterbit.com quando arriva un nuovo ticket
- ricevuta al cliente all'apertura
- aggiornamento al cliente ad ogni cambio di stato
- comunicazione al cliente alla chiusura finale dell'intervento

Ogni funzione e' "silenziosa" sugli errori di invio (non blocca mai la
navigazione dell'utente se il server SMTP e' irraggiungibile o mal
configurato), ma restituisce True/False cosi' il chiamante puo' avvisare
lo staff se qualcosa non e' partito.
"""
import logging

from django.conf import settings
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)


def _invia(subject, message, destinatari, reply_to=None):
    if not destinatari:
        return False
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
        logger.exception("Invio email fallito: subject=%r destinatari=%r", subject, destinatari)
        return False


def notifica_nuovo_ticket_staff(ticket):
    """Avvisa l'indirizzo interno (info@afterbit.com) che e' stato aperto un nuovo ticket."""
    cliente = ticket.created_by
    subject = f"Nuovo ticket #{ticket.id}: {ticket.title}"
    message = (
        f"E' stato aperto un nuovo ticket sul portale assistenza.\n\n"
        f"Numero ticket: #{ticket.id}\n"
        f"Cliente: {cliente.username} ({cliente.email or 'email non indicata'})\n"
        f"Tipo intervento: {ticket.get_tipo_intervento_display()}\n"
        f"Priorità: {ticket.get_priority_display()}\n\n"
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
        f"Tipo intervento: {ticket.get_tipo_intervento_display()}\n"
        f"Priorità: {ticket.get_priority_display()}\n\n"
        f"Ti scriveremo di nuovo non appena il ticket verrà preso in carico "
        f"e ad ogni aggiornamento importante, fino alla chiusura dell'intervento.\n\n"
        f"Team Afterbit"
    )
    return _invia(subject, message, [cliente.email] if cliente.email else [])


def aggiornamento_stato_ticket_cliente(ticket, stato_precedente):
    """Comunicazione al cliente quando lo stato del ticket cambia (assegnazione, in lavorazione, risolto...)."""
    cliente = ticket.created_by
    subject = f"Afterbit - Aggiornamento sul tuo ticket #{ticket.id}"

    riga_codice = f"Codice di richiamo: {ticket.codice_riferimento}\n" if ticket.codice_riferimento else ""
    riga_assegnazione = f"Assegnato a: {ticket.assigned_to.username}\n" if ticket.assigned_to else ""

    message = (
        f"Ciao {cliente.username},\n\n"
        f"Il tuo ticket #{ticket.id} ({ticket.title}) ha subito un aggiornamento.\n\n"
        f"Stato precedente: {dict(ticket.STATUS_CHOICES).get(stato_precedente, stato_precedente)}\n"
        f"Nuovo stato: {ticket.get_status_display()}\n"
        f"{riga_assegnazione}"
        f"{riga_codice}\n"
        f"Team Afterbit"
    )
    return _invia(subject, message, [cliente.email] if cliente.email else [])


def chiusura_ticket_cliente(ticket):
    """Comunicazione finale al cliente quando il ticket viene chiuso."""
    cliente = ticket.created_by
    subject = f"Afterbit - Il tuo ticket #{ticket.id} è stato chiuso"

    riga_codice = (
        f"Se il problema dovesse ripresentarsi, puoi far riferimento al codice "
        f"{ticket.codice_riferimento} per richiamare questo intervento.\n\n"
        if ticket.codice_riferimento else ""
    )

    message = (
        f"Ciao {cliente.username},\n\n"
        f"Il tuo ticket #{ticket.id} ({ticket.title}) è stato chiuso.\n\n"
        f"{riga_codice}"
        f"Grazie per aver scelto Afterbit.\n\n"
        f"Team Afterbit"
    )
    return _invia(subject, message, [cliente.email] if cliente.email else [])
