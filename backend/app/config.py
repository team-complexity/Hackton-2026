"""Configuración leída de variables de entorno o de backend/.env."""

from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ_BACKEND = Path(__file__).resolve().parent.parent


class Configuracion(BaseSettings):
    """Variables de entorno del servidor (spec 001, RF-022, RF-034, RF-041)."""

    model_config = SettingsConfigDict(
        env_file=RAIZ_BACKEND / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    pey_api_base_url: str = "https://api.pey.mx"
    pey_api_key: SecretStr = SecretStr("")
    pey_webhook_secret: SecretStr = SecretStr("")

    # Origen de la web permitido por CORS. Varios orígenes separados por coma.
    web_origin: str = "http://localhost:5173"

    # Carpeta de la web que el servidor entrega en `/`. Vacía en las pruebas:
    # no entrega la web. En la demo, ../web (spec 003, DP-21, R-12).
    carpeta_web: str = ""

    # Límites de la demo pública.
    monto_maximo: Decimal = Decimal("100")
    expiracion_segundos: int = 600  # pey exige 0 o al menos 360
    limite_cobros_por_minuto: int = 10

    # IPs de las que se acepta X-Forwarded-For. El valor por defecto no confía en la red.
    proxies_confiables: str = "127.0.0.1"
    # Segundos de escucha después del vencimiento (spec 001, RF-022).
    gracia_segundos: int = 600
    canales_por_ip: int = 10

    @property
    def origenes_web(self) -> list[str]:
        return [o.strip() for o in self.web_origin.split(",") if o.strip()]


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
