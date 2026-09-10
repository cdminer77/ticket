# Guida Operativa alla Pubblicazione su cPanel (Opzione A - Setup Python App)

Tutti i file del progetto sono pronti e predisposti per la pubblicazione con **Phusion Passenger** e **WhiteNoise**.

---

## 1. File Principali di Deployment inclusi nel progetto

- **`passenger_wsgi.py`**: file di avvio per il server web cPanel (WSGI entry point).
- **`requirements.txt`**: pacchetti Python necessari (Django, PyMySQL, WhiteNoise, Gunicorn, tzdata, sqlparse).
- **`static/`**: cartella dei file statici già compilati con `collectstatic` (CSS, loghi, icone).
- **`tmp/restart.txt`**: file per il riavvio immediato dell'applicazione.

---

## 2. Passaggi Operativi su cPanel

### Passo 1: Caricamento dei file
Carica i file del progetto sul tuo account hosting (via **SFTP/SSH** o tramite il **File Manager** di cPanel) all'interno della cartella di destinazione (es. `/home/username/afterbit_ticket` o `/home/username/test100`).

### Passo 2: Creazione / Configurazione dell'Applicazione in cPanel
1. Entra nel pannello **cPanel**.
2. Clicca sull'icona **Setup Python App** (nella sezione *Software*).
3. Se l'applicazione esiste già, clicca su **Edit**, altrimenti clicca su **Create Application**:
   - **Python version**: `3.12` (o la versione 3.x disponibile)
   - **Application root**: `afterbit_ticket` (o il percorso relativo della cartella caricata)
   - **Application URL**: seleziona il dominio/sottodominio (es. `test100.afterbit.it`)
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`
4. Clicca su **Save** / **Create**.

### Passo 3: Configurazione Variabili d'Ambiente (in cPanel)
Nella stessa schermata di *Setup Python App*, nella sezione **Environment variables**, aggiungi:
- **`DJANGO_ENV`**: `production`
- **`AFTERBIT_EMAIL_PASSWORD`**: `fn_24021972_19122007`

### Passo 4: Esecuzione Comandi (Terminale cPanel o SSH)
In cima alla schermata di cPanel troverai il comando per attivare il virtualenv (es: `source /home/username/virtualenv/afterbit_ticket/3.12/bin/activate`).
Copialo nel terminale ed esegui:

```bash
# 1. Attiva l'ambiente (sostituisci con il tuo percorso generato da cPanel)
source /home/username/virtualenv/afterbit_ticket/3.12/bin/activate

# 2. Spostati nella cartella del progetto
cd /home/username/afterbit_ticket

# 3. Installa le dipendenze
pip install -r requirements.txt

# 4. Esegui le migrazioni del database MySQL di produzione
python manage.py migrate

# 5. Raccogli i file statici
python manage.py collectstatic --noinput

# 6. (Se non già creato) Crea l'amministratore
python manage.py createsuperuser
```

### Passo 5: Riavvio dell'Applicazione
- Clicca sul pulsante **Restart** nella pagina di cPanel (oppure da terminale dai il comando `touch tmp/restart.txt`).
- L'applicazione sarà subito attiva e raggiungibile sul dominio configurato con HTTPS!
