import logging
import os
import shutil
import subprocess
import threading
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from .models import TicketRecording

logger = logging.getLogger(__name__)

# Directory per modelli whisper locali o temporanei
WHISPER_MODEL_SIZE = getattr(settings, 'WHISPER_MODEL_SIZE', 'small')
FFMPEG_BINARY = getattr(settings, 'FFMPEG_BINARY', shutil.which('ffmpeg') or 'ffmpeg')


def check_ffmpeg_available():
    """Verifica se il binario ffmpeg è disponibile nel sistema."""
    if shutil.which(FFMPEG_BINARY):
        return True
    try:
        res = subprocess.run([FFMPEG_BINARY, '-version'], capture_output=True, text=True, timeout=5)
        return res.returncode == 0
    except Exception:
        return False


def extract_audio_if_needed(media_path: Path) -> Path:
    """
    Se il file è un video (mp4, webm, mov, mkv), estrae la traccia audio a 16kHz mono WAV tramite ffmpeg.
    Se è già un file audio compatibile o ffmpeg non è presente, ritorna il percorso originale.
    """
    ext = media_path.suffix.lower()
    if ext in ['.mp4', '.mkv', '.mov', '.webm', '.avi']:
        output_wav = media_path.with_suffix('.extracted_16k.wav')
        if check_ffmpeg_available():
            try:
                cmd = [
                    FFMPEG_BINARY,
                    '-y',
                    '-i', str(media_path),
                    '-vn',                # no video
                    '-acodec', 'pcm_s16le',
                    '-ar', '16000',       # frequenza ideale per whisper
                    '-ac', '1',           # mono
                    str(output_wav)
                ]
                subprocess.run(cmd, check=True, capture_output=True, timeout=600)
                if output_wav.exists() and output_wav.stat().st_size > 0:
                    return output_wav
            except Exception as e:
                logger.error(f"Errore durante l'estrazione audio ffmpeg per {media_path}: {e}")
    return media_path


