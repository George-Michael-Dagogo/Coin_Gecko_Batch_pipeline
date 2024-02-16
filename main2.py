import os 
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime


os.system('python main.py > output.txt')


email_sender = 'georgemichaeldagogo@gmail.com'
email_password = os.environ['EMAIL_KEY']
email_receiver = ['georgemichaeldagogomaynard@gmail.com','kedeisha45@gmail.com']


# Set the subject and body of the email
subject = f'Pipeline update at {datetime.now()}'
body = f'{file1.read()}'
print('1')
em = EmailMessage()
em['From'] = email_sender
em['To'] = email_receiver
em['Subject'] = subject
em.set_content(body)

# Add SSL (layer of security)
context = ssl.create_default_context()
print('2')
# Log in and send the email
with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
    smtp.login(email_sender, email_password)
    smtp.sendmail(email_sender, email_receiver, em.as_string())

file1.close()

if os.path.exists("output.txt"):
    os.remove('output.txt')
