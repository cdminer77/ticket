

Ecco gli account pronti e verificati per eseguire tutti i test sul portale [**test100.afterbit.it**](https://test100.afterbit.it) (o in locale su `127.0.0.1:8000`):

---

### 👤 Account Cliente (per testare creazione ticket, risposte con allegati, chiusura autonoma e feedback a stelle)

| Username | Password | Ruolo / Note |
| :--- | :--- | :--- |
| **`test_client`** | `PasswordSicura123!` | Account Cliente standard |
| **`Marco`** | `PasswordSicura123!` | Account Cliente |
| **`test_user_1788940537`** | `PasswordSicura123!` | Account Cliente |

---

### 🛠️ Account Staff / Operatore Tecnico (per testare presa in carico, risposte staff e risoluzione)

| Username | Password | Ruolo / Note |
| :--- | :--- | :--- |
| **`test_staff`** | `PasswordSicura123!` | Operatore Helpdesk (Staff) |
| **`Afterbit`** | *(Password amministratore personale)* | SuperAdmin / Staff |
| **`claudio`** / **`cdalloro`** | *(Password personali)* | SuperAdmin / Staff |

---

### 🧪 Percorso di Test Consigliato:
1. **Login come Cliente (`test_client`)**:
   - Clicca su **"Nuovo Ticket"** $\rightarrow$ verifica che nel box a destra compaia il profilo utente connesso.
   - Crea un ticket con o senza allegato.
2. **Login come Staff (`test_staff`)**:
   - Apri il ticket, cambia lo stato in **"In Lavorazione"** e invia una risposta con un file allegato.
3. **Ritorno come Cliente (`test_client`)**:
   - Rispondi allegando un nuovo file (senza creare un nuovo ticket).
   - Chiudi autonomamente il ticket con il pulsante **"Chiudi Ticket"** (o lascia che lo risolva lo staff).
   - Inserisci la valutazione a **5 stelle** con eventuale commento.
4. **FAQ 7**:
   - Vai alla pagina **FAQ** e verifica i parametri email / PEC aggiornati.