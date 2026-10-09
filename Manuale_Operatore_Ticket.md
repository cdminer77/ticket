# Afterbit Ticket — Manuale Operatore
**Guida all'uso della piattaforma per lo staff di assistenza — Versione 2.3 (Ottobre 2026)**

---

## 1. Chi è l'operatore
L'operatore è un utente con permesso "staff" (`is_staff = True`) sull'account Django. A differenza del cliente (che accede alla sola vista dei propri ticket), l'operatore visualizza, prende in carico e gestisce tutti i ticket aperti dai clienti sull'intera piattaforma Afterbit.

I permessi di staff si gestiscono dal pannello di amministrazione Django (indirizzo `/admin/`), selezionando la casella **"Staff status"** sulla scheda dell'utente.

---

## 2. Accesso alla Piattaforma
1. Aprire l'indirizzo del portale ([https://test100.afterbit.it](https://test100.afterbit.it/)) e cliccare su **"Accedi"**.
2. Inserire il **Nome utente** (oppure l'indirizzo **email** registrato) e la **Password**.
3. Spuntare **"Ricordami"** per mantenere la sessione attiva anche dopo la chiusura del browser.
4. Dopo l'autenticazione, il sistema reindirizza automaticamente alla **Dashboard Helpdesk**.

---

## 3. La Dashboard Operativa
La Dashboard per gli operatori presenta l'etichetta identificativa **"Staff Helpdesk"** e permette il monitoraggio globale di tutte le richieste di supporto.

### 3.1 Evidenziazione Intelligente Stile Outlook (Richieste da Gestire)
La dashboard include un sistema visivo avanzato di tracciamento dello stato di lettura e lavorazione:
- **In Grassetto con Indicatore `●` (Nuovo / Da Gestire)**: quando un cliente apre un nuovo ticket o inserisce una nuova risposta, la riga del ticket appare **in grassetto marcato** con un pallino arancione e il pulsante arancione **"Gestisci →"**.
- **Carattere Normale (Già Letto / Gestito)**: non appena un operatore apre la scheda di dettaglio del ticket per visualizzarla o vi risponde, il ticket viene marcato come letto e nella dashboard torna automaticamente con font normale e pulsante **"Apri →"**.
- **Reattività Bidirezionale**: se successivamente il cliente aggiunge una nuova nota o replica, il ticket si riattiva immediatamente in grassetto segnalando la necessità di un nuovo intervento da parte dello staff.

### 3.2 Schede di stato (Tab principali)
- **★ Ticket aperti**: ticket con stato *Aperto* (`open`) o *In Lavorazione* (`in_progress`) — visualizzazione predefinita all'accesso.
- **🗑 Ticket chiusi**: storico delle richieste con stato *Risolto* (`resolved`) o *Chiuso* (`closed`).
- **📥 Tutti i ticket**: panoramica completa di tutti i ticket presenti a sistema senza alcun filtro di stato.

Ogni scheda riporta il contatore numerico aggiornato in tempo reale.

### 3.3 Badge Valutazione Clienti (Rating a 5 Stelle)
Nella tabella dei ticket chiusi/risolti viene visualizzato un badge grafico con le **stelle di soddisfazione** (da 1 a 5 stelle d'oro) rilasciate dal cliente, consentendo un monitoraggio immediato della qualità del servizio erogato.

### 3.4 Ricerca e Filtri Avanzati
- **Ricerca rapida (campo `q`)**: ricerca istantanea per numero ticket (`#ID`), codice di riferimento (`AB-AAAA-NNNNN`), oggetto, descrizione, referente o categoria.
- **Filtro Categoria Specifica**: menu a tendina per filtrare rapidamente per una delle 34 categorie tecniche (es. *Posta elettronica*, *PEC*, *Hosting*, *DNS*, *Database MySQL*, *Sicurezza Web*...).
- **Filtro Tipo di Intervento**: selezione tra *Assistenza Tecnica* e *Amministrazione*.
- **Paginazione**: selettore rapido a 25, 50 o 100 ticket per pagina.

### 3.5 Ordinamento Interattivo delle Colonne
Cliccando sulle intestazioni delle colonne della tabella:
1. **ID** (ordinamento per numero/codice ticket)
2. **Oggetto** (ordinamento alfabetico per titolo)
3. **Categoria** (ordinamento per tipologia tecnica)
4. **Utente / Referente** (ordinamento per cliente)
5. **Apertura** (ordinamento per data e ora di creazione)
6. **Risposta / Stato** (ordinamento per stato di avanzamento)
7. **Note** (ordinamento per numero di commenti/aggiornamenti)

Un secondo clic sulla medesima colonna inverte l'ordine tra **crescente (▲)** e **decrescente (▼)**.

---

## 4. Apertura e Creazione Ticket (Esperienza Cliente)
Nel modulo di creazione ticket:
- **Identità Utente Visibile**: nel pannello laterale destro viene mostrata chiaramente la scheda profilo dell'utente connesso (Nome, Email, Telefono, Azienda) e il campo *Referente* viene precompilato automaticamente.
- **Categoria Specifica con Ricerca Istantanea**: digitando la **prima lettera**, l'elenco delle opzioni si restringe immediatamente consentendo una selezione rapidissima con mouse o tastiera (<kbd>↓</kbd>/<kbd>↑</kbd> ed <kbd>Invio</kbd>).
- **Priorità Automatica**: tutte le richieste vengono registrate e trattate automaticamente con priorità **Urgente** (`urgent`).
- **Allegati**: supporto per file fino a 10 MB (PDF, immagini PNG/JPG, documenti DOCX/XLSX, log/TXT).

---

## 5. Gestione, Risposte e Layout Scheda Ticket
Cliccando su **"Gestisci →"** dalla tabella si accede alla scheda di dettaglio del ticket.

### 5.1 Timeline dei Messaggi e Nuovi Allegati
Il ticket presenta una cronologia completa stile conversazione:
- I messaggi del **Cliente** e dello **Staff** sono chiaramente distinti con etichette visive dedicate.
- **Supporto Allegati Multipli**: sia il cliente che lo staff possono inviare risposte successive allegando **nuovi file, screenshot o documenti** a ogni messaggio, senza che il cliente debba mai aprire un secondo ticket per inviare integrazioni.

### 5.2 Pannello di Controllo Staff Helpdesk (Posizionato in Evidenza)
Per velocizzare la presa in carico e l'operatività interna, il **Pannello di Gestione Staff Helpdesk** è posizionato **in evidenza subito sotto la cronologia conversazione**, prima del form di replica generale:

| Campo | Descrizione |
|---|---|
| **Modifica Stato** | Imposta lo stato: *Aperto*, *In Lavorazione*, *Risolto*, *Chiuso*. |
| **Assegna a Tecnico** | Seleziona l'operatore dello staff responsabile della presa in carico. |
| **Modifica Categoria** | Consente di rettificare la categoria tecnica della richiesta se necessario. |
| **Aggiungi Nota di Lavorazione Rapida** | Redige la diagnosi, la nota interna o la spiegazione tecnica per il cliente. |
| **Salvataggio Differenziato** | Scelta tra salvataggio puramente interno o notifica con email formale al cliente. |

### 5.3 Opzioni di Salvataggio Operatore
L'operatore dispone di due pulsanti dedicati:
1. **💾 Salva Modifiche (Senza Invio Email)**: aggiorna lo stato, l'assegnazione e le note unicamente all'interno del sistema helpdesk, senza recapitare comunicazioni all'indirizzo email del cliente (ideale per note tecniche ad uso interno).
2. **✉️ Salva & Invia al Cliente**: aggiorna il ticket e recapita contestualmente l'email di notifica al cliente con il nuovo stato e la risposta. Se lo stato passa a *Chiuso* o *Risolto*, viene inviata l'email conclusiva con invito alla valutazione a stelle.

### 5.4 Chiusura Autonoma e Controlli lato Cliente
Nel modulo di risposta del cliente sono presenti due pulsanti affiancati in basso:
- **[ 🔒 Chiudi Ticket ]**: permette al cliente di chiudere la richiesta in qualsiasi momento con finestra modale e motivazione facoltativa. All'atto della chiusura, compare subito il modulo per la **valutazione a 5 stelle**.
- **[ 📤 Invia Messaggio ]**: invia una replica con eventuale nuovo allegato e notifica lo staff.

---

## 6. Registrazioni Audio/Video Interne & Trascrizione Vocale AI (Esclusivo Staff)
La piattaforma include un modulo interno per acquisire, archiviare e analizzare registrazioni di chiamate telefoniche di assistenza tecnica o sessioni di teleassistenza a schermo condiviso.

> [!IMPORTANT]
> **Riservatezza Assoluta**: le registrazioni audio/video, le trascrizioni e le note OCR sono a **uso rigorosamente interno dello staff**. I clienti non hanno visibilità di questa sezione, non possono scaricare i media né consultare le relative trascrizioni.

### 6.1 Modalità di Acquisizione Media
Nella scheda del ticket (sezione riservata *Registrazioni Interne Staff*), l'operatore ha a disposizione due canali:
1. **Registrazione Live dal Browser (HTML5 MediaRecorder)**:
   - **Audio Microfono**: per registrare direttamente telefonate o note vocali dell'operatore con indicatore waveform live e durata in tempo reale.
   - **Video / Condivisione Schermo**: per registrare la sessione di supporto da remoto (scheda del browser, finestra dell'applicazione o intero schermo del cliente).
2. **Upload di File Esistente**: caricamento di file multimediali fino a 1 GB nei formati audio/video standard (`.mp3`, `.wav`, `.m4a`, `.ogg`, `.webm`, `.mp4`, `.mov`, `.mkv`).

### 6.2 Formula Obbligatoria Consenso Privacy (GDPR)
Per conformità alla normativa europea sulla protezione dei dati (Regolamento UE 2016/679 - GDPR), all'attivazione della registrazione compare in evidenza un riquadro speciale dorato ad alto contrasto con la dicitura da pronunciare:

> **⚖️ FORMULA OBBLIGATORIA CONSENSO GDPR DA PRONUNCIARE AL CLIENTE:**
>
> *“La informo che questa conversazione è soggetta a registrazione per scopi di miglioramento del servizio e gestione della richiesta tecnica. Continuando la conversazione, esprime il consenso al trattamento dei dati secondo la nostra informativa privacy. Acconsente a procedere?”*

- **Regola Operativa**: l'operatore deve attendere la risposta affermativa chiara dell'interlocutore prima di iniziare la trattazione del problema.
- **Valore Probatorio**: il consenso verbale espresso viene registrato e trascritto automaticamente nei primissimi secondi del file, costituendo tracciatura conforme a tutela dell'azienda e del cliente.

### 6.3 Motore di Trascrizione Vocale Locale (faster-whisper)
Appena salvata la registrazione, il sistema avvia in background l'elaborazione locale:
- **Zero Invio a Cloud Esterni**: la trascrizione viene eseguita interamente sul server locale Afterbit tramite la libreria ad altissima efficienza `faster-whisper` (CTranslate2). Nessun dato audio né conversazione viene trasmessa a provider terzi esterni.
- **Supporto Hardware Ibrido**: ottimizzazione con quantizzazione `int8` su CPU e accelerazione `float16` su GPU NVIDIA con CUDA.
- **Trascrizione Temporizzata con VAD**: il testo viene generato con blocchi temporali precisi (`[MM:SS - MM:SS]`) e filtro VAD (*Voice Activity Detection*) per la soppressione automatica dei silenzi e delle pause.
- **Cache in Memoria**: il modello neurale viene mantenuto in memoria per evitare ricaricamenti da disco a ogni sessione, garantendo avvii immediati.

### 6.4 Analisi OCR Automatica dei Fotogrammi Video
In caso di registrazioni video o schermate condivise:
- Il motore estrae automaticamente fotogrammi salienti ad intervalli regolari (1 fotogramma ogni 45 secondi) tramite **FFmpeg**.
- I fotogrammi vengono analizzati tramite motore OCR (**Tesseract**) per identificare automaticamente:
  - **Errori di sistema e avvisi critici** (*Exception*, *Fatal error*, *Error 500/404*, *Timeout*, *Access Denied*, *Stack trace*).
  - **Indirizzi IP e porte rilevati a schermo**.
  - **URL e domini web** coinvolti nel problema.
- Il report OCR viene allegato direttamente alla scheda della registrazione per velocizzare la diagnosi tecnica dello staff.

### 6.5 Gestione da Linea di Comando (CLI Management Command)
Per elaborazioni massive o recupero di file in errore/interrotti, gli amministratori di sistema possono eseguire via terminale:
```bash
# Elabora tutte le registrazioni in attesa
python manage.py transcribe_recordings

# Elabora una registrazione specifica per ID
python manage.py transcribe_recordings --id 12

# Ritenta anche le registrazioni con stato 'failed'
python manage.py transcribe_recordings --retry-failed
```

---

## 7. Sistema di Valutazione e Feedback a 5 Stelle
Quando un ticket viene marcato come *Risolto* o *Chiuso*:
1. Nella pagina del ticket compare il widget interattivo di gradimento con **5 stelle animate**.
2. Il cliente può selezionare il proprio voto (da 1 a 5) e facoltativamente lasciare una recensione/commento.
3. Al salvataggio, il rating viene registrato con data e ora e diventa visibile sia allo staff che al cliente.
4. L'email di chiusura intervento include un link diretto per rilasciare il feedback anche a distanza di tempo.

---

## 8. Sistema di Notifiche Email Automatiche
Le comunicazioni email viaggiano tramite il server SMTP dedicato di Afterbit (`smtp.afterbit.it`) in modalità asincrona non bloccante:

| Evento | Destinatario | Contenuto |
|---|---|---|
| **Apertura nuovo ticket** | Staff Afterbit (`info@afterbit.com`) | Notifica interna con dati cliente, categoria, tipo intervento e descrizione problema |
| **Ricevuta al cliente** | Email del Cliente | Conferma formale di ricezione con ID ticket, oggetto e categoria |
| **Nuova risposta del cliente** | Staff Afterbit (`info@afterbit.com`) | Avviso immediato con testo del messaggio del cliente ed eventuale allegato |
| **Aggiornamento di stato/staff** | Email del Cliente | Notifica di cambio stato (es. in lavorazione) con risposta del tecnico e codice di richiamo |
| **Chiusura intervento** | Email del Cliente | Comunicazione finale di risoluzione problema con riepilogo e link alla valutazione a 5 stelle |

---

## 9. Parametri Ufficiali di Configurazione Email (Riferimento Rapido FAQ 7)
In caso di supporto a clienti che necessitano di configurare client di posta (Outlook, Thunderbird, Apple Mail, Smartphone):

- **IMAP (Posta in Arrivo):** `mail.afterbit.it` — Porta SSL: `993` | Porta No SSL: `143`
- **POP3 (Posta in Arrivo):** `mail.afterbit.it` — Porta SSL: `995` | Porta No SSL: `110`
- **SMTP (Posta in Uscita):** `smtp.afterbit.it` — Porta SSL: `465` | Porta No SSL: `25` (Autenticazione richiesta)
- **PEC:** IMAP `imaps.pec.aruba.it` (Porta 993) | SMTP `smtps.pec.aruba.it` (Porta 465)

---

## 10. Verifica e Ricerca Pubblica Ticket
Per i clienti che desiderano verificare l'avanzamento della propria richiesta senza effettuare il login, è disponibile la pagina **/ticket/cerca/**:
- A tutela della riservatezza e conformità GDPR, è richiesta una **doppia verifica**: inserimento del **Codice Ticket** unito a un dato di riconoscimento (email, nominativo referente/azienda o recapito telefonico registrato).

---

## 11. Buone Pratiche per gli Operatori
1. **Presa in carico immediata**: Assegnare il ticket al proprio nominativo non appena si inizia la diagnosi per informare i colleghi.
2. **Promemoria GDPR**: Leggere sempre la formula di consenso privacy ad alta voce prima di qualsiasi registrazione vocale o teleassistenza.
3. **Note chiare e professionali**: Quando si utilizza *Salva & Invia al Cliente*, formulare risposte comprensibili spiegando i passaggi eseguiti.
4. **Allegati di supporto**: Inviare schermate o file di istruzioni direttamente tramite il campo allegato della risposta.
5. **Monitoraggio del Rating**: Verificare i punteggi di gradimento (1-5 stelle) per mantenere standard qualitativi elevati.
