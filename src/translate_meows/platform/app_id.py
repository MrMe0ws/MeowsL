"""AppUserModelID: без него Windows берёт для панели задач иконку python.exe."""

from __future__ import annotations

import ctypes

from translate_meows.config import APP_DISPLAY_NAME, SETTINGS_ORG

APP_USER_MODEL_ID = f"{SETTINGS_ORG}.{APP_DISPLAY_NAME}"


def set_app_user_model_id() -> bool:
    """Привязывает окна процесса к своей иконке. Вызывать до создания окон."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            APP_USER_MODEL_ID
        )
    except Exception:
        return False
    return True
