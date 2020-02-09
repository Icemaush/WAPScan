# Config file to store sensitive information and other variables.

senderemail = '<ENTER EMAIL ADDRESS HERE>'  # Email address to send notification emails from.
senderpassword = '<ENTER EMAIL PASSWORD HERE>'
smtpserver = "<ENTER SMTP SERVER HERE>"  # eg. smtp.live.com
smtpport = 587  # Change to correct SMTP port.


def init():
    global exceeded_list
    heading_list = ["IP Address", "MAC Address", "Bandwidth"]
    exceeded_list = [tuple(heading_list)]
