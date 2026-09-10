# Afterbit Ticket — Descrizione dello Stack Tecnologico
**Documento tecnico di riferimento — Versione 2.0 (Settembre 2026)**

---

## 1. Panoramica del Progetto
**Afterbit Ticket** è una piattaforma web di gestione delle richieste di assistenza tecnica e amministrativa (Helpdesk/Ticketing) sviluppata con architettura Python/Django.

Consente ai clienti di aprire ticket categorizzati per area tecnica (hosting, posta elettronica, PEC, DNS, database, server, sicurezza web) e allo staff di supporto interno di gestire l'intero ciclo di vita delle richieste (assegnazione, lavorazione, tracciamento note tecniche, comunicazioni email al cliente).

L'applicazione è strutturata con rendering lato server ad alte prestazioni (Django Templates + Tailwind CSS), integrata con file statici serviti da WhiteNoise e backend database MySQL in produzione (con supporto SQLite per lo sviluppo locale).

---

## 2. Dettaglio Componenti Tecnologici

### 2.1 Backend & Web Framework
| Componente | Tecnologia / Versione | Note di Implementazione |
|---|---|---|
| **Linguaggio** | Python 3.12 / 3.14 | Compatibile con gli ambienti CloudLinux/Passenger e VPS |
| **Framework Web** | Django 6.1 | Gestione modelli ORM, form validation, autenticazione e sicurezza CSRF |
| **Server Applicativo (Prod)** | Gunicorn 23.0+ | Server WSGI di produzione multi-worker con monitoraggio PID |
| **Server Statici** | WhiteNoise 6.7.0 | Compilazione e distribuzione ottimizzata dei file statici con cache e gzip |
| **Database Driver** | PyMySQL 1.1+ | Driver nativo integrato con alias MySQLdb per Django |
| **SQL Engine** | sqlparse 0.6.0 | Parsing ed esecuzione query ORM |
| **Timezone** | tzdata 2026.3 | Fuso orario impostato su `Europe/Rome` (UTC+1/+2) |

---

### 2.2 Database & Persistenza
- **Ambiente Locale / Sviluppo**: SQLite (`db.sqlite3`), attivato automaticamente su Windows o con flag `USE_SQLITE=1`.
- **Ambiente di Produzione**: MySQL 8+ su host dedicato (`148.251.75.142:3306`), database `afterbit-test100` con codifica `utf8mb4` e strict transaction mode.
- **Migrazioni**: 6 migrazioni attive e sincronizzate (inclusa la migrazione `0006_alter_ticket_categoria_alter_ticket_priority`).

---

### 2.3 Frontend & Interfaccia Utente
- **Architettura UI**: Server-Side Rendering (SSR) tramite Django Template Engine.
- **Design System**: Tailwind CSS con palette istituzionale Afterbit (Navy `#1C244B`, Orange `#EC3C11`, Slate `#324A6D`, Background `#F3F5F8`).
- **Interattività Client**:
  - Combobox per **Categoria Specifica** con filtro in tempo reale istantaneo alla digitazione della prima lettera e navigazione tastiera (<kbd>↓</kbd>/<kbd>↑</kbd>/<kbd>Enter</kbd>).
  - Feedback visivo di invio form con spinner animato.
  - Ordinamento dinamico delle colonne della Dashboard tramite parametri GET sanitizzati.

---

### 2.4 Autenticazione, Permessi & Sicurezza
- **Sistema Utenti**: `django.contrib.auth` con doppio livello:
  - *Cliente*: accesso alla sola propria cronologia ticket e apertura nuove richieste.
  - *Staff/Operatore* (`is_staff = True`): accesso alla gestione globale di tutti i ticket.
- **Registrazione Clienti**: validazione email univoca, associazione profilo telefonico e verifica di sicurezza anti-bot tramite CAPTCHA matematico dinamico in sessione.
- **Protezione Dati & Privacy**: la pagina pubblica di verifica ticket (`/ticket/cerca/`) applica la doppia verifica obbligatoria (ID/Codice ticket + corrispondenza email/referente/telefono).
- **Protezione CSRF**: middleware Django con validazione token e supporto cookie su proxy inverso.

---

### 2.5 Gestione Notifiche Email
- **Server SMTP**: `smtp.afterbit.it` (Porta 587 con cifratura TLS / STARTTLS).
- **Mittente Ufficiale**: `Afterbit Assistenza <inoltrononcancellare2@afterbit.com>`.
- **Indirizzo di Notifica Interno**: `info@afterbit.com`.
- **Esecuzione Asincrona**: invio email delegato a thread daemon in background con timeout di 5 secondi per garantire che la risposta HTTP di creazione o aggiornamento del ticket sia istantanea (inferiore a 100ms) senza mai bloccare la navigazione dell'utente.

---

### 2.6 Servizi Esterni
- **Geolocalizzazione IP**: interroga l'API `ip-api.com` al momento dell'apertura del ticket con timeout di 3 secondi e fallback sicuro per ambienti localhost/privati, registrando città, regione e ISP per la sicurezza dello staff.

---

### 2.7 Architettura di Deployment & Hosting
- **Server di Produzione**: [https://test100.afterbit.it](https://test100.afterbit.it/)
- **Punto di Ingresso Web**:
  - Reverse proxy ottimizzato (`index.php`) con supporto completo per richieste HTTP `multipart/form-data` (gestione file upload via `CURLFile`) e proxying verso Gunicorn (`127.0.0.1:8000`).
  - Supporto nativo per **Phusion Passenger** tramite [`passenger_wsgi.py`](file:///c:/Users/Utente/.gemini/antigravity/scratch/afterbit_ticket/passenger_wsgi.py).
- **File Statici**: 129 risorse compilate nella directory `static/` servite con header di caching ad alta efficienza tramite WhiteNoise.
- **Storage Allegati**: memorizzazione su filesystem protetto in `media/ticket_attachments/` con validazione estensioni e limite di dimensione di 10 MB.

---

## 3. Struttura del Repository

```text
afterbit_ticket/
├── afterbit_project/          # Configurazione centrale Django
│   ├── settings.py           # Impostazioni database, email, security e statici
│   ├── urls.py               # Routing primario degli endpoint
│   ├── wsgi.py               # WSGI entry point standard
│   └── asgi.py               # ASGI entry point
├── tickets/                  # Applicazione Helpdesk
│   ├── models.py             # Ticket, UserProfile, TicketUpdate
│   ├── views.py              # Logica dashboard, ticket, auth, FAQ e ricerca
│   ├── forms.py              # Form di creazione, cambio stato e registrazione
│   ├── emails.py             # Dispatcher email asincrono per staff e clienti
│   ├── utils.py              # Geolocalizzazione IP, CAPTCHA, ownership check
│   ├── admin.py              # Configurazione del pannello Django Admin
│   ├── templates/            # Template HTML con Tailwind CSS
│   └── migrations/           # Storico schema database (6 migrazioni)
├── static/                   # File statici compilati per la produzione
├── media/                    # Cartella di upload per allegati ticket
├── passenger_wsgi.py         # Entry point per cPanel / CloudLinux Passenger
├── requirements.txt          # Dipendenze Python di produzione
├── Manuale_Operatore_Ticket.md # Manuale operativo per lo staff
└── Stack_Tecnologico.md      # Questo documento
```
