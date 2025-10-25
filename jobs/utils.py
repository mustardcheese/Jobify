# jobs/utils.py
import smtplib
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone

def send_candidate_email(message_instance):
    """
    Send email to candidate using recruiter's email settings
    Returns: (success: bool, error_message: str)
    """
    try:
        # FIX: Use the recipient's CURRENT email from their profile
        if not message_instance.recipient_has_email:
            return False, "No email address available. This candidate doesn't have an email address associated with their account. Message will only be sent to their Jobify inbox."
        
        # Check if sender is a recruiter with email setup
        sender_profile = getattr(message_instance.sender, 'profile', None)
        if not sender_profile:
            return False, "Recruiter profile not found"
        
        # Check if sender is actually a recruiter with email configured
        if not getattr(sender_profile, 'has_email_setup', False):
            return False, "Recruiter has not configured email settings"
        
        # Get job info if applicable
        job_title = None
        company = None
        if message_instance.application:
            job_title = message_instance.application.job.title
            company = message_instance.application.job.company
        
        # Render HTML email template
        html_content = render_to_string('jobs/email_candidate.html', {
            'subject': message_instance.subject,
            'content': message_instance.content,
            'sender_name': message_instance.sender.get_full_name() or message_instance.sender.username,
            'job_title': job_title,
            'company': company,
            'sent_at': message_instance.sent_at,
        })
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Get the decrypted password using the model's method
        email_password = sender_profile.get_email_password()
        
        # Create email connection with recruiter's settings
        connection = get_connection(
            backend='django.core.mail.backends.smtp.EmailBackend',
            host=getattr(sender_profile, 'email_host', 'smtp.gmail.com'),
            port=getattr(sender_profile, 'email_port', 587),
            username=sender_profile.email_host_user,
            password=email_password,
            use_tls=getattr(sender_profile, 'email_use_tls', True),
        )
        
        # FIX: Use the recipient's CURRENT email from the Message model property
        recipient_email = message_instance.recipient_email
        
        # Create email
        email = EmailMultiAlternatives(
            subject=message_instance.subject,
            body=text_content,
            from_email=f"{message_instance.sender.get_full_name() or message_instance.sender.username} <{sender_profile.email_host_user}>",
            to=[recipient_email],  # Use current profile email
            reply_to=[sender_profile.email_host_user],
            connection=connection,
        )
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        # Update message instance
        message_instance.email_sent = True
        message_instance.email_sent_at = timezone.now()
        message_instance.email_failed = False
        message_instance.email_failure_reason = ""
        message_instance.save()
        
        return True, "Email sent successfully"
        
    except Exception as e:
        # Update message instance with failure
        message_instance.email_sent = False
        message_instance.email_failed = True
        message_instance.email_failure_reason = str(e)
        message_instance.save()
        
        return False, str(e)
    
def test_email_connection(email_host, email_port, email_host_user, email_host_password, use_tls=True):
    """
    Test the email connection settings
    Returns: (success: bool, message: str)
    """
    try:
        # Test SMTP connection
        if use_tls and email_port == 587:
            server = smtplib.SMTP(email_host, email_port, timeout=10)
            server.starttls()  # Enable TLS encryption
        elif email_port == 465:
            server = smtplib.SMTP_SSL(email_host, email_port, timeout=10)  # For SSL ports
        else:
            server = smtplib.SMTP(email_host, email_port, timeout=10)
        
        server.login(email_host_user, email_host_password)
        
        # Test sending a simple email to ourselves
        test_subject = "Jobify - Email Configuration Test"
        test_body = "This is a test email to verify your email settings are working correctly."
        
        server.sendmail(
            email_host_user,
            email_host_user,  # Send to ourselves
            f"Subject: {test_subject}\n\n{test_body}"
        )
        
        server.quit()
        return True, "Email connection tested successfully! Settings are correct."
    
    except smtplib.SMTPAuthenticationError:
        return False, "Authentication failed. Please check your email address and app password. Make sure you're using an App Password, not your regular Gmail password."
    
    except smtplib.SMTPConnectError:
        return False, "Could not connect to the email server. Please check your SMTP settings and internet connection."
    
    except smtplib.SMTPServerDisconnected:
        return False, "Connection to the email server was lost. Please try again."
    
    except Exception as e:
        return False, f"Email connection failed: {str(e)}"