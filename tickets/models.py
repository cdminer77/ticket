from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils import timezone

# Estensioni ammesse per gli allegati e dimensione massima (in MB)
ALLOWED_ATTACHMENT_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'log', 'docx', 'xlsx']
MAX_ATTACHMENT_SIZE_MB = 10


def validate_attachment_size(file):
    """Blocca upload di file più grandi di MAX_ATTACHMENT_SIZE_MB."""
    limit_bytes = MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
    if file.size > limit_bytes:
        raise ValidationError(
            f"Il file supera la dimensione massima consentita di {MAX_ATTACHMENT_SIZE_MB} MB."
        )


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Aperto'),
        ('in_progress', 'In Lavorazione'),
        ('resolved', 'Risolto'),
        ('closed', 'Chiuso'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Bassa'),
        ('medium', 'Media'),
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    TIPO_INTERVENTO_CHOICES = [
        ('amministrazione', 'Amministrazione'),
        ('assistenza_tecnica', 'Assistenza Tecnica'),
    ]

    title = models.CharField(max_length=200, verbose_name="Oggetto / Titolo")
    referente = models.CharField(max_length=100, default="Non specificato", verbose_name="Nominativo Referente")
    description = models.TextField(verbose_name="Descrizione del problema")
    tipo_intervento = models.CharField(
        max_length=30,
        choices=TIPO_INTERVENTO_CHOICES,
        default='assistenza_tecnica',
        verbose_name="Tipo di intervento richiesto",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='urgent')
    attachment = models.FileField(
        upload_to='ticket_attachments/',
        blank=True,
        null=True,
        verbose_name="Allegato",
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_ATTACHMENT_EXTENSIONS),
            validate_attachment_size,
        ],
    )

    # Codice mostrato al cliente per poter richiamare l'intervento in corso.
    # Viene generato automaticamente alla prima assegnazione del ticket (es. AB-2026-00042).
    codice_riferimento = models.CharField(max_length=20, blank=True, null=True, unique=True)

    # Ultima volta che qualcuno ha lavorato/assegnato il ticket (diverso da updated_at,
    # che si aggiorna su qualunque save; questo lo aggiorniamo solo dalle azioni di gestione staff).
    last_activity_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')

    created_from_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP di creazione")
    created_from_location = models.CharField(max_length=255, null=True, blank=True, verbose_name="Localizzazione IP")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} - {self.title}"

    def genera_codice_riferimento(self):
        """Genera e salva il codice di richiamo (es. AB-2026-00042) se non esiste ancora."""
        if not self.codice_riferimento:
            anno = self.created_at.year if self.created_at else timezone.now().year
            self.codice_riferimento = f"AB-{anno}-{self.id:05d}"
        return self.codice_riferimento


class UserProfile(models.Model):
    """Dati aggiuntivi del cliente non presenti nel modello User di Django."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=30, blank=True, verbose_name="Telefono")

    def __str__(self):
        return f"Profilo di {self.user.username}"


class TicketUpdate(models.Model):
    """Note di lavorazione/aggiornamento del ticket inserite dallo staff."""
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField(verbose_name="Nota di aggiornamento")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Nota su #{self.ticket.id} da {self.author.username}"
