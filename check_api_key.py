import os

# Sprawdzenie wartości zmiennej SENDGRID_API_KEY
sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
print("SendGrid API Key:", sendgrid_api_key)