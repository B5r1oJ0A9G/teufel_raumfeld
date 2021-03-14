import logging
from typing import Any, Dict

from homeassistant.requirements import DATA_PIP_LOCK, RequirementsNotFound, pip_kwargs
import homeassistant.util.package as pkg_util

from .const import DOMAIN, ENFORCED_REQUIREMENTS

_LOGGER = logging.getLogger(__name__)


def log_info(message):
    """Logging of information."""
    _LOGGER.debug(message)


async def async_process_requirements(hass):
    """Install the requirements and bypass constraints."""
    pip_lock = hass.data.get(DATA_PIP_LOCK)
    if pip_lock is None:
        pip_lock = hass.data[DATA_PIP_LOCK] = asyncio.Lock()

    kwargs = pip_kwargs(hass.config.config_dir)

    if "constraints" in kwargs:
        del kwargs["constraints"]

    async with pip_lock:
        for req in ENFORCED_REQUIREMENTS:
            if pkg_util.is_installed(req):
                continue

            def _install(req: str, kwargs: Dict[str, Any]) -> bool:
                """Install requirement."""
                return pkg_util.install_package(req, **kwargs)

            log_info("Enforced installation of requirement: %s" % req)
            ret = await hass.async_add_executor_job(_install, req, kwargs)

            if not ret:
                raise RequirementsNotFound(DOMAIN, [req])
