import socketserver
import threading

from django.core import mail
from django.test import SimpleTestCase, override_settings


class FakeSMTPHandler(socketserver.StreamRequestHandler):
    def write(self, line):
        self.wfile.write((line + '\r\n').encode())

    def handle(self):
        self.write('220 fake smtp')
        while line := self.rfile.readline().decode().strip():
            command = line.split(' ')[0].split(':')[0].upper()
            if command == 'DATA':
                self.write('354 go ahead')
                while self.rfile.readline().strip() != b'.':
                    pass
                self.server.received += 1
                self.write('250 queued')
            elif command == 'QUIT':
                self.write('221 bye')
                return
            else:
                self.write('250 ok')


class IndividualToEmailBackendTests(SimpleTestCase):
    def setUp(self):
        self.server = socketserver.ThreadingTCPServer(('127.0.0.1', 0), FakeSMTPHandler)
        self.server.daemon_threads = True
        self.server.received = 0
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def test_shared_connection_closed_by_caller(self):
        # juntagrico >= 2.1 sends through one connection and closes it while the mailer threads are still sending
        with override_settings(
            EMAIL_BACKEND='ortoloco.mailer.IndividualToEmailBackend',
            EMAIL_HOST='127.0.0.1', EMAIL_PORT=self.server.server_address[1],
            EMAIL_HOST_USER='', EMAIL_HOST_PASSWORD='', EMAIL_USE_TLS=False, EMAIL_USE_SSL=False,
        ):
            threads = set(threading.enumerate())
            with mail.get_connection() as connection:
                for i in range(5):
                    mail.EmailMessage(
                        'subject', 'body', 'info@ortoloco.ch', [f'to{i}@example.org'], bcc=[f'bcc{i}@example.org'],
                        connection=connection,
                    ).send()
            for thread in set(threading.enumerate()) - threads:
                if not thread.daemon:
                    thread.join(10)
        self.assertEqual(self.server.received, 10)
