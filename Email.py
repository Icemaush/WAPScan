# Import modules.
import smtplib
import config


# ----- SEND EMAIL FUNCTION ----- #
# Function to create and send an email notification when called by WAPScan code.
class Email(object):
    def send_email(self):
        # Email components.
        message = """Subject: WAP Bandwidth Limit Exceeded\n
    
        WAP AT1 bandwidth limit has been exceeded by the following device/s:\n\n"""

        message2 = ""
        for i in config.exceeded_list:
            message2 += "\t" + i[0] + "\t\t\t" + i[1] + "\t\t\t" + i[2] + "\n"
        footer = """\n
        Thank you,
    
    
        Network Administrator"""
        # Attempt to connect and send email.
        try:
            server = smtplib.SMTP(config.smtpserver, int(config.smtpport))
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(config.senderemail, config.senderpassword)
            server.sendmail(config.senderemail, config.senderemail, message + message2 + footer)
            server.quit()
            print('Email sent.')
            heading_list = ["IP Address", "MAC Address", "Bandwidth Rate"]
            config.exceeded_list = [tuple(heading_list)]

        # Print text to console if unable to send email.
        except:
            print('Error sending email.')
