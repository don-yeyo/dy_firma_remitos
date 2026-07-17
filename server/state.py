import threading
import uuid

# Estado global de la tarea activa
_state = {
    "status": "idle",  # idle, scanning, processing, scanning-and-processing, syncing
    "action_id": None, # Identificador único de la corrida activa actual
    "cancel_requested": False,
    "progress_message": "",
    "current_step": 0,
    "total_steps": 0,
    "last_result": None
}

_lock = threading.Lock()

def get_state():
    """Devuelve una copia del estado actual de forma segura para subprocesos."""
    with _lock:
        return dict(_state)

def reset_state(status="idle"):
    """Reinicia el estado del proceso para una nueva corrida y retorna su ID único."""
    with _lock:
        new_id = uuid.uuid4().hex
        _state["status"] = status
        _state["action_id"] = new_id
        _state["cancel_requested"] = False
        _state["progress_message"] = "Iniciando proceso..."
        _state["current_step"] = 0
        _state["total_steps"] = 0
        _state["last_result"] = None
        return new_id

def set_idle(last_result=None, action_id=None):
    """Establece el estado a inactivo y registra el resultado si el ID de acción coincide."""
    with _lock:
        # Si se especifica un action_id, validar que sea la acción activa actual
        if action_id is not None and _state["action_id"] != action_id:
            # Descartar actualización de hilo residual/viejo
            return
            
        _state["status"] = "idle"
        _state["action_id"] = None
        _state["cancel_requested"] = False
        _state["progress_message"] = ""
        _state["current_step"] = 0
        _state["total_steps"] = 0
        if last_result is not None:
            _state["last_result"] = last_result

def update_progress(message: str, current: int = 0, total: int = 0):
    """Actualiza los detalles de progreso legibles por humanos."""
    with _lock:
        _state["progress_message"] = message
        _state["current_step"] = current
        _state["total_steps"] = total

def request_cancel() -> bool:
    """Solicita la cancelación si hay un proceso corriendo."""
    with _lock:
        if _state["status"] != "idle":
            _state["cancel_requested"] = True
            _state["progress_message"] = "Cancelación solicitada, deteniendo de forma limpia..."
            return True
        return False

def is_cancel_requested() -> bool:
    """Comprueba si se ha solicitado cancelar la tarea en curso."""
    with _lock:
        return _state["cancel_requested"]

class ProcessCancelledException(Exception):
    """Excepción que se lanza cuando el usuario cancela voluntariamente el proceso."""
    pass
