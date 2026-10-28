from pathlib import Path
import json
import os
import stat

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / '.private'
CREDENTIALS = STATE_DIR / 'credentials.json'
PROVIDER_KEYS = {
    'keepa': ('KEEPA_API_KEY',),
    'sp-api': ('SP_API_CLIENT_ID', 'SP_API_CLIENT_SECRET', 'SP_API_REFRESH_TOKEN'),
}

class ConfigurationError(Exception):
    pass

def load_credentials(path=CREDENTIALS):
    data = {}
    if path.exists():
        if path.is_symlink() or stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise ConfigurationError('El archivo privado debe ser regular y tener permisos 600.')
        try:
            data = json.loads(path.read_text())
        except (ValueError, OSError):
            raise ConfigurationError('No se puede leer la configuración privada.') from None
        if not isinstance(data, dict):
            raise ConfigurationError('Formato de configuración privada incorrecto.')
    names = {n for keys in PROVIDER_KEYS.values() for n in keys}
    return {n: os.environ.get(n) or data.get(n, '') for n in names}

def readiness(values):
    return {p: {'configured': all(values.get(k) for k in keys),
                'missing': [k for k in keys if not values.get(k)]}
            for p, keys in PROVIDER_KEYS.items()}

def save_credentials(values, path=CREDENTIALS):
    names = {n for keys in PROVIDER_KEYS.values() for n in keys}
    if any(k not in names for k in values):
        raise ConfigurationError('Variable de credencial desconocida.')
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    if path.is_symlink():
        raise ConfigurationError('No se escribe en un enlace simbólico.')
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, 'w') as f:
        os.fchmod(f.fileno(), 0o600)
        json.dump({k: str(v) for k, v in values.items() if k in names and v}, f)
