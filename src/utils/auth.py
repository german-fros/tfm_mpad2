import streamlit as st
from streamlit_cookies_controller import CookieController
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta

from config.logger_config import LoggerSetup, log_function, find_project_root

logger_setup = LoggerSetup()
logger = logger_setup.setup_logger(__name__)

PROJECT_ROOT = find_project_root()
USERS_FILE = PROJECT_ROOT / "data" / "users.json"

# Development mode flag - set to True to skip authentication during development
DEVELOPMENT_MODE = False

# Configuración de cookies
COOKIE_EXPIRY_DAYS = 30
AUTH_COOKIE_NAME = "auth_token"

# Inicializar controlador de cookies
def _get_cookie_controller():
    """
    Obtener controlador de cookies usando session state para persistencia.
    Almacena la instancia en session state para evitar recreación múltiple.
    
    Returns:
        CookieController instance si está disponible, None de lo contrario.
    """
    # Clave para almacenar el controlador en session state
    controller_key = 'inter_miami_cookie_controller'
    
    # Verificar si ya tenemos un controlador en session state
    if controller_key in st.session_state:
        controller = st.session_state[controller_key]
        if controller:
            logger.debug("Usando CookieController existente desde session state")
            return controller
        else:
            return None
    
    # Crear nuevo controlador y almacenarlo en session state
    try:
        controller = CookieController()
        st.session_state[controller_key] = controller
        logger.debug("CookieController creado y almacenado en session state")
        return controller
    except ImportError as e:
        logger.error(f"Error de importación en controlador de cookies: {str(e)}")
        st.session_state[controller_key] = None
        return None
    except Exception as e:
        logger.error(f"Error inicializando controlador de cookies: {str(e)}")
        st.session_state[controller_key] = None
        return None


@log_function("hash_password")
def _hash_password(password: str) -> str:
    """
    Hace hash de la contraseña usando SHA-256 para seguridad básica.

    Args:
        password: Contraseña en texto plano para hacer hash.

    Returns:
        Contraseña hasheada como cadena hexadecimal.
    """
    return hashlib.sha256(password.encode()).hexdigest()


@log_function("create_auth_token")
def _create_auth_token(username: str, login_time: datetime) -> str:
    """
    Crear token de autenticación seguro para cookies.

    Args:
        username: Nombre del usuario.
        login_time: Tiempo de login.

    Returns:
        Token de autenticación hasheado.
    """
    token_data = f"{username}_{login_time.isoformat()}_{AUTH_COOKIE_NAME}"
    return _hash_password(token_data)


@log_function("save_auth_cookie")
def _save_auth_cookie(username: str, login_time: datetime) -> Tuple[bool, str]:
    """
    Guardar token de autenticación en cookie del navegador.

    Args:
        username: Nombre del usuario.
        login_time: Tiempo de login.

    Returns:
        Tupla de (éxito: bool, mensaje: str).
    """
    try:
        controller = _get_cookie_controller()
        if controller is None:
            return False, "Error inicializando controlador de cookies"
        
        # Crear token seguro
        auth_token = _create_auth_token(username, login_time)
        
        # Crear datos de cookie con información necesaria
        cookie_data = {
            'username': username,
            'login_time': login_time.isoformat(),
            'token': auth_token
        }
        
        # Convertir a JSON para almacenar
        cookie_value = json.dumps(cookie_data)
        
        # Calcular fecha de expiración
        expiry_date = login_time + timedelta(days=COOKIE_EXPIRY_DAYS)
        
        # Guardar cookie
        controller.set(AUTH_COOKIE_NAME, cookie_value, expires=expiry_date)
        logger.info(f"Cookie de autenticación guardada para usuario {username}")
        return True, f"Sesión persistente creada exitosamente (válida por {COOKIE_EXPIRY_DAYS} días)"
        
    except Exception as e:
        error_message = f"Error guardando cookie de autenticación: {str(e)}"
        logger.error(error_message)
        return False, "No se pudo crear sesión persistente debido a un error técnico."


