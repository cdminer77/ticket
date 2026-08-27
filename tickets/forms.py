from django import forms  # type: ignore[reportMissingModuleSource]
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Ticket, MAX_ATTACHMENT_SIZE_MB, UserProfile
from django.utils.safestring import mark_safe

INPUT_CLASSES = (
    'block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 shadow-sm '
    'focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 sm:text-sm'
)


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['tipo_intervento', 'title', 'referente', 'description', 'attachment']
        widgets = {
            'tipo_intervento': forms.Select(attrs={
                'class': INPUT_CLASSES
            }),
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Es. Errore accesso server di posta'
            }),
            'referente': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Nome e Cognome di chi segnala il problema'
            }),
            'description': forms.Textarea(attrs={
                'class': INPUT_CLASSES,
                'rows': 5,
                'placeholder': 'Descrivi dettagliatamente il problema riscontrato...'
            }),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            })
        }

    def clean_attachment(self):
        # Validazione esplicita anche qui, cosi' l'errore appare come form error
        # leggibile (i validators sul model comunque restano come seconda barriera).
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            limit_bytes = MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
            if attachment.size > limit_bytes:
                raise forms.ValidationError(
                    f"Il file supera la dimensione massima consentita di {MAX_ATTACHMENT_SIZE_MB} MB."
                )
        return attachment


class TicketStatusForm(forms.ModelForm):
    """Form riservata allo staff per aggiornare stato e assegnazione di un ticket."""

    class Meta:
        model = Ticket
        fields = ['status', 'assigned_to']
        widgets = {
            'status': forms.Select(attrs={'class': INPUT_CLASSES}),
            'assigned_to': forms.Select(attrs={'class': INPUT_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo utenti staff possono essere assegnatari
        self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
        self.fields['assigned_to'].required = False


class CustomerRegistrationForm(UserCreationForm):
    """Registrazione pubblica self-service per i clienti (include telefono)."""

    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'class': INPUT_CLASSES})
    )
    phone = forms.CharField(
        required=False,
        label="Telefono",
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Es. 0587 123456'})
    )
    captcha = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Inserisci il risultato'})
    )
    accetta_privacy = forms.BooleanField(
        required=True,
        label=mark_safe('Accetto la <a href="/privacy-policy/" target="_blank" class="text-blue-600 hover:underline">Privacy Policy</a>'),
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-600'})
    )


    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request:
            question = self.request.session.get('captcha_question')
            if question:
                self.fields['captcha'].label = f"Verifica di sicurezza: quanto fa {question}?"
            else:
                self.fields['captcha'].label = "Verifica di sicurezza"
        else:
            self.fields['captcha'].label = "Verifica di sicurezza"

        for field_name in ['username', 'password1', 'password2', 'captcha']:
            if field_name in self.fields:
                self.fields[field_name].widget.attrs.update({'class': INPUT_CLASSES})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Esiste gia' un account registrato con questa email.")
        return email

    def clean_captcha(self):
        captcha_val = self.cleaned_data.get('captcha', '').strip()
        if not self.request:
            return captcha_val

        correct_answer = self.request.session.get('captcha_answer')
        if not correct_answer or captcha_val != correct_answer:
            raise forms.ValidationError("Risposta captcha errata. Riprova.")
        return captcha_val

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            UserProfile.objects.create(user=user, phone=self.cleaned_data.get('phone', ''))
        return user

