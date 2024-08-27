#!/usr/bin/env python3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail credentials
smtp_server = 'smtp.gmail.com'
smtp_port = 587
smtp_user = 'your_smtp_email@gmail.com'
smtp_password = 'smtp_appPass_her'
RECIPIENTS = [
	'user1@domain.com', 
	'user2@domain.com'
	]
subject = 's3.odysseyanalytics.net - Health Check Alert'

# Function to send email using Gmail SMTP
def send_email(subject, body):
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = ', '.join(RECIPIENTS)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, RECIPIENTS, msg.as_string())
    except Exception as e:
        print(f"Failed to send email: {e}")