@log_function("load_auth_cookie")
def _load_auth_cookie() -> Optional[Dict[str, Any]]:
    """
    Cargar y validar token de autenticación desde cookie del navegador.

    Returns:
        Diccionario con datos de autenticación si es válido, None si no es válido.
    """
    try:
        controller = _get_cookie_controller()
        if controller is None:
            logger.debug("No se puede cargar cookie - controlador no disponible")
            return None
        
        # Obtener cookie
        cookie_value = controller.get(AUTH_COOKIE_NAME)
        if not cookie_value:
            logger.debug("No se encontró cookie de autenticación")
            return None
        
        logger.debug(f"Cookie encontrada (primeros 50 chars): {cookie_value[:50]}...")
        
        # Parsear datos de cookie
        try:
            cookie_data = json.loads(cookie_value)
        except json.JSONDecodeError as e:
            logger.warning(f"Cookie corrupta - JSON inválido: {str(e)}")
            _clear_auth_cookie()
            return None
            
        username = cookie_data.get('username')
        login_time_str = cookie_data.get('login_time')
        stored_token = cookie_data.get('token')
        
        if not all([username, login_time_str, stored_token]):
            logger.warning("Datos de cookie incompletos - faltan campos requeridos")
            _clear_auth_cookie()
            return None
        
        # Validar tiempo de login
        try:
            login_time = datetime.fromisoformat(login_time_str)
        except ValueError as e:
            logger.warning(f"Formato de fecha inválido en cookie: {str(e)}")
            _clear_auth_cookie()
            return None
        
        # Recrear token para verificar integridad
        expected_token = _create_auth_token(username, login_time)
        
        if stored_token != expected_token:
            logger.warning(f"Token de cookie inválido para usuario {username}")
            return None
        
        # Verificar expiración
        if datetime.now() > login_time + timedelta(days=COOKIE_EXPIRY_DAYS):
            logger.info(f"Cookie expirada para usuario {username}")
            _clear_auth_cookie()
            return None
        
        # Verificar que el usuario aún existe
        users = _load_users()
        if username not in users:
            logger.warning(f"Usuario {username} no existe, limpiando cookie")
            _clear_auth_cookie()
            return None
        
        logger.info(f"Cookie de autenticación válida para usuario {username}")
        return {
            'username': username,
            'login_time': login_time,
            'token': stored_token
        }
        
    except Exception as e:
        logger.error(f"Error cargando cookie de autenticación: {str(e)}")
        _clear_auth_cookie()  # Limpiar cookie corrupta
        return None


@log_function("clear_auth_cookie")
def _clear_auth_cookie() -> None:
    """
    Limpiar cookie de autenticación del navegador.
    """
    try:
        controller = _get_cookie_controller()
        if controller is not None:
            controller.remove(AUTH_COOKIE_NAME)
            logger.info("Cookie de autenticación limpiada")
    except Exception as e:
        logger.error(f"Error limpiando cookie de autenticación: {str(e)}")


@log_function("load_users")
def _load_users() -> Dict[str, Any]:
    """
    Cargar usuarios desde archivo JSON.

    Returns:
        Diccionario que contiene datos de usuarios.
    """
    if not USERS_FILE.exists():
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {}
    
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logger.warning("No se pudo cargar archivo de usuarios, comenzando con base de datos vacía")
        return {}


@log_function("save_users")
def _save_users(users: Dict[str, Any]) -> None:
    """
    Guardar usuarios en archivo JSON.

    Args:
        users: Diccionario que contiene datos de usuarios a guardar.
    """
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


@log_function("initialize_session_state")
def initialize_session_state() -> None:
    """
    Inicializar variables de estado de sesión relacionadas con autenticación.
    Solo inicializa variables que no existen, preservando el estado existente.
    """
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    if 'auth_token' not in st.session_state:
        st.session_state.auth_token = None
    if 'auth_tab' not in st.session_state:
        st.session_state.auth_tab = "Iniciar Sesión"
    if 'registration_success' not in st.session_state:
        st.session_state.registration_success = False


