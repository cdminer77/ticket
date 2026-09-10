import urllib.request
import urllib.error
import json

def get_client_ip(request):
    """Estrarre l'indirizzo IP del client, gestendo eventuali header proxy."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_private_ip(ip):
    """Verifica se l'indirizzo IP appartiene a un intervallo privato o locale."""
    if not ip:
        return True
    # Loopback e localhost
    if ip in ('127.0.0.1', '::1', 'localhost', 'testserver'):
        return True
    try:
        # Controllo semplice per intervalli IPv4 privati
        if ip.startswith('10.') or ip.startswith('127.'):
            return True
        if ip.startswith('192.168.'):
            return True
        if ip.startswith('172.'):
            parts = ip.split('.')
            if len(parts) >= 2 and 16 <= int(parts[1]) <= 31:
                return True
    except Exception:
        pass
    return False

def get_ip_location(ip):
    """Interroga l'API di ip-api.com per geolocalizzare l'IP fornito."""
    if not ip or is_private_ip(ip):
        return "Sviluppo / Localhost"
    
    url = f"http://ip-api.com/json/{ip}"
    try:
        # Timeout basso (3 secondi) per non bloccare il thread dell'utente
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('status') == 'success':
                city = data.get('city', '')
                region = data.get('regionName', '')
                country = data.get('country', '')
                isp = data.get('isp', '')
                
                parts = []
                if city:
                    parts.append(city)
                if region and region != city:
                    parts.append(region)
                if country:
                    parts.append(country)
                
                location_str = ", ".join(parts)
                if isp:
                    location_str += f" (ISP: {isp})"
                return location_str or "Sconosciuto"
            else:
                return f"Errore API: {data.get('message', 'Non riuscito')}"
    except urllib.error.URLError:
        return "Servizio di geolocalizzazione non raggiungibile"
    except Exception as e:
        return f"Errore durante la geolocalizzazione: {str(e)}"


import random

def generate_captcha(request):
    """Genera una semplice domanda matematica casuale e la memorizza in sessione."""
    old_answer = request.session.get('captcha_answer')
    num1, num2, operator, answer = 1, 1, '+', 2
    for _ in range(10):
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        operator = random.choice(['+', '-'])

        if operator == '+':
            answer = num1 + num2
        else:
            if num1 < num2:
                num1, num2 = num2, num1
            answer = num1 - num2
        if str(answer) != old_answer:
            break

    question = f"{num1} {operator} {num2}"
    request.session['captcha_question'] = question
    request.session['captcha_answer'] = str(answer)


def verify_ticket_ownership(ticket, verify_contact):
    """
    Verifica se il dato di contatto fornito dall'utente (email, referente/azienda o telefono)
    corrisponde effettivamente al proprietario/richiedente del ticket per motivi di privacy.
    """
    if not ticket or not verify_contact:
        return False

    val = verify_contact.strip().lower()
    if not val:
        return False

    # 1. Verifica email dell'utente creatore
    if ticket.created_by and ticket.created_by.email:
        if ticket.created_by.email.strip().lower() == val:
            return True

    # 2. Verifica username dell'utente creatore
    if ticket.created_by and ticket.created_by.username:
        if ticket.created_by.username.strip().lower() == val:
            return True

    # 3. Verifica nominativo referente / ragione sociale del ticket
    if ticket.referente:
        ref = ticket.referente.strip().lower()
        if val == ref or val in ref or ref in val:
            return True

    # 4. Verifica recapito telefonico (dal profilo utente o formato numeri)
    if ticket.created_by and hasattr(ticket.created_by, 'profile') and ticket.created_by.profile.phone:
        phone = ticket.created_by.profile.phone.strip()
        if phone:
            if val in phone.lower():
                return True
            digits_val = ''.join(c for c in val if c.isdigit())
            digits_phone = ''.join(c for c in phone if c.isdigit())
            if digits_val and digits_phone and len(digits_val) >= 4 and len(digits_phone) >= 4:
                if digits_val == digits_phone or digits_val.endswith(digits_phone) or digits_phone.endswith(digits_val):
                    return True

    return False

