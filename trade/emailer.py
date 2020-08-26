import smtplib, ssl
import os

def send_message(to_email, message):
    smtp_server = "smtp.gmail.com"
    port = 587  # For starttls
    sender_email = os.environ['SEND_EMAIL']
    password = os.environ['SEND_EMAIL_PASSWORD']



    # Create a secure SSL context
    context = ssl.create_default_context()

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtp_server,port)
        server.ehlo() # Can be omitted
        server.starttls(context=context) # Secure the connection
        server.ehlo() # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, to_email, message)
        print('email sent to ' + to_email)
        # TODO: Send email here
    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        server.quit()


if __name__ == '__main__':
    message = """\
    Subject: Testing Emailer

    We are testing our email functionality.

    Sincerely,
    K.M.T.
    """

    to_email = "jacob@roboflow.ai"
    send_message(to_email, message)
