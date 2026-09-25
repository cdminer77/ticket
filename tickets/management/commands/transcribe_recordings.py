from django.core.management.base import BaseCommand
from tickets.models import TicketRecording
from tickets.service_transcription import process_ticket_recording, check_ffmpeg_available


class Command(BaseCommand):
    help = "Esegue la trascrizione vocale locale delle registrazioni interne in attesa (pending o failed)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            type=int,
            help='ID specifico del TicketRecording da trascrivere',
        )
        parser.add_argument(
            '--retry-failed',
            action='store_true',
            help='Ritenta anche le registrazioni con stato failed',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Verifica dipendenze locali..."))
        ffmpeg_ok = check_ffmpeg_available()
        if ffmpeg_ok:
            self.stdout.write(self.style.SUCCESS("✓ FFmpeg rilevato."))
        else:
            self.stdout.write(self.style.WARNING("! FFmpeg non rilevato in PATH. Per i file video potrebbe fallire l'estrazione audio."))

        rec_id = options.get('id')
        retry_failed = options.get('retry_failed')

        if rec_id:
            recordings = TicketRecording.objects.filter(id=rec_id)
            if not recordings.exists():
                self.stdout.write(self.style.ERROR(f"Nessun TicketRecording trovato con ID {rec_id}"))
                return
        else:
            statuses = ['pending']
            if retry_failed:
                statuses.append('failed')
            recordings = TicketRecording.objects.filter(status__in=statuses).order_by('created_at')

        total = recordings.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Nessuna registrazione in attesa di trascrizione."))
            return

        self.stdout.write(self.style.NOTICE(f"Trovate {total} registrazioni da elaborare."))

        for rec in recordings:
            self.stdout.write(f"Inizio elaborazione: #{rec.id} ({rec.title or rec.recording_file.name})...")
            process_ticket_recording(rec.id)
            rec.refresh_from_db()
            if rec.status == 'completed':
                self.stdout.write(self.style.SUCCESS(f"✓ Trascritto con successo: #{rec.id}"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ Errore su #{rec.id}: {rec.error_message}"))