@log_function("register_user")
def register_user(username: str, password: str, full_name: str = "") -> Tuple[bool, str]:
    """
    Registrar un nuevo usuario con nombre de usuario y contraseña.

    Args:
        username: Nombre de usuario único para el usuario.
        password: Contraseña en texto plano.
        full_name: Nombre completo opcional del usuario.

    Returns:
        Tupla de (éxito: bool, mensaje: str).
    """
    if not username or not password:
        return False, "Nombre de usuario y contraseña son requeridos"
    
    if len(username) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres"
    
    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres"
    
    users = _load_users()
    
    if username in users:
        return False, "El nombre de usuario ya existe"
    
    users[username] = {
        'password_hash': _hash_password(password),
        'full_name': full_name,
        'created_at': datetime.now().isoformat(),
        'last_login': None
    }
    
    try:
        _save_users(users)
        return True, "Usuario registrado exitosamente"
    except Exception as e:
        logger.error(f"Error guardando datos de usuario: {str(e)}")
        return False, "Error registrando usuario"
    

@log_function("authenticate_user")
def authenticate_user(username: str, password: str) -> Tuple[bool, str]:
    """
    Autenticar usuario con nombre de usuario y contraseña.

    Args:
        username: Nombre de usuario a autenticar.
        password: Contraseña en texto plano.

    Returns:
        Tupla de (éxito: bool, mensaje: str).
    """
    if not username or not password:
        return False, "Nombre de usuario y contraseña son requeridos"
    
    users = _load_users()
    
    if username not in users:
        return False, "Nombre de usuario o contraseña inválidos"
    
    user_data = users[username]
    password_hash = _hash_password(password)
    
    if password_hash != user_data['password_hash']:
        return False, "Nombre de usuario o contraseña inválidos"
    
    # Actualizar último login
    login_time = datetime.now()
    user_data['last_login'] = login_time.isoformat()
    _save_users(users)
    
    # Establecer estado de sesión con persistencia mejorada
    st.session_state.authenticated = True
    st.session_state.username = username
    st.session_state.login_time = login_time
    st.session_state.auth_token = _hash_password(f"{username}_{login_time.isoformat()}")
    
    # Guardar cookie de autenticación persistente
    cookie_saved, cookie_message = _save_auth_cookie(username, login_time)
    if cookie_saved:
        logger.info(f"Sesión persistente creada para usuario {username}")
    else:
        logger.warning(f"No se pudo crear sesión persistente para usuario {username}: {cookie_message}")
    
    return True, f"Bienvenido de nuevo, {user_data.get('full_name', username)}!"


@log_function("logout_user")
def logout_user() -> None:
    """
    Cerrar sesión del usuario actual y limpiar estado de sesión y cookies.
    """
    current_user = st.session_state.get('username', 'usuario desconocido')
    
    # Limpiar estado de sesión
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.login_time = None
    st.session_state.auth_token = None
    st.session_state.auth_tab = "Iniciar Sesión"
    st.session_state.registration_success = False
    
    # Limpiar cookie de autenticación
    _clear_auth_cookie()
    
    logger.info(f"Usuario {current_user} cerró sesión exitosamente y cookie limpiada")


@log_function("get_current_user")
def get_current_user() -> Optional[str]:
    """
    Obtener nombre de usuario autenticado actual.

    Returns:
        Nombre de usuario actual si está autenticado, None de lo contrario.
    """
    if validate_session():
        return st.session_state.get('username')
    return None


@log_function("get_user_info")
def get_user_info(username: str = None) -> Optional[Dict[str, Any]]:
    """
    Obtener información de usuario por nombre de usuario.

    Args:
        username: Nombre de usuario para obtener info. Si es None, usa el usuario actual.

    Returns:
        Diccionario de información de usuario o None si no se encuentra.
    """
    if username is None:
        username = get_current_user()
    
    if not username:
        return None
    
    users = _load_users()
    user_data = users.get(username)
    
    if user_data:
        # Remover hash de contraseña de los datos devueltos
        safe_data = user_data.copy()
        safe_data.pop('password_hash', None)
        return safe_data
    
    return None


