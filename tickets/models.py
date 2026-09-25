from django.db import models  # type: ignore
from django.contrib.auth.models import User  # type: ignore
from django.core.exceptions import ValidationError  # type: ignore
from django.core.validators import FileExtensionValidator  # type: ignore
from django.utils import timezone  # type: ignore

ALLOWED_ATTACHMENT_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'log', 'docx', 'xlsx']
MAX_ATTACHMENT_SIZE_MB = 10

def validate_attachment_size(file):
    limit_bytes = MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
    if file.size > limit_bytes:
        raise ValidationError(
            f"Il file supera la dimensione massima consentita di {MAX_ATTACHMENT_SIZE_MB} MB."
        )

CATEGORIA_CHOICES = [
    ('Fatture e contabilità', 'Fatture e contabilità'),
    ('Attivazioni', 'Attivazioni'),
    ('Cloud', 'Cloud'),
    ('DNS', 'DNS'),
    ('Database Access', 'Database Access'),
    ('Database MySQL', 'Database MySQL'),
    ('Fatturazione elettronica', 'Fatturazione elettronica'),
    ('.htaccess', '.htaccess'),
    ('FrontPage', 'FrontPage'),
    ('FTP', 'FTP'),
    ('GoMobi', 'GoMobi'),
    ('Mail Server Dedicato (DEM)', 'Mail Server Dedicato (DEM)'),
    ('Office 365', 'Office 365'),
    ('Online storage', 'Online storage'),
    ('Pagine ASP', 'Pagine ASP'),
    ('Pagine JSP', 'Pagine JSP'),
    ('Pagine PHP', 'Pagine PHP'),
    ('Pannello di controllo Servermate', 'Pannello di controllo Servermate'),
    ('Pc non connesso a Internet', 'Pc non connesso a Internet '),
    ('pc non si accende', 'pc non si accende'),
    ('Posta certificata', 'Posta certificata (PEC)'),
    ('Posta elettronica', 'Posta elettronica'),
    ('Posta elettronica - incremento', 'Posta elettronica - incremento'),
    ('Protocollo SSL', 'Protocollo SSL'),
    ('Registrazione domini', 'Registrazione domini'),
    ('Rivenditori', 'Rivenditori'),
    ('Server dedicati / VPS', 'Server dedicati / VPS'),
    ('Server SMTP', 'Server SMTP'),
    ('Sicurezza Web', 'Sicurezza Web'),
    ('SiteGenerator', 'SiteGenerator'),
    ('Siti malevoli', 'Siti malevoli'),
    ('SMS e Banner Server', 'SMS e Banner Server'),
    ('SQL Server', 'SQL Server'),
    ('Statistiche', 'Statistiche'),
    ('Trasferimento domini', 'Trasferimento domini'),
    ('Sito Web', 'Sito Web'),
    ('Hardware', 'Hardware'),
    ('Software', 'Software'),   
]

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('open', 'Aperto'),
        ('in_progress', 'In Lavorazione'),
        ('resolved', 'Risolto'),
        ('closed', 'Chiuso'),
    ]

    PRIORITY_CHOICES = [
        ('high', 'Alta'),
        ('urgent', 'Urgente'),
    ]

    TIPO_INTERVENTO_CHOICES = [
        ('amministrazione', 'Amministrazione'),
        ('assistenza_tecnica', 'Assistenza Tecnica'),
    ]

    title = models.CharField(max_length=200, verbose_name="Oggetto / Titolo")
    referente = models.CharField(max_length=100, default="Non specificato", verbose_name="Nominativo Referente")
    servizio = models.CharField(max_length=100, default="Generale", blank=True, verbose_name="Servizio")
    categoria = models.CharField(max_length=100, choices=CATEGORIA_CHOICES, default="Sito Web", verbose_name="Categoria")
    description = models.TextField(verbose_name="Descrizione del problema")
    tipo_intervento = models.CharField(
        max_length=30,
        choices=TIPO_INTERVENTO_CHOICES,
        default='assistenza_tecnica',
        verbose_name="Tipo di intervento richiesto",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='urgent', blank=True)
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

    codice_riferimento = models.CharField(max_length=20, blank=True, null=True, unique=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')

    created_from_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP di creazione")
    created_from_location = models.CharField(max_length=255, null=True, blank=True, verbose_name="Localizzazione IP")

    # Feedback e valutazione del cliente
    rating = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Valutazione (1-5 stelle)")
    rating_comment = models.TextField(blank=True, default="", verbose_name="Commento feedback")
    rated_at = models.DateTimeField(null=True, blank=True, verbose_name="Data valutazione")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.id} - {self.title}"

    def genera_codice_riferimento(self):
        if not self.codice_riferimento:
            anno = self.created_at.year if self.created_at else timezone.now().year
            self.codice_riferimento = f"AB-{anno}-{self.id:05d}"
        return self.codice_riferimento

    @property
    def comments_count(self):
        return self.updates.count()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=30, blank=True, verbose_name="Telefono")

    def __str__(self):
        return f"Profilo di {self.user.username}"


