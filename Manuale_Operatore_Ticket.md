# Afterbit Ticket — Manuale Operatore
**Guida all'uso della piattaforma per lo staff di assistenza — Versione 2.0 (Settembre 2026)**

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

### 3.1 Schede di stato (Tab principali)
- **★ Ticket aperti**: ticket con stato *Aperto* (`open`) o *In Lavorazione* (`in_progress`) — visualizzazione predefinita all'accesso.
- **🗑 Ticket chiusi**: storico delle richieste con stato *Risolto* (`resolved`) o *Chiuso* (`closed`).
- **📥 Tutti i ticket**: panoramica completa di tutti i ticket presenti a sistema senza alcun filtro di stato.

Ogni scheda riporta il contatore numerico aggiornato in tempo reale.

### 3.2 Ricerca e Filtri Avanzati
- **Ricerca rapida (campo `q`)**: ricerca istantanea per numero ticket (`#ID`), codice di riferimento (`AB-AAAA-NNNNN`), oggetto, descrizione, referente o categoria.
- **Filtro Categoria Specifica**: menu a tendina per filtrare rapidamente per una delle 34 categorie tecniche (es. *Posta elettronica*, *PEC*, *Hosting*, *DNS*, *Database MySQL*, *Sicurezza Web*...).
- **Filtro Tipo di Intervento**: selezione tra *Assistenza Tecnica* e *Amministrazione*.
- **Paginazione**: selettore rapido a 25, 50 o 100 ticket per pagina.

### 3.3 Ordinamento Interattivo delle Colonne
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

## 4. Apertura e Creazione Ticket
Nel modulo di creazione ticket:
- **Categoria Specifica con Ricerca Istantanea**: il campo dispone di un menu a tendina interattivo; digitando la **prima lettera**, l'elenco delle opzioni si restringe immediatamente consentendo una selezione rapidissima con mouse o tastiera (<kbd>↓</kbd>/<kbd>↑</kbd> ed <kbd>Invio</kbd>).
- **Priorità Automatica**: tutte le richieste vengono registrate e trattate automaticamente con priorità **Urgente** (`urgent`), senza richiedere selezioni manuali da parte dell'utente.
- **Allegati**: supporto per file fino a 10 MB (PDF, immagini PNG/JPG, documenti DOCX/XLSX, log/TXT).

---

## 5. Gestione e Lavorazione del Singolo Ticket
Cliccando su **"Gestisci →"** dalla tabella si accede alla scheda di dettaglio del ticket.

### 5.1 Pannello di Gestione Staff Helpdesk
Nel pannello riservato agli operatori sono disponibili i seguenti comandi:

| Campo | Descrizione |
|---|---|
| **Modifica Stato** | Imposta lo stato: *Aperto*, *In Lavorazione*, *Risolto*, *Chiuso*. |
| **Assegna a Tecnico** | Seleziona l'operatore dello staff responsabile della presa in carico. |
| **Modifica Categoria** | Consente di rettificare la categoria tecnica della richiesta se necessario. |
| **Aggiungi Nota di Lavorazione** | Spazio per redigere la diagnosi, gli interventi eseguiti o la risposta per il cliente. |

### 5.2 Opzioni di Salvataggio
L'operatore dispone di due pulsanti dedicati:
1. **💾 Salva Modifiche (Senza Invio Email)**: aggiorna lo stato, l'assegnazione e le note unicamente all'interno del sistema helpdesk, senza recapitare comunicazioni all'indirizzo email del cliente (ideale per appunti tecnici interni).
2. **✉️ Salva & Invia al Cliente**: aggiorna il ticket e recapita contestualmente l'email di notifica al cliente con il nuovo stato e la nota di risposta. Se lo stato passa a *Chiuso*, viene inviata l'email conclusiva di chiusura intervento.

### 5.3 Codice di Riferimento Univoco
Al momento della prima assegnazione a un tecnico (o alla creazione), il sistema genera un codice univoco nel formato **`AB-AAAA-NNNNN`** (es. `AB-2026-00012`), utile per richiamare la pratica in futuro.

---

## 6. Sistema di Notifiche Email Automatiche
Le comunicazioni email viaggiano tramite il server SMTP dedicato di Afterbit (`smtp.afterbit.it`) in modalità asincrona non bloccante:

| Evento | Destinatario | Contenuto |
|---|---|---|
| **Apertura nuovo ticket** | Staff Afterbit (`info@afterbit.com`) | Notifica interna con dati cliente, categoria, tipo intervento e descrizione problema |
| **Ricevuta al cliente** | Email del Cliente | Conferma formale di ricezione con ID ticket, oggetto e categoria |
| **Aggiornamento di stato** | Email del Cliente | Notifica di cambio stato (es. preso in carico / in lavorazione) con note del tecnico e codice di richiamo |
| **Chiusura intervento** | Email del Cliente | Comunicazione finale di risoluzione problema con riepilogo e codice di riferimento |

---

## 7. Verifica e Ricerca Pubblica Ticket
Per i clienti che desiderano verificare l'avanzamento della propria richiesta senza effettuare il login, è disponibile la pagina **/ticket/cerca/**:
- A tutela della riservatezza e conformità GDPR, è richiesta una **doppia verifica**: inserimento del **Codice Ticket** unito a un dato di riconoscimento (email, nominativo referente/azienda o recapito telefonico registrato).

---

## 8. Buone Pratiche per gli Operatori
1. **Presa in carico immediata**: Assegnare il ticket al proprio nominativo non appena si inizia la diagnosi per informare i colleghi.
2. **Note chiare e professionali**: Quando si utilizza *Salva & Invia al Cliente*, formulare risposte comprensibili spiegando i passaggi eseguiti.
3. **Chiusura tempestiva**: Una volta risolta l'anomalia, impostare lo stato su *Chiuso* con *Salva & Invia al Cliente* per rilasciare la ricevuta finale.
