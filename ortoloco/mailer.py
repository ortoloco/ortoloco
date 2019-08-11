import copy

from django.core import mail


class Mailer:
    def send(msg):
        tos = msg.to + msg.bcc
        plain_msg = copy.copy(msg)
        plain_msg.bcc = None
        plain_msg.to = None
        msgs = []
        for to in tos:
            new_message = copy.copy(plain_msg)
            new_message.to =[to]
            msgs.append(new_message)
        connection = mail.get_connection()
        connection.send_messages(msgs)
