from abc import ABC, abstractmethod

class NotificationService(ABC):
    """
    Interfaz base para todos los servicios de notificación.
    Patrón Strategy: cada servicio implementa send() a su manera.
    """
    
    @abstractmethod
    def send(self, message: str, username: str) -> dict:
        """
        Envía un mensaje a la plataforma correspondiente.
        Devuelve un dict con status y provider_response.
        """
        pass