from vellox import Vellox
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

# Defina o escopo e o arquivo de credenciais
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Certifique-se de que este arquivo está no diretório do projeto

# Função para autenticação
def test_credentials():
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        drive_service = build('drive', 'v3', credentials=credentials)
        print("Autenticação bem-sucedida.")
        return drive_service
    except Exception as e:
        print("Erro ao autenticar com o Google Drive:", e)
        return None

# Conecte-se ao Google Drive
drive_service = test_credentials()
if not drive_service:
    raise Exception("Falha na autenticação. Verifique o arquivo de credenciais e o escopo.")

# Função para listar todos os arquivos no Google Drive
def list_files_in_drive(folder_id=None):
    try:
        # Lista todos os arquivos (não apenas pastas)
        query = "trashed = false"
        if folder_id:
            query = f"'{folder_id}' in parents and " + query
        
        files = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name, mimeType)',
        ).execute().get('files', [])
        
        # Organize os dados dos arquivos
        file_details = [{
            'id': file['id'],
            'name': file['name'],
            'mimeType': file['mimeType']
        } for file in files]
        
        return file_details
    except Exception as e:
        print("Erro ao listar arquivos:", e)
        return []

# Função de aplicação para responder com arquivos do Drive
async def app(scope, receive, send):
    # Certifique-se de que o 'scope' tenha a estrutura correta para Vellox
    if 'method' not in scope:
        scope['method'] = 'GET'  # Definir um método padrão para a requisição

    folder_id = None  # Para listar todos os arquivos, mantenha o ID como None
    file_details = list_files_in_drive(folder_id)
    
    # Converte os detalhes dos arquivos para JSON
    response_json = json.dumps(file_details, indent=4)
    
    # Envia a resposta para o cliente
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [[b"content-type", b"application/json; charset=utf-8"]]
    })
    await send({
        "type": "http.response.body",
        "body": response_json.encode('utf-8')
    })

# Inicia o servidor Vellox com a aplicação assíncrona
vellox = Vellox(app=app, lifespan="off")

# Função de handler que recebe requisições HTTP
def handler(request):
    return vellox(request)

# Se você estiver rodando isso diretamente, execute o servidor.
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(handler, host="0.0.0.0", port=8000)
