import imaplib
import logging

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    logger = logging.getLogger('django.server')

    def add_arguments(self, parser):
        parser.add_argument('email', nargs=1)
        parser.add_argument('pst', nargs=1)
        parser.add_argument('pcy', nargs=1)

    # entry point used by manage.py
    def handle(self, *args, **options):
        self.logger.info('Start mailcopy')
        email = options['email'][0]
        pst = options['pst'][0]
        pcy = options['pcy'][0]
        self.logger.info('log on to servertown')
        st_con = imaplib.IMAP4_SSL('www12.servertown.ch', 993)
        st_con.login(email, pst)
        self.logger.info('log on to cyon')
        cy_con = imaplib.IMAP4_SSL('mail.cyon.ch', 993)
        cy_con.login(email, pcy)
        for box in st_con.list()[1]:
            box_str = str(box).split(' "." ')[1].replace('"', '').replace("'", '')
            st_con.select(box_str, readonly=False)  # open box which will have its contents copied
            self.logger.info('Fetching messages from \'%s\'...' % box_str)
            resp, items = st_con.search(None, 'ALL')  # get all messages in the box
            msg_nums = items[0].split()
            self.logger.info('%s messages to cyon' % len(msg_nums))
            if len(msg_nums) > 0:
                cy_con.create(box_str)
            for msg_num in msg_nums:
                resp, data = st_con.fetch(msg_num, "(FLAGS INTERNALDATE BODY.PEEK[])")  # get email
                message = data[0][1]
                flags = imaplib.ParseFlags(data[0][0])  # get flags
                flags_str = [x.decode("utf-8") for x in flags]
                flag_str = " ".join(flags_str)
                self.logger.info(flag_str)
                date = imaplib.Time2Internaldate(imaplib.Internaldate2tuple(data[0][0]))  # get date
                copy_result = cy_con.append(box_str, flag_str, date, message)  # copy to archive
                self.logger.info(copy_result)
        st_con.logout()
        cy_con.logout()
