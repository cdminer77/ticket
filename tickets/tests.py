from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from .models import Ticket, TicketUpdate
from unittest.mock import patch


class TicketSystemTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='mario.rossi',
            password='PasswordSicura123!',
            email='mario.rossi@example.com'
        )
        self.staff_user = User.objects.create_user(
            username='staff.helpdesk',
            password='PasswordSicura123!',
            is_staff=True
        )
        self.client = Client()

    def test_login_and_redirect(self):
        response = self.client.post(reverse('login'), {
            'username': 'mario.rossi',
            'password': 'PasswordSicura123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_with_email_and_redirect(self):
        response = self.client.post(reverse('login'), {
            'username': 'mario.rossi@example.com',
            'password': 'PasswordSicura123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_invalid_credentials_shows_error(self):
        response = self.client.post(reverse('login'), {
            'username': 'mario.rossi',
            'password': 'password-sbagliata'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Credenziali non valide')

    def test_create_ticket_authenticated(self):
        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        ticket_data = {
            'tipo_intervento': 'assistenza_tecnica',
            'title': 'Problema VPN aziendale',
            'referente': 'Mario Rossi',
            'categoria': 'Sito Web',
            'description': 'Impossibile connettersi al gateway principale.',
        }
        response = self.client.post(reverse('create_ticket'), ticket_data)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

        ticket = Ticket.objects.filter(title='Problema VPN aziendale').first()
        self.assertIsNotNone(ticket)
        self.assertEqual(ticket.created_by, self.user)
        self.assertEqual(ticket.status, 'open')
        self.assertEqual(ticket.priority, 'urgent')
        self.assertEqual(ticket.referente, 'Mario Rossi')

    def test_create_ticket_invalid_form_shows_errors(self):
        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        # Titolo mancante -> form non valido
        response = self.client.post(reverse('create_ticket'), {
            'tipo_intervento': 'assistenza_tecnica',
            'title': '',
            'referente': 'Mario Rossi',
            'categoria': 'Sito Web',
            'description': 'Descrizione senza titolo',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Controlla i campi evidenziati')
        self.assertFalse(Ticket.objects.filter(description='Descrizione senza titolo').exists())

    def test_create_ticket_rejects_oversized_attachment(self):
        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        oversized_file = SimpleUploadedFile(
            'documento.pdf',
            b'x' * (11 * 1024 * 1024),  # 11MB > limite di 10MB
            content_type='application/pdf'
        )
        response = self.client.post(reverse('create_ticket'), {
            'tipo_intervento': 'assistenza_tecnica',
            'title': 'Ticket con allegato grande',
            'referente': 'Mario Rossi',
            'categoria': 'Sito Web',
            'description': 'Test dimensione allegato',
            'attachment': oversized_file,
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ticket.objects.filter(title='Ticket con allegato grande').exists())

    def test_unauthenticated_user_cannot_create_ticket(self):
        response = self.client.get(reverse('create_ticket'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')) or '/login/' in response.url)

    def test_normal_user_sees_only_own_tickets(self):
        Ticket.objects.create(
            title='Ticket di Mario', description='...', created_by=self.user
        )
        other_user = User.objects.create_user(username='luigi.bianchi', password='PasswordSicura123!')
        Ticket.objects.create(
            title='Ticket di Luigi', description='...', created_by=other_user
        )

        self.client.login(username='mario.rossi', password='PasswordSicura123!')
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Ticket di Mario')
        self.assertNotContains(response, 'Ticket di Luigi')

    def test_staff_sees_all_tickets(self):
        Ticket.objects.create(title='Ticket di Mario', description='...', created_by=self.user)
        other_user = User.objects.create_user(username='luigi.bianchi', password='PasswordSicura123!')
        Ticket.objects.create(title='Ticket di Luigi', description='...', created_by=other_user)

        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Ticket di Mario')
        self.assertContains(response, 'Ticket di Luigi')

    def test_normal_user_cannot_see_others_ticket_detail(self):
        other_user = User.objects.create_user(username='luigi.bianchi', password='PasswordSicura123!')
        ticket = Ticket.objects.create(title='Ticket di Luigi', description='...', created_by=other_user)

        self.client.login(username='mario.rossi', password='PasswordSicura123!')
        response = self.client.get(reverse('ticket_detail', args=[ticket.id]))

        self.assertEqual(response.status_code, 404)

    def test_staff_can_update_ticket_status(self):
        ticket = Ticket.objects.create(title='Ticket da aggiornare', description='...', created_by=self.user)

        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        response = self.client.post(reverse('ticket_detail', args=[ticket.id]), {
            'status': 'in_progress',
            'assigned_to': self.staff_user.id,
        })

        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'in_progress')
        self.assertEqual(ticket.assigned_to, self.staff_user)

    def test_ticket_search_finds_existing_ticket_with_valid_email(self):
        ticket = Ticket.objects.create(title='Ticket ricercabile', description='...', created_by=self.user)

        response = self.client.get(reverse('ticket_search'), {
            'code': str(ticket.id),
            'verify_contact': 'mario.rossi@example.com'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ticket ricercabile')

    def test_ticket_search_finds_ticket_with_referente_or_azienda(self):
        ticket = Ticket.objects.create(
            title='Ticket con azienda',
            referente='Acme Corp Srl',
            description='...',
            created_by=self.user
        )

        response = self.client.get(reverse('ticket_search'), {
            'code': str(ticket.id),
            'verify_contact': 'Acme Corp Srl'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ticket con azienda')

    def test_ticket_search_rejects_without_verification_contact(self):
        ticket = Ticket.objects.create(title='Ticket privato', description='...', created_by=self.user)

        response = self.client.get(reverse('ticket_search'), {'code': str(ticket.id)})

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Ticket privato')
        self.assertContains(response, 'tutelare la privacy')

    def test_ticket_search_rejects_wrong_verification_contact(self):
        ticket = Ticket.objects.create(title='Ticket privato', description='...', created_by=self.user)

        response = self.client.get(reverse('ticket_search'), {
            'code': str(ticket.id),
            'verify_contact': 'hacker@sconosciuto.it'
        })

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Ticket privato')
        self.assertContains(response, 'Nessun ticket trovato o dati di verifica non corrispondenti')

    def test_ticket_search_no_result_for_invalid_code(self):
        response = self.client.get(reverse('ticket_search'), {
            'code': '999999',
            'verify_contact': 'mario.rossi@example.com'
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nessun ticket trovato')

    def test_create_ticket_requires_tipo_intervento(self):
        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        response = self.client.post(reverse('create_ticket'), {
            'tipo_intervento': '',  # non valido: non e' una delle scelte ammesse
            'title': 'Ticket senza tipo',
            'referente': 'Mario Rossi',
            'description': 'Manca il tipo di intervento',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Ticket.objects.filter(title='Ticket senza tipo').exists())

    def test_ticket_shows_selected_tipo_intervento(self):
        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        self.client.post(reverse('create_ticket'), {
            'tipo_intervento': 'amministrazione',
            'title': 'Richiesta fattura',
            'referente': 'Mario Rossi',
            'categoria': 'Fatture e contabilità',
            'description': 'Serve una fattura del mese scorso.',
        })

        ticket = Ticket.objects.get(title='Richiesta fattura')
        self.assertEqual(ticket.tipo_intervento, 'amministrazione')

    def test_codice_riferimento_generato_alla_prima_assegnazione(self):
        ticket = Ticket.objects.create(
            title='Ticket da assegnare', description='...', created_by=self.user
        )
        self.assertIsNone(ticket.codice_riferimento)

        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        self.client.post(reverse('ticket_detail', args=[ticket.id]), {
            'status': 'in_progress',
            'assigned_to': self.staff_user.id,
        })

        ticket.refresh_from_db()
        self.assertIsNotNone(ticket.codice_riferimento)
        self.assertTrue(ticket.codice_riferimento.startswith('AB-'))
        self.assertIn(str(ticket.id).zfill(5), ticket.codice_riferimento)

    def test_codice_riferimento_non_cambia_se_gia_assegnato(self):
        ticket = Ticket.objects.create(
            title='Ticket gia assegnato', description='...',
            created_by=self.user, assigned_to=self.staff_user
        )
        ticket.genera_codice_riferimento()
        ticket.save()
        codice_originale = ticket.codice_riferimento

        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        self.client.post(reverse('ticket_detail', args=[ticket.id]), {
            'status': 'resolved',
            'assigned_to': self.staff_user.id,
        })

        ticket.refresh_from_db()
        self.assertEqual(ticket.codice_riferimento, codice_originale)

    def test_last_activity_at_aggiornato_da_staff(self):
        ticket = Ticket.objects.create(title='Ticket da lavorare', description='...', created_by=self.user)
        self.assertIsNone(ticket.last_activity_at)

        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        self.client.post(reverse('ticket_detail', args=[ticket.id]), {
            'status': 'in_progress',
            'assigned_to': self.staff_user.id,
        })

        ticket.refresh_from_db()
        self.assertIsNotNone(ticket.last_activity_at)

    # --- Blocco 2: dashboard ---

    def test_dashboard_mostra_colonne_e_stato(self):
        Ticket.objects.create(title='Ticket senza lavorazione', description='...', created_by=self.user)

        self.client.login(username='mario.rossi', password='PasswordSicura123!')
        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, 'Apertura')
        self.assertContains(response, 'Risposta / Stato')

    def test_dashboard_mostra_operatore_assegnato(self):
        ticket = Ticket.objects.create(title='Ticket assegnato', description='...', created_by=self.user)

        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        self.client.post(reverse('ticket_detail', args=[ticket.id]), {
            'status': 'in_progress',
            'assigned_to': self.staff_user.id,
        })

        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'staff.helpdesk')

    # --- Blocco 3: registrazione clienti ---

    def test_registrazione_nuovo_cliente(self):
        session = self.client.session
        session['captcha_answer'] = '8'
        session.save()

        response = self.client.post(reverse('register'), {
            'username': 'nuovo.cliente',
            'email': 'nuovo.cliente@example.com',
            'phone': '0587 123456',
            'password1': 'PasswordSuperSicura123!',
            'password2': 'PasswordSuperSicura123!',
            'captcha': '8',
            'accetta_privacy': True,
        })

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('dashboard'))

        user = User.objects.get(username='nuovo.cliente')
        self.assertEqual(user.email, 'nuovo.cliente@example.com')
        self.assertEqual(user.profile.phone, '0587 123456')

    def test_registrazione_password_non_coincidenti(self):
        session = self.client.session
        session['captcha_answer'] = '8'
        session.save()

        response = self.client.post(reverse('register'), {
            'username': 'altro.cliente',
            'email': 'altro.cliente@example.com',
            'phone': '',
            'password1': 'PasswordSuperSicura123!',
            'password2': 'PasswordDiversa456!',
            'captcha': '8',
            'accetta_privacy': True,
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='altro.cliente').exists())

    def test_registrazione_email_duplicata_rifiutata(self):
        User.objects.create_user(username='esistente', email='dup@example.com', password='PasswordSicura123!')

        session = self.client.session
        session['captcha_answer'] = '8'
        session.save()

        response = self.client.post(reverse('register'), {
            'username': 'nuovo.utente',
            'email': 'dup@example.com',
            'phone': '',
            'password1': 'PasswordSuperSicura123!',
            'password2': 'PasswordSuperSicura123!',
            'captcha': '8',
            'accetta_privacy': True,
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nuovo.utente').exists())

    # --- Blocco 3.5: captcha di sicurezza ---

    def test_captcha_domanda_visibile_in_get(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        q = self.client.session.get('captcha_question')
        self.assertIsNotNone(q)
        self.assertContains(response, f"Verifica di sicurezza: quanto fa {q}?")

    def test_registrazione_fallisce_con_captcha_errato(self):
        session = self.client.session
        session['captcha_answer'] = '8'
        session.save()

        response = self.client.post(reverse('register'), {
            'username': 'nuovo.cliente',
            'email': 'nuovo.cliente@example.com',
            'phone': '0587 123456',
            'password1': 'PasswordSuperSicura123!',
            'password2': 'PasswordSuperSicura123!',
            'captcha': '9', # risposta errata
            'accetta_privacy': True,
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nuovo.cliente').exists())
        self.assertContains(response, 'Risposta captcha errata')

    def test_captcha_rigenerato_dopo_errore(self):
        session = self.client.session
        session['captcha_answer'] = '8'
        session.save()

        response = self.client.post(reverse('register'), {
            'username': 'nuovo.cliente',
            'email': 'nuovo.cliente@example.com',
            'phone': '0587 123456',
            'password1': 'PasswordSuperSicura123!',
            'password2': 'PasswordSuperSicura123!',
            'captcha': '9', # risponde male
            'accetta_privacy': True,
        })

        # La sessione deve contenere un nuovo captcha dopo l'errore di invio
        self.assertEqual(response.status_code, 200)
        new_answer = self.client.session.get('captcha_answer')
        self.assertIsNotNone(new_answer)
        self.assertNotEqual(new_answer, '8')

    # --- Blocco 3.7: privacy policy ---

    def test_registrazione_fallisce_senza_accettare_privacy(self):
        session = self.client.session
        session['captcha_answer'] = '8'
        session.save()

        response = self.client.post(reverse('register'), {
            'username': 'nuovo.cliente',
            'email': 'nuovo.cliente@example.com',
            'phone': '0587 123456',
            'password1': 'PasswordSuperSicura123!',
            'password2': 'PasswordSuperSicura123!',
            'captcha': '8',
            # 'accetta_privacy' mancante o False
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='nuovo.cliente').exists())
        self.assertContains(response, 'Questo campo è obbligatorio')

    def test_privacy_policy_page_resolves_correctly(self):
        response = self.client.get(reverse('privacy_policy'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Informativa sulla Privacy')
        self.assertContains(response, 'Afterbit')

    def test_home_mostra_opzioni_cliente_registrato_e_nuovo(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Accedi')
        self.assertContains(response, 'Registrati')

    # --- Blocco 4: email automatiche ---

    def test_creazione_ticket_invia_notifica_staff_e_ricevuta_cliente(self):
        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        self.client.post(reverse('create_ticket'), {
            'tipo_intervento': 'assistenza_tecnica',
            'title': 'PC non si accende',
            'referente': 'Mario Rossi',
            'categoria': 'Sito Web',
            'description': 'Il PC in reception non parte piu.',
        })

        self.assertEqual(len(mail.outbox), 2)

        destinatari = [set(m.to) for m in mail.outbox]
        self.assertIn({'info@afterbit.com'}, destinatari)
        self.assertIn({'mario.rossi@example.com'}, destinatari)

        ricevuta = next(m for m in mail.outbox if m.to == ['mario.rossi@example.com'])
        self.assertIn('PC non si accende', ricevuta.body)

    def test_creazione_ticket_senza_email_cliente_non_fallisce(self):
        utente_senza_email = User.objects.create_user(
            username='cliente.senza.email', password='PasswordSicura123!'
        )
        self.client.login(username='cliente.senza.email', password='PasswordSicura123!')

        response = self.client.post(reverse('create_ticket'), {
            'tipo_intervento': 'assistenza_tecnica',
            'title': 'Sito lento',
            'referente': 'Referente Senza Email',
            'categoria': 'Sito Web',
            'description': 'Il sito impiega troppo a caricare.',
        })

        self.assertEqual(response.status_code, 302)
        # Solo la notifica staff, nessuna ricevuta cliente (email mancante)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['info@afterbit.com'])

    def test_cambio_stato_invia_email_aggiornamento_cliente(self):
        ticket = Ticket.objects.create(
            title='Problema stampante', description='...', created_by=self.user
        )
        mail.outbox.clear()

        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        self.client.post(reverse('ticket_detail', args=[ticket.id]), {
            'status': 'in_progress',
            'assigned_to': self.staff_user.id,
            'action': 'save_and_notify',
        })

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('mario.rossi@example.com', mail.outbox[0].to)
        self.assertIn('info@afterbit.com', mail.outbox[0].to)
        self.assertIn('In Lavorazione', mail.outbox[0].body)

    def test_chiusura_ticket_invia_email_dedicata_al_cliente(self):
        ticket = Ticket.objects.create(
            title='Problema risolto ieri', description='...', created_by=self.user,
            status='resolved', assigned_to=self.staff_user
        )
        mail.outbox.clear()

        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        self.client.post(reverse('ticket_detail', args=[ticket.id]), {
            'status': 'closed',
            'assigned_to': self.staff_user.id,
            'action': 'save_and_notify',
        })

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('mario.rossi@example.com', mail.outbox[0].to)
        self.assertIn('info@afterbit.com', mail.outbox[0].to)
        self.assertIn('chiuso', mail.outbox[0].subject.lower())

    def test_nessuna_email_se_lo_stato_non_cambia(self):
        ticket = Ticket.objects.create(
            title='Ticket stabile', description='...', created_by=self.user,
            status='in_progress', assigned_to=self.staff_user
        )
        ticket.genera_codice_riferimento()
        ticket.save()
        mail.outbox.clear()

        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        self.client.post(reverse('ticket_detail', args=[ticket.id]), {
            'status': 'in_progress',  # invariato
            'assigned_to': self.staff_user.id,
            'action': 'save_and_notify',
        })

        self.assertEqual(len(mail.outbox), 0)

    def test_creazione_ticket_salva_ip_e_localizzazione_sviluppo(self):
        self.client.login(username='mario.rossi', password='PasswordSicura123!')
        response = self.client.post(reverse('create_ticket'), {
            'tipo_intervento': 'assistenza_tecnica',
            'title': 'Test IP locale',
            'referente': 'Mario Rossi',
            'categoria': 'Sito Web',
            'description': 'Descrizione test',
        })
        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(title='Test IP locale')
        # Di default in locale REMOTE_ADDR e' 127.0.0.1
        self.assertEqual(ticket.created_from_ip, '127.0.0.1')
        self.assertEqual(ticket.created_from_location, 'Sviluppo / Localhost')

    @patch('urllib.request.urlopen')
    def test_creazione_ticket_salva_ip_e_localizzazione_mockata(self, mock_urlopen):
        # Simula una risposta JSON di successo da ip-api.com
        import io
        mock_response = io.BytesIO(b'''{
            "status": "success",
            "city": "Milano",
            "regionName": "Lombardia",
            "country": "Italy",
            "isp": "Fastweb SpA"
        }''')
        mock_urlopen.return_value = mock_response

        self.client.login(username='mario.rossi', password='PasswordSicura123!')
        # Per forzare REMOTE_ADDR a un IP pubblico, passiamo REMOTE_ADDR nei parametri extra del client
        response = self.client.post(
            reverse('create_ticket'),
            {
                'tipo_intervento': 'assistenza_tecnica',
                'title': 'Test IP pubblico',
                'referente': 'Mario Rossi',
                'categoria': 'Sito Web',
                'description': 'Descrizione test',
            },
            REMOTE_ADDR='93.34.12.34'
        )
        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(title='Test IP pubblico')
        self.assertEqual(ticket.created_from_ip, '93.34.12.34')
        self.assertEqual(ticket.created_from_location, 'Milano, Lombardia, Italy (ISP: Fastweb SpA)')

    def test_ip_e_localizzazione_visibili_solo_a_staff(self):
        ticket = Ticket.objects.create(
            title='Ticket test visibilita',
            description='...',
            created_by=self.user,
            created_from_ip='93.34.12.34',
            created_from_location='Milano, Italy'
        )

        # 1. Utente normale non deve vederli
        self.client.login(username='mario.rossi', password='PasswordSicura123!')
        response = self.client.get(reverse('ticket_detail', args=[ticket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'IP di creazione')
        self.assertNotContains(response, '93.34.12.34')
        self.assertNotContains(response, 'Milano, Italy')

        # 2. Utente staff deve vederli
        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        response = self.client.get(reverse('ticket_detail', args=[ticket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'IP di creazione')
        self.assertContains(response, '93.34.12.34')
        self.assertContains(response, 'Milano, Italy')

    def test_normal_user_sees_referente_in_details(self):
        ticket = Ticket.objects.create(
            title='Ticket con referente', referente='Luigi Bianchi',
            description='...', created_by=self.user
        )
        self.client.login(username='mario.rossi', password='PasswordSicura123!')
        response = self.client.get(reverse('ticket_detail', args=[ticket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Luigi Bianchi')

    def test_staff_adds_note_and_emails_customer(self):
        ticket = Ticket.objects.create(
            title='Ticket per note', description='...', created_by=self.user
        )
        mail.outbox.clear()

        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')
        response = self.client.post(reverse('ticket_detail', args=[ticket.id]), {
            'status': 'in_progress',
            'assigned_to': self.staff_user.id,
            'note': 'Siamo al lavoro per risolvere l\'errore del database.',
            'action': 'save_and_notify',
        })

        self.assertEqual(response.status_code, 302)
        ticket.refresh_from_db()
        self.assertEqual(ticket.updates.count(), 1)
        update = ticket.updates.first()
        self.assertEqual(update.note, 'Siamo al lavoro per risolvere l\'errore del database.')
        self.assertEqual(update.author, self.staff_user)

        # Check email contains the note
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Siamo al lavoro per risolvere l\'errore del database.', mail.outbox[0].body)

    def test_dashboard_filters_by_text_search(self):
        Ticket.objects.create(title='Stampante rotta', description='La stampante non stampa.', created_by=self.user)
        Ticket.objects.create(title='Errore login', description='Errore ad accedere al pannello.', created_by=self.user, referente='Giovanni Rossi')

        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        # Cerca per parola chiave 'Stampante'
        response = self.client.get(reverse('dashboard'), {'q': 'Stampante'})
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].title, 'Stampante rotta')

        # Cerca per referente 'Giovanni'
        response = self.client.get(reverse('dashboard'), {'q': 'Giovanni'})
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].title, 'Errore login')

    def test_dashboard_filters_by_status(self):
        Ticket.objects.create(title='Ticket Aperto', status='open', created_by=self.user)
        Ticket.objects.create(title='Ticket Risolto', status='resolved', created_by=self.user)

        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        response = self.client.get(reverse('dashboard'), {'status': 'resolved'})
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].title, 'Ticket Risolto')

    def test_dashboard_filters_by_tipo_intervento(self):
        Ticket.objects.create(title='Ticket Amministrazione', tipo_intervento='amministrazione', created_by=self.user)
        Ticket.objects.create(title='Ticket Assistenza', tipo_intervento='assistenza_tecnica', created_by=self.user)

        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        response = self.client.get(reverse('dashboard'), {'tipo_intervento': 'amministrazione'})
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].title, 'Ticket Amministrazione')

    def test_user_marco_creates_ticket_smoothly_with_urgent_priority(self):
        marco = User.objects.create_user(
            username='marco',
            password='PasswordSicura123!',
            email='marco@afterbit.com'
        )
        self.client.login(username='marco', password='PasswordSicura123!')

        response = self.client.post(reverse('create_ticket'), {
            'tipo_intervento': 'assistenza_tecnica',
            'title': 'Ticket di Marco',
            'referente': 'Marco Rossi',
            'categoria': 'Posta elettronica',
            'description': 'Problema con la casella IMAP.',
        })

        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(title='Ticket di Marco')
        self.assertEqual(ticket.created_by, marco)
        self.assertEqual(ticket.priority, 'urgent')
        self.assertEqual(ticket.categoria, 'Posta elettronica')

    def test_dashboard_and_detail_do_not_contain_servizio_column_or_priority_selector(self):
        ticket = Ticket.objects.create(
            title='Ticket senza servizio visibile',
            description='Test visualizzazione pulita',
            created_by=self.user,
            categoria='Posta certificata'
        )
        self.client.login(username='staff.helpdesk', password='PasswordSicura123!')

        # Dashboard check
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, 'Posta certificata')

        # Detail check
        detail_response = self.client.get(reverse('ticket_detail', args=[ticket.id]))
        self.assertEqual(detail_response.status_code, 200)
        self.assertNotContains(detail_response, 'Modifica Priorità')

    def test_customer_reply_to_ticket_with_attachment_and_reopen(self):
        ticket = Ticket.objects.create(
            title='Problema email',
            description='Descrizione iniziale',
            created_by=self.user,
            status='closed'
        )
        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        test_file = SimpleUploadedFile('screenshot_errore.png', b'file_data_here', content_type='image/png')

        response = self.client.post(
            reverse('ticket_detail', args=[ticket.id]),
            {
                'action': 'reply',
                'note': 'Ecco lo screenshot aggiuntivo richiesto dal tecnico.',
                'attachment': test_file
            }
        )
        self.assertEqual(response.status_code, 302)

        ticket.refresh_from_db()
        # The ticket should be reopened since customer replied to a closed ticket
        self.assertEqual(ticket.status, 'in_progress')
        self.assertEqual(ticket.updates.count(), 1)

        update = ticket.updates.first()
        self.assertEqual(update.author, self.user)
        self.assertIn('screenshot_errore', update.attachment.name)
        self.assertEqual(update.note, 'Ecco lo screenshot aggiuntivo richiesto dal tecnico.')

    def test_customer_submit_feedback_five_stars(self):
        ticket = Ticket.objects.create(
            title='Intervento risolto',
            description='Problema risolto con successo',
            created_by=self.user,
            status='resolved'
        )
        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        response = self.client.post(
            reverse('ticket_detail', args=[ticket.id]),
            {
                'action': 'submit_feedback',
                'rating': '5',
                'rating_comment': 'Servizio impeccabile e veloce!'
            }
        )
        self.assertEqual(response.status_code, 302)

        ticket.refresh_from_db()
        self.assertEqual(ticket.rating, 5)
        self.assertEqual(ticket.rating_comment, 'Servizio impeccabile e veloce!')
        self.assertIsNotNone(ticket.rated_at)

        # Verify feedback is visible in detail view
        get_response = self.client.get(reverse('ticket_detail', args=[ticket.id]))
        self.assertContains(get_response, 'Valutazione Servizio: 5 su 5 Stelle')
        self.assertContains(get_response, 'Servizio impeccabile e veloce!')

    def test_create_ticket_page_shows_logged_in_user_info(self):
        self.client.login(username='mario.rossi', password='PasswordSicura123!')
        response = self.client.get(reverse('create_ticket'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mario.rossi')
        self.assertContains(response, 'mario.rossi@example.com')
        self.assertContains(response, 'Richiedente / Account Autenticato')

    def test_faq_page_contains_comprehensive_email_and_pec_settings(self):
        response = self.client.get(reverse('faq'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Server IMAP (Consigliato)')
        self.assertContains(response, 'mail.afterbit.it')
        self.assertContains(response, 'smtp.afterbit.it')
        self.assertContains(response, '993')
        self.assertContains(response, '465')
        self.assertContains(response, 'Parametri Casella PEC')
        self.assertContains(response, 'imaps.pec.aruba.it')

    def test_customer_can_close_ticket_anytime_with_reason(self):
        ticket = Ticket.objects.create(
            title='Ticket da chiudere autonomamente',
            description='Problema temporaneo',
            created_by=self.user,
            status='open'
        )
        self.client.login(username='mario.rossi', password='PasswordSicura123!')

        response = self.client.post(
            reverse('ticket_detail', args=[ticket.id]),
            {
                'action': 'close_by_customer',
                'close_reason': 'Risolto riavviando il router.'
            }
        )
        self.assertEqual(response.status_code, 302)

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'closed')
        self.assertEqual(ticket.updates.count(), 1)
        update = ticket.updates.first()
        self.assertIn('Risolto riavviando il router', update.note)
        self.assertEqual(update.author, self.user)