@log_function("validate_session")
def validate_session() -> bool:
    """
    Validar si la sesión actual es válida y activa.
    
    Returns:
        True si la sesión es válida, False de lo contrario.
    """
    try:
        # Verificar si hay variables de sesión básicas
        authenticated = st.session_state.get('authenticated', False)
        username = st.session_state.get('username')
        auth_token = st.session_state.get('auth_token')
        
        logger.debug(f"Validando sesión - authenticated: {authenticated}, username: {username}, has_token: {bool(auth_token)}")
        
        if not authenticated:
            logger.debug("Sesión no autenticada")
            return False
        
        if not username:
            logger.debug("Falta nombre de usuario en sesión")
            return False
        
        if not auth_token:
            logger.debug("Falta token de autenticación en sesión")
            return False
        
        # Verificar si el usuario aún existe en la base de datos
        try:
            users = _load_users()
            if username not in users:
                logger.warning(f"Usuario {username} no existe en la base de datos, invalidando sesión")
                return False
        except Exception as e:
            logger.warning(f"Error cargando usuarios para validación: {str(e)}")
            # En caso de error de DB, mantener sesión válida por ahora
            pass
        
        # Validar tiempo de sesión (extendido a 30 días para coincidir con cookies)
        login_time = st.session_state.get('login_time')
        if login_time and isinstance(login_time, datetime):
            session_age = datetime.now() - login_time
            if session_age.total_seconds() > (COOKIE_EXPIRY_DAYS * 24 * 3600):  # Usar mismo tiempo que cookies
                logger.info("Sesión expirada por tiempo")
                return False
        
        logger.debug(f"Sesión válida para usuario: {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error validando sesión: {str(e)}")
        return False


@log_function("recover_session_from_cookie")
def _recover_session_from_cookie() -> bool:
    """
    Intentar recuperar sesión desde cookie de autenticación.

    Returns:
        True si se recuperó la sesión exitosamente, False de lo contrario.
    """
    try:
        logger.info("Intentando recuperar sesión desde cookie")
        cookie_data = _load_auth_cookie()
        if not cookie_data:
            logger.info("No se encontraron datos de cookie válidos")
            return False
        
        username = cookie_data.get('username')
        login_time_str = cookie_data.get('login_time') 
        token = cookie_data.get('token')
        
        if not all([username, login_time_str, token]):
            logger.warning("Datos de cookie incompletos")
            return False
        
        # Convertir login_time de string a datetime si es necesario
        if isinstance(login_time_str, str):
            try:
                login_time = datetime.fromisoformat(login_time_str)
            except ValueError as e:
                logger.error(f"Error parseando fecha de login: {str(e)}")
                _clear_auth_cookie()
                return False
        else:
            login_time = login_time_str
        
        # Restaurar estado de sesión desde cookie
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.login_time = login_time
        st.session_state.auth_token = token
        
        logger.info(f"Sesión recuperada exitosamente desde cookie para usuario {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error recuperando sesión desde cookie: {str(e)}")
        _clear_auth_cookie()  # Limpiar cookie corrupta
        return False


@log_function("attempt_session_state_recovery")
def _attempt_session_state_recovery() -> bool:
    """
    Método de fallback para recuperar sesión usando técnicas alternativas.
    Experimental - intenta usar información persistente en el entorno.
    
    Returns:
        True si se logró recuperar algo de información de sesión.
    """
    try:
        logger.info("Intentando recuperación fallback de sesión")
        
        # Por ahora, este método es principalmente para debugging
        # En el futuro podría implementar:
        # - LocalStorage via JavaScript
        # - URL parameters
        # - Archivos temporales
        
        # Para debugging: mostrar estado completo de session_state
        logger.debug("Estado completo de session_state:")
        for key, value in st.session_state.items():
            if 'auth' in key.lower() or key in ['authenticated', 'username', 'login_time']:
                logger.debug(f"  {key}: {value}")
        
        return False  # Por ahora no implementamos recuperación alternativa
        
    except Exception as e:
        logger.error(f"Error en recuperación fallback: {str(e)}")
        return False

    

@log_function("create_login_form")
def create_login_form() -> None:
    """
    Crear componente UI del formulario de login.
    """
    st.subheader("Iniciar Sesión")
    
    with st.form("login_form"):
        username = st.text_input("Nombre de Usuario")
        password = st.text_input("Contraseña", type="password")
        submit_button = st.form_submit_button("Iniciar Sesión")
        
        if submit_button:
            success, message = authenticate_user(username, password)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)


