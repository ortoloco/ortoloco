from django.core.files import File
from mailqueue.models import MailerMessage


class Mailer:
    def send(msg):
        tos = msg.to + msg.bcc
        for to in tos:
            new_message = MailerMessage()
            new_message.subject = msg.subject
            new_message.to_address = to
            new_message.from_address = msg.from_email
            new_message.content = msg.body
            if len(msg.alternatives) > 0:
                new_message.html_content = msg.alternatives[0][0]
            new_message.reply_to =  next(iter(msg.reply_to or []),None)
            for a in msg.attachments:
                with open(a[0], 'wb') as f:
                    f.write(a[1])
                at = File(open(a[0], 'rb'))
                new_message.add_attachment(at)
            new_message.save()