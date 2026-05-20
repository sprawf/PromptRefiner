import os
import sys
import json
import shutil
import logging

logger = logging.getLogger(__name__)

APP_NAME = 'PromptRefiner'
VERSION  = '1.0.0'


def appdata_dir() -> str:
    base = os.environ.get('APPDATA', os.path.expanduser('~'))
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def resource_path(filename: str) -> str:
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS  # type: ignore
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)


def config_path() -> str:
    return os.path.join(appdata_dir(), 'config.json')


def prompts_path() -> str:
    return os.path.join(appdata_dir(), 'prompts.json')


def log_path() -> str:
    return os.path.join(appdata_dir(), 'app.log')


DEFAULT_CONFIG: dict = {
    'version': VERSION,
    'active_provider': 'cerebras',   # fastest out of the box
    'autostart': True,
    'hotkeys': {
        'refine':  'alt+shift+w',
        'library': 'alt+shift+e',
    },
    'providers': {
        'local':    {'model_id': 'Qwen/Qwen2.5-1.5B-Instruct-GGUF'},
        'groq':     {'api_key': '', 'model': 'llama-3.3-70b-versatile'},
        'cerebras': {'api_key': '', 'model': 'llama3.1-8b'},
    },
}


def load_config() -> dict:
    path = config_path()
    try:
        with open(path, encoding='utf-8') as f:
            cfg = json.load(f)
        merged = {**DEFAULT_CONFIG, **cfg}
        merged['providers'] = {**DEFAULT_CONFIG['providers'], **cfg.get('providers', {})}
        merged['hotkeys']   = {**DEFAULT_CONFIG['hotkeys'],   **cfg.get('hotkeys',   {})}
        # Drop stale 'gemini' provider key left over from previous versions
        merged['providers'].pop('gemini', None)
        return merged
    except FileNotFoundError:
        save_config(DEFAULT_CONFIG)
        return dict(DEFAULT_CONFIG)
    except Exception as e:
        logger.error(f'Config load error: {e} — using defaults')
        return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> None:
    try:
        with open(config_path(), 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f'Config save error: {e}')


_FALLBACK_COLORS = [
    '#FFF9C4', '#DCEDC8', '#BBDEFB', '#F8BBD0',
    '#FFE0B2', '#E1BEE7', '#D7CCC8', '#B2DFDB',
]

def load_prompts() -> list:
    user_path = prompts_path()
    if not os.path.exists(user_path):
        try:
            shutil.copy2(resource_path('prompts.json'), user_path)
            logger.info('Default prompts copied to AppData.')
        except Exception as e:
            logger.error(f'Failed to copy default prompts: {e}')
            return []
    try:
        with open(user_path, encoding='utf-8') as f:
            prompts = json.load(f)
        # Migrate: add color field if missing (old installs pre-color support)
        changed = False
        for i, p in enumerate(prompts):
            if 'color' not in p:
                p['color'] = _FALLBACK_COLORS[i % len(_FALLBACK_COLORS)]
                changed = True
        if changed:
            save_prompts(prompts)
            logger.info('Migrated prompts: added missing color fields.')
        return prompts
    except Exception as e:
        logger.error(f'Prompts load error: {e}')
        return []


def save_prompts(prompts: list) -> None:
    try:
        with open(prompts_path(), 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f'Prompts save error: {e}')


def set_autostart(enabled: bool) -> None:
    import winreg
    exe = sys.executable if getattr(sys, 'frozen', False) else None
    if not exe:
        return  # Don't set autostart when running from source
    key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe}"')
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        logger.error(f'Autostart error: {e}')
