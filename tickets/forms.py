from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Ticket, TicketUpdate, MAX_ATTACHMENT_SIZE_MB, UserProfile, CATEGORIA_CHOICES
from django.utils.safestring import mark_safe

INPUT_CLASSES = (
    'block w-full rounded-lg border border-slate-300 px-3 py-2 text-slate-900 shadow-sm '
    'focus:border-blue-600 focus:outline-none focus:ring-1 focus:ring-blue-600 sm:text-sm'
)

class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'referente', 'categoria', 'tipo_intervento', 'description', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Es. Errore accesso server di posta'
            }),
            'referente': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'Nome e Cognome / Ragione Sociale'
            }),
            'categoria': forms.Select(attrs={
                'class': INPUT_CLASSES,
                'id': 'id_categoria'
            }),
            'tipo_intervento': forms.Select(attrs={
                'class': INPUT_CLASSES
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

    def save(self, commit=True):
        ticket = super().save(commit=False)
        ticket.priority = 'urgent'
        if not ticket.servizio:
            ticket.servizio = 'Generale'
        if commit:
            ticket.save()
        return ticket

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            limit_bytes = MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
            if attachment.size > limit_bytes:
                raise forms.ValidationError(
                    f"Il file supera la dimensione massima consentita di {MAX_ATTACHMENT_SIZE_MB} MB."
                )
        return attachment


class TicketStatusForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['status', 'assigned_to', 'categoria']
        widgets = {
            'status': forms.Select(attrs={'class': INPUT_CLASSES}),
            'assigned_to': forms.Select(attrs={'class': INPUT_CLASSES}),
            'categoria': forms.Select(attrs={'class': INPUT_CLASSES}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_to'].queryset = User.objects.filter(is_staff=True)
        self.fields['assigned_to'].required = False
        if 'categoria' in self.fields:
            self.fields['categoria'].required = False

    def clean_categoria(self):
        return self.cleaned_data.get('categoria') or (self.instance.categoria if self.instance and self.instance.pk else 'Sito Web')

    def save(self, commit=True):
        ticket = super().save(commit=False)
        ticket.priority = 'urgent'
        if not ticket.servizio:
            ticket.servizio = 'Generale'
        if commit:
            ticket.save()
        return ticket


class TicketReplyForm(forms.ModelForm):
    class Meta:
        model = TicketUpdate
        fields = ['note', 'attachment']
        widgets = {
            'note': forms.Textarea(attrs={
                'class': 'block w-full rounded-xl border border-slate-300 p-3.5 text-slate-800 shadow-xs focus:border-[#EC3C11] focus:outline-none focus:ring-2 focus:ring-[#EC3C11] text-xs sm:text-sm',
                'rows': 4,
                'placeholder': 'Scrivi qui la tua risposta, ulteriori informazioni o chiarimenti sul problema...'
            }),
            'attachment': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3.5 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-orange-50 file:text-[#EC3C11] hover:file:bg-orange-100 cursor-pointer'
            })
        }

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            limit_bytes = MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
            if attachment.size > limit_bytes:
                raise forms.ValidationError(
                    f"Il file supera la dimensione massima consentita di {MAX_ATTACHMENT_SIZE_MB} MB."
                )
        return attachment


class TicketFeedbackForm(forms.Form):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.HiddenInput(),
        required=True,
        error_messages={'required': 'Seleziona una valutazione da 1 a 5 stelle.'}
    )
    rating_comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'block w-full rounded-xl border border-slate-300 p-3 text-slate-800 shadow-xs focus:border-[#EC3C11] focus:outline-none focus:ring-2 focus:ring-[#EC3C11] text-xs',
            'rows': 3,
            'placeholder': 'Lascia un commento opzionale sulla tua esperienza o sulla risoluzione del ticket...'
        })
    )


class CustomerRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Es. nome@azienda.it'})
    )
    phone = forms.CharField(
        required=False,
        label="Telefono",
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Es. 0587 123456'})
    )
    captcha = forms.CharField(
        required=True,
        label="Verifica di sicurezza",
        widget=forms.TextInput(attrs={'class': INPUT_CLASSES, 'placeholder': 'Inserisci il risultato numerico'})
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

        # Assicura bordi e stili Tailwind definiti per tutti i campi
        for field_name, field in self.fields.items():
            if field_name != 'accetta_privacy':
                field.widget.attrs['class'] = INPUT_CLASSES

        if 'username' in self.fields:
            self.fields['username'].widget.attrs['placeholder'] = 'Es. mario.rossi'
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs['placeholder'] = 'Password sicura'
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs['placeholder'] = 'Ripeti la password'

        if self.request:
            q = self.request.session.get('captcha_question')
            if q:
                self.fields['captcha'].label = f"Verifica di sicurezza: quanto fa {q}?"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Un account con questa email è già registrato.")
        return email

    def clean_captcha(self):
        answer = self.cleaned_data.get('captcha')
        correct = self.request.session.get('captcha_answer') if self.request else None
        if not correct or str(answer).strip() != str(correct):
            raise forms.ValidationError("Risposta captcha errata. Riprova.")
        return answer

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            phone = self.cleaned_data.get('phone', '')
            UserProfile.objects.create(user=user, phone=phone)
        return user


class TicketRecordingUploadForm(forms.ModelForm):
    """
    Form ad uso ESCLUSIVO dello staff per caricare o registrare audio/video legati al ticket.
    """
    media_blob_base64 = forms.CharField(required=False, widget=forms.HiddenInput())
    audio_blob_base64 = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        from .models import TicketRecording
        model = TicketRecording
        fields = ['title', 'media_type', 'recording_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'block w-full rounded-xl border border-slate-300 p-2.5 text-slate-800 shadow-xs focus:border-[#EC3C11] focus:outline-none focus:ring-2 focus:ring-[#EC3C11] text-xs',
                'placeholder': 'Es. Chiamata tecnica con referente / Registrazione condivisione schermo'
            }),
            'media_type': forms.Select(attrs={
                'class': 'block w-full rounded-xl border border-slate-300 p-2.5 text-slate-800 shadow-xs focus:border-[#EC3C11] focus:outline-none focus:ring-2 focus:ring-[#EC3C11] text-xs'
            }),
            'recording_file': forms.ClearableFileInput(attrs={
                'class': 'block w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3.5 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer border border-slate-200 rounded-xl bg-white p-1'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Il file da input non è obbligatorio se è stata fatta la registrazione vocale/video live
        self.fields['recording_file'].required = False

    def clean(self):
        cleaned_data = super().clean()
        file_obj = cleaned_data.get('recording_file')
        base64_data = cleaned_data.get('media_blob_base64') or cleaned_data.get('audio_blob_base64')
        if not file_obj and not base64_data:
            raise forms.ValidationError("Registra dal vivo (audio o schermo) oppure seleziona un file da caricare.")
        return cleaned_data

