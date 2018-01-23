#/usr/bin/python3
# -*- coding:Utf-8 -*-

import smtplib, MimeWriter, mimetools, StringIO

def sendHtmlMail(email_from, email_to, subject, text):
    encoding = "base64"
    charset = "utf8"

    # déclaration des buffers
    out = StringIO.StringIO() 
    txtin = StringIO.StringIO(text)

    # déclaration et initialisation du writer
    writer = MimeWriter.MimeWriter(out)
    writer.addheader("Subject", subject)
    writer.addheader("MIME-Version", "1.0")
    writer.startmultipartbody("alternative")
    writer.flushheaders()

    # ajout de la partie text
    textPart = writer.nextpart()
    textPart.addheader("Content-Transfer-Encoding", encoding)
    pout = textPart.startbody("text/plain", [("charset", charset)])
    mimetools.encode(txtin, pout, encoding)
    txtin.close()

    # on clot le mail
    writer.lastpart()
    mail = out.getvalue()
    out.close()
    smtp = smtplib.SMTP()
    smtp.connect("xx")
    smtp.sendmail(email_from, [email_to], mail)
    smtp.close()

sendHtmlMail("xx", "xx", "sujet email", """%s""" % ("&é'(§è!çà)'"))