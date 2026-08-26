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
    if ip in ('127.0.0.1', '::1', 'localhost'):
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
    num1 = random.randint(1, 10)
    num2 = random.randint(1, 10)
    operator = random.choice(['+', '-'])

    if operator == '+':
        answer = num1 + num2
    else:
        # Assicura risultato positivo per semplicità
        if num1 < num2:
            num1, num2 = num2, num1
        answer = num1 - num2

    question = f"{num1} {operator} {num2}"
    request.session['captcha_question'] = question
    request.session['captcha_answer'] = str(answer)