def run_local_whisper_transcription(audio_file_path: Path):
    """
    Esegue la trascrizione vocale sul server usando faster-whisper.
    Genera sia la trascrizione con timestamp sia il testo consolidato.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError(
            "La libreria 'faster-whisper' non è installata nell'ambiente Python. "
            "Installa con: pip install faster-whisper"
        )

    # Inizializza il modello locale (su CPU con quantizzazione int8 o float16 se GPU disponibile)
    device = "cpu"
    compute_type = "int8"
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            compute_type = "float16"
    except Exception:
        pass

    logger.info(f"Caricamento modello faster-whisper ({WHISPER_MODEL_SIZE}) su device={device}, compute_type={compute_type}...")
    model = WhisperModel(WHISPER_MODEL_SIZE, device=device, compute_type=compute_type)

    segments, info = model.transcribe(
        str(audio_file_path),
        language="it",
        beam_size=5,
        vad_filter=True  # Rimuove il silenzio prolungato nelle call
    )

    formatted_lines = []
    plain_text_parts = []

    for segment in segments:
        start_min = int(segment.start // 60)
        start_sec = int(segment.start % 60)
        end_min = int(segment.end // 60)
        end_sec = int(segment.end % 60)
        timestamp_str = f"[{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}]"
        clean_text = segment.text.strip()
        if clean_text:
            formatted_lines.append(f"{timestamp_str} {clean_text}")
            plain_text_parts.append(clean_text)

    transcript_full = "\n".join(formatted_lines)
    duration_detected = int(info.duration) if hasattr(info, 'duration') and info.duration else None

    return transcript_full, duration_detected


import re
import tempfile

def extract_video_keyframes(video_path: Path, max_frames: int = 12) -> list[tuple[float, Path]]:
    """
    Estrae fotogrammi salienti dal video a intervalli regolari (es. ogni 30 o 60 secondi)
    oppure basandosi sul rilevamento cambi di scena.
    Ritorna una lista di tuple (timestamp_secondi, percorso_immagine_jpg).
    """
    if not check_ffmpeg_available():
        return []

    temp_dir = Path(tempfile.mkdtemp(prefix="video_frames_"))
    # Estrae 1 fotogramma ogni 45 secondi
    output_pattern = temp_dir / "frame_%04d.jpg"
    try:
        cmd = [
            FFMPEG_BINARY,
            '-y',
            '-i', str(video_path),
            '-vf', 'fps=1/45,scale=1280:-1',  # 1 frame ogni 45s, scala mantenendo proporzioni
            '-q:v', '2',
            str(output_pattern)
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=600)

        frame_files = sorted(list(temp_dir.glob("frame_*.jpg")))
        results = []
        for idx, f in enumerate(frame_files[:max_frames]):
            timestamp_sec = idx * 45.0
            results.append((timestamp_sec, f))
        return results
    except Exception as e:
        logger.error(f"Errore durante l'estrazione frame video per {video_path}: {e}")
        return []


def analyze_video_frames_ocr(keyframes: list[tuple[float, Path]]) -> str:
    """
    Esegue OCR sui fotogrammi estratti per rilevare:
    - Messaggi di errore (Fatal error, Exception, Error 404/500, Timeout, Access Denied)
    - Indirizzi IP e Porte
    - Domini e URL
    - Comandi console / shell
    Utilizza pytesseract se disponibile sul server.
    """
    if not keyframes:
        return ""

    try:
        import pytesseract
        from PIL import Image
        has_ocr = True
    except ImportError:
        has_ocr = False

    detected_findings = []
    seen_snippets = set()

    for timestamp_sec, frame_path in keyframes:
        time_str = f"{int(timestamp_sec // 60):02d}:{int(timestamp_sec % 60):02d}"
        text_content = ""

        if has_ocr:
            try:
                img = Image.open(frame_path)
                text_content = pytesseract.image_to_string(img, lang='ita+eng')
            except Exception as e:
                logger.warning(f"Errore OCR sul fotogramma {frame_path}: {e}")

        if not text_content:
            continue

        # Ricerca pattern di interesse (errori, IP, domini, log)
        lines = [line.strip() for line in text_content.splitlines() if line.strip()]
        relevant_lines = []

        # Regex per IP
        ip_matches = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b', text_content)
        # Regex per URL o domini
        url_matches = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text_content)

        # Filtro parole chiave critiche
        keywords = ['error', 'exception', 'fatal', 'failed', 'warning', 'denied', 'timeout', 'sql', 'database', 'stack trace']
        for line in lines:
            line_lower = line.lower()
            if any(k in line_lower for k in keywords):
                if line not in seen_snippets and len(line) > 5:
                    relevant_lines.append(f"⚠️ {line}")
                    seen_snippets.add(line)

        finding_parts = []
        if relevant_lines:
            finding_parts.append("\n  " + "\n  ".join(relevant_lines[:4]))
        if ip_matches:
            finding_parts.append(f"📡 IP rilevati a schermo: {', '.join(set(ip_matches[:5]))}")
        if url_matches:
            finding_parts.append(f"🌐 URL rilevati a schermo: {', '.join(set(url_matches[:5]))}")

        if finding_parts:
            detected_findings.append(f"• Al minuto [{time_str}]:\n  " + "\n  ".join(finding_parts))

    if detected_findings:
        return "Rilevamenti automatici dai fotogrammi video (OCR):\n" + "\n\n".join(detected_findings)
    elif has_ocr:
        return "Nessun errore critico o configurazione di rilievo identificata a schermo dai fotogrammi analizzati."
    else:
        return "OCR non attivo: per abilitare la scansione automatica dei testi a video, installare 'pytesseract' e l'eseguibile tesseract-ocr."


def process_ticket_recording(recording_id: int):
    """
    Elabora una singola registrazione TicketRecording:
    1. Aggiorna lo stato in 'processing'
    2. Estrae l'audio se si tratta di un video
    3. Esegue la trascrizione locale via faster-whisper
    4. Se video, estrae i fotogrammi ed esegue l'analisi OCR
    5. Aggiorna il modello con il testo, durata, note estratte e stato 'completed'
    """
    try:
        recording = TicketRecording.objects.get(id=recording_id)
    except TicketRecording.DoesNotExist:
        logger.error(f"TicketRecording #{recording_id} non trovato.")
        return

    recording.status = 'processing'
    recording.save(update_fields=['status'])

    file_path = Path(recording.recording_file.path)
    if not file_path.exists():
        recording.status = 'failed'
        recording.error_message = f"File non trovato sul disco: {file_path}"
        recording.save(update_fields=['status', 'error_message'])
        return

    extracted_audio_path = None
    keyframes = []
    try:
        # 1. Se video, estrai fotogrammi per analisi OCR
        if recording.media_type == 'video' or file_path.suffix.lower() in ['.mp4', '.mkv', '.mov', '.webm', '.avi']:
            keyframes = extract_video_keyframes(file_path)
            extracted_notes = analyze_video_frames_ocr(keyframes)
            if extracted_notes:
                recording.extracted_notes = extracted_notes

        # 2. Estrai traccia audio se video
        extracted_audio_path = extract_audio_if_needed(file_path)

        # 3. Trascrizione vocale
        transcript_text, duration = run_local_whisper_transcription(extracted_audio_path)

        recording.transcript = transcript_text
        if duration:
            recording.duration_seconds = duration
        recording.status = 'completed'
        recording.error_message = ""
        recording.save()
        logger.info(f"TicketRecording #{recording_id} completato con successo.")

    except Exception as e:
        logger.exception(f"Errore durante l'elaborazione del TicketRecording #{recording_id}: {e}")
        recording.status = 'failed'
        recording.error_message = str(e)
        recording.save(update_fields=['status', 'error_message'])

    finally:
        # Pulizia file temporaneo WAV se era stato creato a parte
        if extracted_audio_path and extracted_audio_path != file_path and extracted_audio_path.exists():
            try:
                extracted_audio_path.unlink()
            except Exception:
                pass
        # Pulizia cartella fotogrammi temporanei
        if keyframes:
            for _, kf in keyframes:
                try:
                    kf.unlink()
                except Exception:
                    pass
            try:
                keyframes[0][1].parent.rmdir()
            except Exception:
                pass


def queue_recording_transcription(recording_id: int):
    """
    Lancia l'elaborazione in background tramite un thread daemon per non bloccare
    la richiesta HTTP della web app Django.
    In un secondo momento può essere ricollegato direttamente a Celery / Django-Q.
    """
    thread = threading.Thread(
        target=process_ticket_recording,
        args=(recording_id,),
        daemon=True,
        name=f"TranscribeRecording-{recording_id}"
    )
    thread.start()
