import copy
import time
import threading

from django.dispatch import Signal
from juntagrico.config import Config
from juntagrico.backends.email import BaseEmailBackend
from django.core.mail.backends import smtp

batch_mail_sent = Signal()

class IndividualToEmailBackend(BaseEmailBackend, smtp.EmailBackend):
    def send_messages(self, email_messages):
        email_messages = self.clean_messages(email_messages)
        for email_message in email_messages:
            # open daemon thread that sends the emails in the background
            print('Sending mail "{}"'.format(email_message.subject))
            t = threading.Thread(
                target=self._send_batches,
                args=[email_message, Config.batch_mailer('batch_size'), Config.batch_mailer('wait_time')],
                daemon=True
            )
            t.start()
        return len(email_messages)  # pretend that all will go well

    def _send_batches(self, msg, batch_size, wait_time):
        starttime = time.time()
        tos = msg.to + msg.bcc
        plain_msg = copy.copy(msg)
        plain_msg.bcc = []
        plain_msg.to = []

        batches = 0
        sent = 0
        msgs = []
        for idx, to in enumerate(tos):
            new_message = copy.copy(plain_msg)
            new_message.to = [to]
            new_message.connection = self
            msgs.append(new_message)
            if (idx + 1) % batch_size == 0 or idx == len(tos) - 1:
                self.open()
                self.send_cleaned_messages(msgs)
                self.close()
                batches += 1
                sent += len(msgs)
                msgs = []

        mails_duration = time.time() - starttime
        print('Mailer sent {} Mails in {:.3f} seconds and {} batches'.format(sent, mails_duration, batches))
