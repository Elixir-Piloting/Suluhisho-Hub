from flask import current_app, render_template, url_for
from flask_mail import Message
from threading import Thread
from app.utils.tokens import generate_verification_token

def send_async_email(app, msg):
    with app.app_context():
        try:
            print(f"\n=== Email Debug ===")
            print(f"SMTP Server: {app.config['MAIL_SERVER']}")
            print(f"SMTP Port: {app.config['MAIL_PORT']}")
            print(f"TLS Enabled: {app.config['MAIL_USE_TLS']}")
            print(f"Username: {app.config['MAIL_USERNAME']}")
            print(f"Sending email to: {msg.recipients}")
            print(f"Subject: {msg.subject}")
            
            current_app.mail.send(msg)
            print("Email sent successfully")
            print("==================\n")
        except Exception as e:
            print(f"\n=== Email Error ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            print("==================\n")
            raise

def send_email(subject, recipients, text_body, html_body=None):
    try:
        msg = Message(
            subject=subject,
            sender=current_app.config['MAIL_USERNAME'],
            recipients=recipients,
            body=text_body,
            html=html_body
        )
        
        # Send email asynchronously
        Thread(
            target=send_async_email,
            args=(current_app._get_current_object(), msg)
        ).start()
        
    except Exception as e:
        print(f"\n=== Email Creation Error ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("=========================\n")
        raise

def send_verification_email(user):
    try:
        print(f"\n=== Verification Email Debug ===")
        print(f"Generating token for: {user.email}")
        
        token = generate_verification_token(user.email)
        verify_url = url_for('auth.verify_email', token=token, _external=True)
        
        print(f"Verification URL: {verify_url}")
        
        subject = 'Verify Your Email - Suluhisho Hub'
        text_body = render_template(
            'email/verify_email.txt',
            user=user,
            verify_url=verify_url
        )
        html_body = render_template(
            'email/verify_email.html',
            user=user,
            verify_url=verify_url
        )
        
        print("Sending verification email...")
        send_email(
            subject=subject,
            recipients=[user.email],
            text_body=text_body,
            html_body=html_body
        )
        print("============================\n")
        
    except Exception as e:
        print(f"\n=== Verification Email Error ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("==============================\n")
        raise 