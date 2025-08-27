import hashlib
import requests
import time
import json
import pandas as pd

def get_access_token(outlet, secret):
    timestamp = int(round(time.time() * 1000))
    post_url = f"https://oauth.performgroup.com/oauth/token/{outlet}?_fmt=json&_rt=b"
    key = str.encode(outlet + str(timestamp) + secret)
    unique_hash = hashlib.sha512(key).hexdigest()
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {unique_hash}',
        'Timestamp': str(timestamp)
    }
    body = {
        'grant_type': 'client_credentials',
        'scope': 'b2b-feeds-auth'
    }
    
    response = requests.post(post_url, data=body, headers=headers)
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception(f"Error obteniendo el token OAuth: {response.status_code}, {response.text}")

def get_error_message(status_code, error_code):
    error_messages = {
        400: {
            10200: "Falta un parámetro obligatorio en la solicitud.",
            10202: "Valor de parámetro de solicitud no válido.",
            10203: "Parámetros de solicitud ambiguos o no válidos.",
            10212: "Modo no compatible: parámetro _rt.",
            10213: "Delta solicitado no válido: parámetro _dlt.",
            10217: "Solicitudes de paginación no válidas.",
            10219: "Solicitud no válida."
        },
        401: {
            10310: "Usuario no autorizado. No se proporcionó token de acceso.",
            10312: "Token OAuth expirado."
        },
        403: {
            10300: "Acceso al feed denegado.",
            10313: "Usuario no autorizado. Token con permisos insuficientes."
        },
        404: {
            10001: "Página no encontrada.",
            10010: "El outlet no existe. Clave de autenticación incorrecta o faltante.",
            10400: "No se encontraron datos. Inténtalo de nuevo. Si el error persiste, es posible que no haya elementos o activos disponibles que coincidan con la combinación de parámetros y valores de la consulta. Intenta realizar una llamada utilizando diferentes criterios de búsqueda (prueba con una llamada simple para fines de prueba)."
        },
        405: {
            10204: "Método de solicitud no válido."
        },
        408: {
            10401: "Tiempo de espera de solicitud de datos agotado. Se agotó el tiempo de espera de la solicitud de datos específicos, por ejemplo, de una consulta de búsqueda de texto. Inténtelo de nuevo. Si el error persiste, intente realizar una solicitud simple al feed (no utilice muchos parámetros ni valores)."
        },
        415: {
            10210: "Formato no compatible: parámetro _fmt o encabezado Accept no válido."
        },
        500: {
            10000: "Ha ocurrido un error inesperado.",
            10100: "Feed no disponible."
        },
        503: {
            10320: "Se ha excedido el límite de uso aceptable."
        },
        562: {
            10201: "Parámetro de solicitud desconocido."
        }
    }

    if status_code in error_messages and error_code in error_messages[status_code]:
        return error_messages[status_code][error_code]
    else:
        return f"Error desconocido. Código de estado: {status_code}, Código de error: {error_code}"

def call_api(endpoint, params=None, output_format='json'):
    # Leer las credenciales del archivo
    with open('token.txt', 'r') as file:
        outlet = file.readline().strip()
        secret = file.readline().strip()
    
    # Obtener el token de acceso
    try:
        access_token = get_access_token(outlet, secret)
    except Exception as e:
        print(f"Error al obtener el token de acceso: {str(e)}")
        return None
    
    # Construir la URL base de la API
    base_url = f"https://api.performfeeds.com/soccerdata/{endpoint}/{outlet}"
    
    # Parámetros por defecto
    default_params = {
        '_rt': 'b',
        '_fmt': 'json'
    }
    
    # Combinar parámetros por defecto con los proporcionados
    if params:
        default_params.update(params)
    
    # Hacer la llamada a la API
    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        response = requests.get(base_url, headers=headers, params=default_params)
    except requests.RequestException as e:
        print(f"Error en la solicitud HTTP: {str(e)}")
        return None
    
    # Manejar la respuesta
    if response.status_code == 200:
        # Procesar la respuesta según el formato de salida deseado
        if output_format == 'json':
            return response.json()
        elif output_format == 'dataframe':
            return pd.json_normalize(response.json())
        else:
            print("Formato de salida no válido. Se devolverá JSON por defecto.")
            return response.json()
    else:
        # Intentar obtener el código de error específico de la API
        try:
            error_data = response.json()
            error_code = int(error_data.get('errorCode', 0))
        except:
            error_code = 0

        error_message = get_error_message(response.status_code, error_code)
        print(f"Error: {error_message}")
        print(f"Detalles adicionales: {response.text}")
        return None