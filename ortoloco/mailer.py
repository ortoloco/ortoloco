import copy
import time

from django.core import mail


class Mailer:
    def send(msg):
        starttime = time.time()
        tos = msg.to + msg.bcc
        plain_msg = copy.copy(msg)
        plain_msg.bcc = []
        plain_msg.to = []
        msgs = []
        for to in tos:
            new_message = copy.copy(plain_msg)
            new_message.to =[to]
            msgs.append(new_message)
        connection = mail.get_connection()
        connection.send_messages(msgs)

        mails_duration = time.time() - starttime
        print('Mailer sent {} Mails in {:.3f} seconds'.format(mails_count,mails_duration))
