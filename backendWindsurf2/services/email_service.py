"""
services/email_service.py – Email service for sending password reset codes.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_code: str, user_name: str = "") -> bool:
    """Send password reset code email to user."""
    # Validate SMTP configuration before attempting to send
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.error(
            "SMTP configuration is incomplete. "
            "Please set SMTP_USER and SMTP_PASSWORD in the .env file. "
            "Password reset email cannot be sent."
        )
        return False

    try:
        subject = "ExamAI - Şifre Sıfırlama Kodu"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .header h1 {{ color: #6366f1; margin: 0; }}
                .content {{ line-height: 1.6; color: #333333; }}
                .code-box {{ background-color: #f3f4f6; border-left: 4px solid #6366f1; padding: 20px; margin: 20px 0; text-align: center; }}
                .code {{ font-size: 32px; font-weight: bold; color: #6366f1; letter-spacing: 5px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; text-align: center; }}
                .warning {{ background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ExamAI</h1>
                </div>
                <div class="content">
                    <p>Merhaba {user_name or 'Değerli Kullanıcı'},</p>
                    <p>Şifre sıfırlama talebiniz alındı. Hesabınıza erişimi geri kazanmak için aşağıdaki kodu kullanabilirsiniz:</p>
                    
                    <div class="code-box">
                        <div class="code">{reset_code}</div>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Güvenlik Uyarısı:</strong> Bu kod 10 dakika içinde geçersiz olacaktır. Kimseyle paylaşmayınız.
                    </div>
                    
                    <p>Eğer bu talebi siz yapmadıysanız, lütfen bu e-postayı dikkate almayın ve hesabınızın güvenliği için şifrenizi değiştirin.</p>
                </div>
                <div class="footer">
                    <p>Bu e-posta ExamAI tarafından otomatik olarak gönderilmiştir.<br>
                    © 2024 ExamAI. Tüm hakları saklıdır.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_FROM
        msg['To'] = to_email
        
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Password reset email sent to {to_email}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        logger.error(
            f"SMTP authentication failed for {to_email}. "
            "Check SMTP_USER and SMTP_PASSWORD in .env"
        )
        return False
    except smtplib.SMTPConnectError:
        logger.error(
            f"Could not connect to SMTP server {settings.SMTP_HOST}:{settings.SMTP_PORT}. "
            "Check SMTP_HOST and SMTP_PORT in .env"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
        return False


def send_welcome_email(to_email: str, user_name: str) -> bool:
    """Send welcome email to new users."""
    try:
        subject = "ExamAI'ye Hoş Geldiniz!"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .header h1 {{ color: #6366f1; margin: 0; }}
                .content {{ line-height: 1.6; color: #333333; }}
                .features {{ background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .features ul {{ margin: 0; padding-left: 20px; }}
                .features li {{ margin: 10px 0; }}
                .cta {{ text-align: center; margin: 30px 0; }}
                .cta a {{ display: inline-block; background-color: #6366f1; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>ExamAI</h1>
                </div>
                <div class="content">
                    <p>Merhaba {user_name},</p>
                    <p>ExamAI'ye kaydolduğunuz için teşekkür ederiz! Yapay zeka destekli sınav hazırlama platformuna hoş geldiniz.</p>
                    
                    <div class="features">
                        <h3>🚀 Neler yapabilirsiniz?</h3>
                        <ul>
                            <li>Ders notlarınızı yükleyin (PDF, resim, metin)</li>
                            <li>Yapay zeka ile kişiselleştirilmiş sınavlar oluşturun</li>
                            <li>Geçmiş performansınıza göre zorluk ayarı yapın</li>
                            <li>Sınav sonuçlarınızı analiz edin ve gelişiminizi takip edin</li>
                        </ul>
                    </div>
                    
                    <div class="cta">
                        <a href="{settings.FRONTEND_URL}">Hemen Başlayın</a>
                    </div>
                </div>
                <div class="footer">
                    <p>Bu e-posta ExamAI tarafından otomatik olarak gönderilmiştir.<br>
                    © 2024 ExamAI. Tüm hakları saklıdır.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_FROM
        msg['To'] = to_email
        
        html_part = MIMEText(html_body, 'html', 'utf-8')
        msg.attach(html_part)
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Welcome email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {to_email}: {str(e)}")
        return False
