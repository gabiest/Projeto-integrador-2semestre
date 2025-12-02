DRIVE_FOLDER_ID = '1IfMK8UGcaT2cUALo5Uas2mB0n9zIp8hs'
import os
import zipfile
import datetime
import json
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import argparse
import sys

# --- CONFIGURAÇÕES ---
# O escopo define o nível de acesso. Drive completo é o mais simples para começar.
SCOPES = ['https://www.googleapis.com/auth/drive']
# O nome do arquivo de credenciais baixado do Google Cloud Console
# Tenta localizar `credentials.json` ao lado deste script; aceita também
# `credentials.json.json` (arquivo presente no workspace atual).
DEFAULT_CRED_BASENAME = 'credentials.json'
ALT_CRED_BASENAME = 'credentials.json.json'
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), DEFAULT_CRED_BASENAME)
if not os.path.exists(CREDENTIALS_FILE):
    alt = os.path.join(os.path.dirname(__file__), ALT_CRED_BASENAME)
    if os.path.exists(alt):
        CREDENTIALS_FILE = alt

# Diretório raiz do seu projeto (assumindo que o script está em PROJETO HOSTS/hosts.py/backup.py)
# Você precisa subir dois níveis para chegar à pasta PROJETO HOSTS
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

# Nome do arquivo ZIP de backup
BACKUP_FILENAME = f"hosts_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
BACKUP_PATH = os.path.join(PROJECT_ROOT, BACKUP_FILENAME)

# ID da pasta de destino no Google Drive.
# *** ID DA SUA PASTA: 1IfMK8UGcaT2cUALo5Uas2mB0n9zIp8hs ***
DRIVE_FOLDER_ID = '1IfMK8UGcaT2cUALo5Uas2mB0n9zIp8hs'

# --- FUNÇÕES ---

def authenticate_google_drive():
    """Realiza a autenticação e retorna o objeto de serviço do Google Drive."""
    creds = None
    # O arquivo token.json armazena os tokens de acesso e de atualização do usuário
    # e é criado automaticamente após a primeira autorização.
    TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')

    # Primeiro, tenta autenticar como Service Account (mais simples para uploads programáticos)
    try:
        service_creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES)
        print("Usando Service Account para autenticação.")
        return build('drive', 'v3', credentials=service_creds)
    except Exception:
        # Não é um service account - tenta fluxo OAuth de usuário
        pass

    if os.path.exists(TOKEN_FILE):
        try:
            creds = UserCredentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None

    # Se não houver credenciais válidas, permite o login.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                print("\n❌ Falha no fluxo OAuth. Mensagem:", e)
                print("Possíveis causas:")
                print(" - O app não passou pela verificação do Google (mostra 'Access blocked')")
                print(" - O e-mail usado não está listado como 'Test user' na OAuth consent screen")
                print("Soluções recomendadas:")
                print(" 1) Adicione seu e-mail em 'APIs & Services -> OAuth consent screen -> Test users' no Cloud Console.")
                print(" 2) Use uma Service Account (recomendado para automação). Coloque o JSON da service account na mesma pasta e execute novamente.")
                print(" 3) Se quiser, informe o caminho do JSON de service account via variável de ambiente SERVICE_ACCOUNT_FILE ou usando --service-account.")
                sys.exit(1)

        # Salva as credenciais para a próxima execução
        with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)


def parse_args():
    parser = argparse.ArgumentParser(description='Backup do projeto e upload para Google Drive')
    parser.add_argument('--service-account', '-s', help='Caminho para JSON de Service Account')
    parser.add_argument('--credentials', '-c', help='Caminho para OAuth client_secret JSON (credentials.json)')
    parser.add_argument('--drive-folder', '-d', help='ID da pasta do Drive de destino')
    parser.add_argument('--no-cleanup', action='store_true', help='Não remover o ZIP local após upload')
    return parser.parse_args()

def create_zip_backup(root_dir, output_path):
    """Compacta todo o conteúdo do diretório raiz do projeto."""
    print(f"Criando arquivo ZIP de backup em: {output_path}...")
    
    # Lista de arquivos/pastas para ignorar no backup
    EXCLUDE_LIST = [
        '__pycache__', 
        '.git', 
        BACKUP_FILENAME, # Evita incluir o próprio backup no backup
        'token.json', # Não precisa de backup da credencial de acesso
        'credentials.json',
        'meu_banco.db' 
    ]

    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(root_dir):
                # Modifica 'dirs' no local para excluir pastas
                dirs[:] = [d for d in dirs if d not in EXCLUDE_LIST]
                
                # Cria o caminho relativo dentro do ZIP
                relative_path_start = len(root_dir) + len(os.sep) 

                for file in files:
                    # Ignora arquivos de credenciais ou o próprio script
                    if file in EXCLUDE_LIST:
                        continue

                    full_path = os.path.join(root, file)
                    arcname = full_path[relative_path_start:]

                    # Ignora se o arquivo for o próprio script backup.py
                    if "backup.py" in arcname:
                        continue

                    zipf.write(full_path, arcname)
        print("✅ Backup ZIP criado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar o arquivo ZIP: {e}")
        return False


def upload_to_drive(service, file_path, folder_id=''):
    """Faz o upload do arquivo para o Google Drive."""
    file_metadata = {
        'name': os.path.basename(file_path),
        'mimeType': 'application/zip'
    }

    if folder_id:
        file_metadata['parents'] = [folder_id]

    media = MediaFileUpload(file_path, mimetype='application/zip')

    print(f"Iniciando upload de '{os.path.basename(file_path)}' para o Google Drive...")
    
    try:
        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id').execute()
        print(f"✅ Upload concluído. ID do Arquivo no Drive: {file.get('id')}")
        return True
    except Exception as e:
        print(f"❌ Erro ao fazer upload para o Google Drive: {e}")
        return False


def cleanup(file_path):
    """Remove o arquivo ZIP local."""
    try:
        os.remove(file_path)
        print(f"🗑️ Arquivo local '{os.path.basename(file_path)}' removido.")
    except Exception as e:
        print(f"❌ Erro ao remover o arquivo local: {e}")


# --- EXECUÇÃO PRINCIPAL ---

def run_backup():
    print("Iniciando rotina de Backup para o Google Drive...")

    args = parse_args()

    # Se o usuário forneceu caminhos customizados, atualiza variáveis
    global CREDENTIALS_FILE, DRIVE_FOLDER_ID
    if args.credentials:
        CREDENTIALS_FILE = args.credentials
    # Ambiente SERVICE_ACCOUNT_FILE sobrepõe
    sa_env = os.environ.get('SERVICE_ACCOUNT_FILE')
    if args.service_account:
        CREDENTIALS_FILE = args.service_account
    elif sa_env:
        CREDENTIALS_FILE = sa_env

    if args.drive_folder:
        DRIVE_FOLDER_ID = args.drive_folder

    # 1. Compactar o Projeto
    if not create_zip_backup(PROJECT_ROOT, BACKUP_PATH):
        print("\nProcesso de backup falhou na criação do ZIP.")
        return

    # 2. Autenticar com o Google Drive
    drive_service = authenticate_google_drive()

    # 3. Fazer o Upload
    try:
        uploaded = upload_to_drive(drive_service, BACKUP_PATH, DRIVE_FOLDER_ID)
    except HttpError as e:
        print(f"\n❌ Erro HTTP durante upload: {e}")
        uploaded = False

    # 4. Limpeza Local
    if uploaded and not args.no_cleanup:
        cleanup(BACKUP_PATH)

    print("\nProcesso de backup finalizado.")


if __name__ == '__main__':
    run_backup()