@log_function("create_registration_form")
def create_registration_form() -> None:
    """
    Crear componente UI del formulario de registro de usuario.
    """
    st.subheader("Registrar Nuevo Usuario")
    
    with st.form("registration_form"):
        username = st.text_input("Nombre de Usuario")
        full_name = st.text_input("Nombre Completo (opcional)")
        password = st.text_input("Contraseña", type="password")
        confirm_password = st.text_input("Confirmar Contraseña", type="password")
        submit_button = st.form_submit_button("Registrar")
        
        if submit_button:
            if password != confirm_password:
                st.error("Las contraseñas no coinciden")
            else:
                success, message = register_user(username, password, full_name)
                if success:
                    st.success(message)
                    st.success("¡Registro exitoso! Redirigiendo al login...")
                    # Cambiar a la pestaña de login después del registro exitoso
                    st.session_state.auth_tab = "Iniciar Sesión"
                    st.session_state.registration_success = True
                    # Esperar un momento y recargar
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)


@log_function("create_user_menu")
def create_user_menu() -> None:
    """
    Crear menú de usuario para usuarios autenticados.
    """
    if validate_session():
        username = get_current_user()
        user_info = get_user_info(username)
        
        with st.sidebar:
            st.write("---")
            st.subheader("Menú de Usuario")
            
            # Si full_name está vacío o es None, usar username como fallback
            display_name = username
            if user_info:
                full_name = user_info.get('full_name', '').strip()
                display_name = full_name if full_name else username
            st.write(f"Conectado como: **{display_name}**")
            
            if user_info and user_info.get('last_login'):
                last_login = datetime.fromisoformat(user_info['last_login'])
                st.caption(f"Último acceso: {last_login.strftime('%Y-%m-%d %H:%M')}")
            
            if st.button("Cerrar Sesión"):
                logout_user()
                st.rerun()


@log_function("require_authentication")
def require_authentication() -> bool:
    """
    Función tipo decorador para requerir autenticación para acceso a páginas.
    Incluye validación de sesión existente, recuperación desde cookies y autenticación automática.

    Returns:
        True si el usuario está autenticado, False de lo contrario.
    """
    try:
        # Skip authentication in development mode
        if DEVELOPMENT_MODE:
            logger.info("Development mode: skipping authentication")
            return True
        
        # Siempre inicializar el estado de sesión primero
        initialize_session_state()
        
        # Debug: mostrar estado actual de sesión
        logger.debug(f"Estado inicial - authenticated: {st.session_state.get('authenticated', False)}, "
                    f"username: {st.session_state.get('username', 'None')}")
        
        # 1. Primero verificar si hay una sesión válida existente
        if validate_session():
            logger.info(f"Sesión válida encontrada para usuario: {st.session_state.username}")
            create_user_menu()
            return True
        
        # 2. Si no hay sesión válida, intentar recuperar desde cookie
        logger.info("No hay sesión válida, intentando recuperar desde cookie")
        
        # Primero intentar recuperación por cookies
        cookie_recovery_success = False
        if _recover_session_from_cookie():
            # Verificar que la sesión recuperada sea válida
            if validate_session():
                logger.info(f"Sesión recuperada exitosamente desde cookie para usuario: {st.session_state.username}")
                create_user_menu()
                cookie_recovery_success = True
                return True
            else:
                logger.warning("Sesión recuperada desde cookie no pasó validación")
        
        # Fallback: intentar recuperación usando session state persistente (experimental)
        if not cookie_recovery_success:
            logger.info("Cookie recovery falló, intentando fallback de session state")
            if _attempt_session_state_recovery():
                if validate_session():
                    logger.info(f"Sesión recuperada con fallback para usuario: {st.session_state.username}")
                    create_user_menu()
                    return True
        
        # 3. Si había una sesión autenticada pero ya no es válida, limpiar estado
        if st.session_state.get('authenticated', False):
            logger.info("Limpiando sesión inválida")
            logout_user()
        
        # 4. No hay sesión válida ni cookie válida, mostrar formulario de login
        st.warning("Por favor, inicia sesión para acceder a esta aplicación.")
        
        # Mostrar mensaje de registro exitoso si corresponde
        if st.session_state.get('registration_success', False):
            st.success("¡Usuario registrado exitosamente! Ahora puedes iniciar sesión.")
            st.session_state.registration_success = False  # Limpiar el flag
        
        # Crear tabs de login/registro
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab1:
            create_login_form()
        
        with tab2:
            create_registration_form()
        
        return False
        
    except Exception as e:
        logger.error(f"Error en require_authentication: {str(e)}")
        st.error("Error de autenticación. Por favor, recarga la página.")
        return False


