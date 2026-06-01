import random
import smtplib
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from os import getenv

from django.db.models import Sum, Case, When, Value, DecimalField, F

from apps.models import Operation


def otp_generator():
    return random.randint(100000, 999999)


def send_email(email: str, code):
    sender_email = getenv('SENDER_EMAIL')
    sender_name = "Expense Manager"
    receiver_email = email
    password = getenv('EMAIL_PASSWORD')

    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Verification Code"
    message["From"] = formataddr((sender_name, sender_email))
    message["To"] = receiver_email

    html = f"""
            <div style="font-family: Arial, sans-serif; background:#f4f6f8; padding:20px">
                <div style="max-width:400px; margin:auto; background:#ffffff; padding:20px; border-radius:8px;">
                    <h2 style="color:#333; text-align:center;">🔐 Verification code</h2>
                    <p style="font-size:16px; color:#555; text-align:center;">
                        Your OTP code:
                    </p>
                    <div style="font-size:28px; font-weight:bold; letter-spacing:4px;
                                text-align:center; margin:20px 0; color:#000;">
                        {code}
                    </div>
                    <hr>
                    <p style="font-size:12px; color:#aaa; text-align:center;">
                        Multipart Test
                    </p>
                </div>
            </div>
            """

    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message.as_string())


def users_balance(user):
    balance = Operation.objects.filter(user=user).aggregate(
        balance=Sum(Case(When(type='income', then='amount'),
                         When(type='expense', then=Value(-1) * F('amount')),
                         default=Value(0),
                         output_field=DecimalField()
                         )
                    )
    )
    balance = balance['balance'] or Decimal('0.00')
    return balance