class TicketUpdate(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='updates')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField(verbose_name="Nota di aggiornamento")
    attachment = models.FileField(
        upload_to='ticket_updates_attachments/',
        blank=True,
        null=True,
        verbose_name="Allegato risposta",
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_ATTACHMENT_EXTENSIONS),
            validate_attachment_size,
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Nota su #{self.ticket.id} da {self.author.username}"


class TicketReadStatus(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_read_statuses')
    last_read_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('ticket', 'user')
        verbose_name = "Stato Lettura Ticket"
        verbose_name_plural = "Stati Lettura Ticket"

    def __str__(self):
        return f"{self.user.username} - Ticket #{self.ticket_id} letto il {self.last_read_at}"


ALLOWED_RECORDING_EXTENSIONS = ['mp3', 'wav', 'm4a', 'ogg', 'webm', 'mp4', 'mov', 'mkv']
MAX_RECORDING_SIZE_MB = 1000  # 1 GB per call/video lunghi fino a 1 ora

def validate_recording_size(file):
    limit_bytes = MAX_RECORDING_SIZE_MB * 1024 * 1024
    if file.size > limit_bytes:
        raise ValidationError(
            f"Il file supera la dimensione massima consentita di {MAX_RECORDING_SIZE_MB} MB."
        )


class TicketRecording(models.Model):
    """
    Registrazioni audio/video di sessioni e call con clienti ad uso ESCLUSIVO interno dello staff.
    I clienti non hanno accesso a questo modello né alla sua visualizzazione/gestione.
    """
    MEDIA_TYPE_CHOICES = [
        ('audio', 'Audio Call / Vocale'),
        ('video', 'Video / Registrazione Schermo'),
    ]

    STATUS_CHOICES = [
        ('pending', 'In attesa di trascrizione'),
        ('processing', 'Trascrizione in corso...'),
        ('completed', 'Completato'),
        ('failed', 'Errore elaborazione'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='recordings')
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Operatore staff")
    title = models.CharField(max_length=200, blank=True, default="", verbose_name="Titolo / Oggetto call")
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, default='audio', verbose_name="Tipo file")
    recording_file = models.FileField(
        upload_to='ticket_staff_recordings/%Y/%m/',
        verbose_name="File Registrazione",
        validators=[
            FileExtensionValidator(allowed_extensions=ALLOWED_RECORDING_EXTENSIONS),
            validate_recording_size,
        ]
    )
    duration_seconds = models.PositiveIntegerField(null=True, blank=True, verbose_name="Durata in secondi")

    # Dati generati dal motore locale (faster-whisper e OCR)
    transcript = models.TextField(blank=True, default="", verbose_name="Trascrizione integrale")
    extracted_notes = models.TextField(blank=True, default="", verbose_name="Dati e note estratte (OCR / Punti chiave)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Stato trascrizione")
    error_message = models.TextField(blank=True, default="", verbose_name="Eventuale errore")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data registrazione")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Registrazione Interna Ticket"
        verbose_name_plural = "Registrazioni Interne Ticket"

    def __str__(self):
        return f"[{self.get_media_type_display()}] #{self.ticket.id} - {self.title or self.created_at.strftime('%d/%m/%Y %H:%M')}"

