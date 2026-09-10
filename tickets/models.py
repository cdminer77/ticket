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
    ('Trust', 'Trust'),
    ('Sito Web', 'Sito Web'),
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
