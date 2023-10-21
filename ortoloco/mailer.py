import copy
import time

from django.core import mail


class Mailer:
    def send(msg):
        print('Sending mail "{}"'.format(msg.subject))
        starttime = time.time()
        tos = msg.to + msg.bcc
        plain_msg = copy.copy(msg)
        plain_msg.bcc = []
        plain_msg.to = []
        batchsize = 500
        batches = 0
        sent = 0
        msgs = []
        for idx, to in enumerate(tos):
            new_message = copy.copy(plain_msg)
            new_message.to = [to]
            msgs.append(new_message)
            if (idx + 1) % batchsize == 0 or idx == len(tos) - 1:
                connection = mail.get_connection()
                connection.send_messages(msgs)
                batches += 1
                sent += len(msgs)
                msgs = []

        mails_duration = time.time() - starttime
        print('Mailer sent {} Mails in {:.3f} seconds and {} batches'.format(sent, mails_duration, batches))
