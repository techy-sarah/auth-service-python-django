from django.core.mail import send_mail
from django.conf import settings

def send_verification_email(user):
    token = user.verification_token.token
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    send_mail(
        subject='Verify your email address',
        message=f'Click to verify: {verify_url}\n\nExpires in 24 hours.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

def send_password_reset_email(user, token_obj):
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token_obj.token}"
    send_mail(
        subject='Reset your password',
        message=f'Click to reset: {reset_url}\n\nExpires in 1 hour.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )