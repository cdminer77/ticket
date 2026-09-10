# Afterbit Ticket — Manuale Operatore
**Guida all'uso della piattaforma per lo staff di assistenza — Versione 2.1 (Settembre 2026)**

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

### 3.2 Badge Valutazione Clienti (Rating a 5 Stelle)
Nella tabella dei ticket chiusi/risolti viene visualizzato un badge grafico con le **stelle di soddisfazione** (da 1 a 5 stelle d'oro) rilasciate dal cliente, consentendo un monitoraggio immediato della qualità del servizio erogato.

### 3.3 Ricerca e Filtri Avanzati
- **Ricerca rapida (campo `q`)**: ricerca istantanea per numero ticket (`#ID`), codice di riferimento (`AB-AAAA-NNNNN`), oggetto, descrizione, referente o categoria.
- **Filtro Categoria Specifica**: menu a tendina per filtrare rapidamente per una delle 34 categorie tecniche (es. *Posta elettronica*, *PEC*, *Hosting*, *DNS*, *Database MySQL*, *Sicurezza Web*...).
- **Filtro Tipo di Intervento**: selezione tra *Assistenza Tecnica* e *Amministrazione*.
- **Paginazione**: selettore rapido a 25, 50 o 100 ticket per pagina.

### 3.4 Ordinamento Interattivo delle Colonne
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

## 5. Gestione, Risposte e Thread di Conversazione
Cliccando su **"Gestisci →"** dalla tabella si accede alla scheda di dettaglio del ticket.

### 5.1 Timeline dei Messaggi e Nuovi Allegati
Il ticket presenta una cronologia completa stile conversazione:
- I messaggi del **Cliente** e dello **Staff** sono chiaramente distinti con etichette visive dedicate.
- **Supporto Allegati Multipli**: sia il cliente che lo staff possono inviare risposte successive allegando **nuovi file, screenshot o documenti** a ogni messaggio, senza che il cliente debba mai aprire un secondo ticket per inviare integrazioni.

### 5.2 Pannello di Controllo Staff Helpdesk
Nel pannello riservato agli operatori sono disponibili i seguenti comandi:

| Campo | Descrizione |
|---|---|
| **Modifica Stato** | Imposta lo stato: *Aperto*, *In Lavorazione*, *Risolto*, *Chiuso*. |
| **Assegna a Tecnico** | Seleziona l'operatore dello staff responsabile della presa in carico. |
| **Modifica Categoria** | Consente di rettificare la categoria tecnica della richiesta se necessario. |
| **Aggiungi Risposta / Nota** | Redige la diagnosi, la risposta per il cliente o gli aggiornamenti. |
| **Nuovo Allegato** | Permette allo staff di inviare patch, guide PDF o report al cliente. |

### 5.3 Opzioni di Salvataggio Operatore
L'operatore dispone di due pulsanti dedicati:
1. **💾 Salva Modifiche (Senza Invio Email)**: aggiorna lo stato, l'assegnazione e le note unicamente all'interno del sistema helpdesk, senza recapitare comunicazioni all'indirizzo email del cliente (ideale per note tecniche ad uso interno).
2. **✉️ Salva & Invia al Cliente**: aggiorna il ticket e recapita contestualmente l'email di notifica al cliente con il nuovo stato e la risposta. Se lo stato passa a *Chiuso* o *Risolto*, viene inviata l'email conclusiva con invito alla valutazione a stelle.

### 5.4 Chiusura Autonoma da Parte del Cliente
Il cliente ha a disposizione il pulsante **"Chiudi Ticket"** per chiudere la richiesta in qualsiasi momento in totale autonomia. All'atto della chiusura:
- Lo stato passa a *Chiuso* (`closed`).
- Compare subito il modulo interattivo per rilasciare la **valutazione a 5 stelle** e un commento sull'esperienza.

---

## 6. Sistema di Valutazione e Feedback a 5 Stelle
Quando un ticket viene marcato come *Risolto* o *Chiuso*:
1. Nella pagina del ticket compare il widget interattivo di gradimento con **5 stelle animate**.
2. Il cliente può selezionare il proprio voto (da 1 a 5) e facoltativamente lasciare una recensione/commento.
3. Al salvataggio, il rating viene registrato con data e ora e diventa visibile sia allo staff che al cliente.
4. L'email di chiusura intervento include un link diretto per rilasciare il feedback anche a distanza di tempo.

---

## 7. Sistema di Notifiche Email Automatiche
Le comunicazioni email viaggiano tramite il server SMTP dedicato di Afterbit (`smtp.afterbit.it`) in modalità asincrona non bloccante:

| Evento | Destinatario | Contenuto |
|---|---|---|
| **Apertura nuovo ticket** | Staff Afterbit (`info@afterbit.com`) | Notifica interna con dati cliente, categoria, tipo intervento e descrizione problema |
| **Ricevuta al cliente** | Email del Cliente | Conferma formale di ricezione con ID ticket, oggetto e categoria |
| **Nuova risposta del cliente** | Staff Afterbit (`info@afterbit.com`) | Avviso immediato con testo del messaggio del cliente ed eventuale allegato |
| **Aggiornamento di stato/staff** | Email del Cliente | Notifica di cambio stato (es. in lavorazione) con risposta del tecnico e codice di richiamo |
| **Chiusura intervento** | Email del Cliente | Comunicazione finale di risoluzione problema con riepilogo e link alla valutazione a 5 stelle |

---

## 8. Parametri Ufficiali di Configurazione Email (Riferimento Rapido FAQ 7)
In caso di supporto a clienti che necessitano di configurare client di posta (Outlook, Thunderbird, Apple Mail, Smartphone):

- **IMAP (Posta in Arrivo):** `mail.afterbit.it` — Porta SSL: `993` | Porta No SSL: `143`
- **POP3 (Posta in Arrivo):** `mail.afterbit.it` — Porta SSL: `995` | Porta No SSL: `110`
- **SMTP (Posta in Uscita):** `smtp.afterbit.it` — Porta SSL: `465` | Porta No SSL: `25` (Autenticazione richiesta)
- **PEC:** IMAP `imaps.pec.aruba.it` (Porta 993) | SMTP `smtps.pec.aruba.it` (Porta 465)

---

## 9. Verifica e Ricerca Pubblica Ticket
Per i clienti che desiderano verificare l'avanzamento della propria richiesta senza effettuare il login, è disponibile la pagina **/ticket/cerca/**:
- A tutela della riservatezza e conformità GDPR, è richiesta una **doppia verifica**: inserimento del **Codice Ticket** unito a un dato di riconoscimento (email, nominativo referente/azienda o recapito telefonico registrato).

---

## 10. Buone Pratiche per gli Operatori
1. **Presa in carico immediata**: Assegnare il ticket al proprio nominativo non appena si inizia la diagnosi per informare i colleghi.
2. **Note chiare e professionali**: Quando si utilizza *Salva & Invia al Cliente*, formulare risposte comprensibili spiegando i passaggi eseguiti.
3. **Allegati di supporto**: Inviare schermate o file di istruzioni direttamente tramite il campo allegato della risposta.
4. **Monitoraggio del Rating**: Verificare i punteggi di gradimento (1-5 stelle) per mantenere standard qualitativi elevati.
