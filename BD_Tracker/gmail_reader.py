import os
import base64
import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

REPRESENTADAS_DOMINIOS = {
    '@seismos.com': 'Seismos',
    '@revsolz.com': 'Revsolz',
    '@qnergy.com': 'Qnergy',
    '@8sigmaes.com': '8Sigma'
}

def authenticate_gmail():
    creds = None
    if os.path.exists('BD_Tracker/token.json'):
        creds = Credentials.from_authorized_user_file('BD_Tracker/token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'BD_Tracker/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('BD_Tracker/token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def get_sent_emails(domains=None, days_back=7):
    creds = authenticate_gmail()
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['SENT'], maxResults=100).execute()
    messages = results.get('messages', [])

    data = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        headers = msg_data['payload']['headers']

        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        to = next((h['value'] for h in headers if h['name'] == 'To'), '')
        cc = next((h['value'] for h in headers if h['name'] == 'Cc'), '')
        date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        date = datetime.strptime(date_str[:-6], '%a, %d %b %Y %H:%M:%S') if date_str else None

        if not date or date < datetime.now() - timedelta(days=days_back):
            continue

        todos_los_destinatarios = f"{to},{cc}".lower()
        if domains and not any(d in todos_los_destinatarios for d in domains):
            continue

        empresas_involucradas = [nombre for dom, nombre in REPRESENTADAS_DOMINIOS.items() if dom in todos_los_destinatarios]
        if not empresas_involucradas:
            empresas_involucradas = ['Desconocida']

        cliente = to
        snippet = msg_data.get('snippet', '')

        for empresa in empresas_involucradas:
            data.append({
                'Fecha': date.date(),
                'Empresa': empresa,
                'Cliente': cliente,
                'Asunto': subject,
                'Resumen': snippet
            })

    return pd.DataFrame(data)