@log_function("test_authentication_system")
def test_authentication_system() -> Dict[str, Any]:
    """
    Función de debugging para probar el sistema de autenticación.
    
    Returns:
        Diccionario con información del estado del sistema.
    """
    try:
        test_results = {
            'cookie_controller_available': False,
            'session_state_initialized': False,
            'users_file_exists': USERS_FILE.exists(),
            'current_session_state': {},
            'cookie_data': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Test cookie controller
        controller = _get_cookie_controller()
        test_results['cookie_controller_available'] = controller is not None
        
        # Test session state
        initialize_session_state()
        test_results['session_state_initialized'] = True
        test_results['current_session_state'] = {
            'authenticated': st.session_state.get('authenticated', False),
            'username': st.session_state.get('username', 'None'),
            'has_auth_token': bool(st.session_state.get('auth_token')),
            'login_time': str(st.session_state.get('login_time', 'None'))
        }
        
        # Test cookie loading
        cookie_data = _load_auth_cookie()
        test_results['cookie_data'] = 'Available' if cookie_data else 'None'
        
        logger.info(f"Test de autenticación completado: {test_results}")
        return test_results
        
    except Exception as e:
        logger.error(f"Error en test de autenticación: {str(e)}")
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}


@log_function("test_cookie_functionality")
def test_cookie_functionality() -> Dict[str, Any]:
    """
    Función específica para testear la funcionalidad de cookies.
    
    Returns:
        Resultado de las pruebas de cookies.
    """
    try:
        logger.info("=== INICIANDO TEST DE COOKIES ===")
        test_results = {
            'controller_available': False,
            'test_save_success': False,
            'test_load_success': False,
            'all_cookies': {},
            'test_cookie_name': 'test_auth_cookie',
            'timestamp': datetime.now().isoformat()
        }
        
        # 1. Obtener controlador
        controller = _get_cookie_controller()
        test_results['controller_available'] = controller is not None
        
        if not controller:
            logger.error("Controller no disponible, no se puede probar cookies")
            return test_results
        
        # 2. Test de guardado
        test_data = {
            'test_user': 'test_usuario',
            'test_time': datetime.now().isoformat(),
            'test_token': 'test_token_123'
        }
        test_value = json.dumps(test_data)
        test_expiry = datetime.now() + timedelta(minutes=5)
        
        try:
            logger.info(f"Guardando cookie de test: {test_results['test_cookie_name']}")
            controller.set(test_results['test_cookie_name'], test_value, expires=test_expiry)
            test_results['test_save_success'] = True
            logger.info("✓ Cookie de test guardada exitosamente")
        except Exception as e:
            logger.error(f"✗ Error guardando cookie de test: {str(e)}")
            test_results['save_error'] = str(e)
        
        # 3. Test de carga inmediata
        try:
            retrieved_value = controller.get(test_results['test_cookie_name'])
            if retrieved_value:
                test_results['test_load_success'] = True
                test_results['retrieved_data'] = json.loads(retrieved_value)
                logger.info("✓ Cookie de test recuperada exitosamente")
            else:
                logger.error("✗ Cookie de test no se pudo recuperar")
        except Exception as e:
            logger.error(f"✗ Error cargando cookie de test: {str(e)}")
            test_results['load_error'] = str(e)
        
        # 4. Listar todas las cookies
        try:
            all_cookies = controller.getAll()
            test_results['all_cookies'] = {k: str(v)[:50] + "..." if len(str(v)) > 50 else str(v) 
                                         for k, v in all_cookies.items()} if all_cookies else {}
            logger.info(f"Cookies disponibles: {list(test_results['all_cookies'].keys())}")
        except Exception as e:
            logger.error(f"Error listando cookies: {str(e)}")
            test_results['list_error'] = str(e)
        
        # 5. Limpiar cookie de test
        try:
            controller.remove(test_results['test_cookie_name'])
            logger.info("Cookie de test eliminada")
        except Exception as e:
            logger.error(f"Error eliminando cookie de test: {str(e)}")
        
        logger.info("=== TEST DE COOKIES COMPLETADO ===")
        return test_results
        
    except Exception as e:
        logger.error(f"Error en test de cookies: {str(e)}")
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}