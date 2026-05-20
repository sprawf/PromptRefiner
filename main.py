import os
import sys
import time
import queue
import logging
import logging.handlers
import threading
import tkinter as tk

import customtkinter as ctk
import keyboard
import pyperclip
import pystray
from PIL import Image, ImageDraw, ImageFont

from storage  import load_config, save_config, load_prompts, save_prompts, appdata_dir, log_path
from engine   import build_provider, LocalProvider, Provider
from overlay  import OverlayWindow
from library  import LibraryWindow
from settings import SettingsWindow

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')

# ── Logging ───────────────────────────────────────────────────────────────────

os.makedirs(appdata_dir(), exist_ok=True)
_log_handler = logging.handlers.RotatingFileHandler(
    log_path(), maxBytes=1_000_000, backupCount=3, encoding='utf-8',
)
_log_handler.setFormatter(logging.Formatter('%(asctime)s  %(levelname)-8s  %(name)s: %(message)s'))
logging.getLogger().addHandler(_log_handler)
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger('main')

VERSION = '1.0.0'


# ── App ───────────────────────────────────────────────────────────────────────

class App:
    def __init__(self) -> None:
        self._q:        queue.Queue = queue.Queue()
        self._refine_t0: float      = 0.0

        self.config  = load_config()
        self.prompts = load_prompts()
        self.active_prompt: dict = self.prompts[0] if self.prompts else {
            'title': 'Refine', 'prompt': 'Improve the following text and return only the result.'
        }

        self.root = ctk.CTk()
        self.root.withdraw()
        self.root.title('Prompt Refiner')

        self.provider: Provider = build_provider(self.config)

        self.overlay  = OverlayWindow(self.root)
        self.library  = LibraryWindow(self.root, self.prompts,
                                      on_select=self._on_prompt_selected,
                                      on_save=self._on_prompts_saved)
        self.settings = SettingsWindow(self.root, self.config,
                                       on_save=self._on_settings_saved)

        # Event dispatch table
        self._dispatch = {
            'refine':          self._do_refine,
            'library':         lambda _: self.library.show(),
            'settings':        lambda _: self.settings.show(),
            'done':            self._on_done,
            'error':           self.overlay.show_error,
            'model_ready':     self._on_model_ready,
            'model_error':     lambda d: self._notify('Model failed to load', str(d)[:120]),
            'switch_provider': self._switch_provider,
        }

        self._register_hotkeys()
        self._start_tray()

        if isinstance(self.provider, LocalProvider):
            threading.Thread(target=self._load_model, daemon=True).start()

        threading.Thread(target=self._prewarm, daemon=True).start()

        self.root.after(50, self._poll)
        logger.info(f'Prompt Refiner v{VERSION} started.')

    # ── Hotkeys ───────────────────────────────────────────────────────────────

    def _hotkey_cfg(self) -> dict:
        return self.config.get('hotkeys', {'refine': 'alt+shift+w', 'library': 'alt+shift+e'})

    def _register_hotkeys(self) -> None:
        keyboard.unhook_all()
        hk = self._hotkey_cfg()
        try:
            keyboard.add_hotkey(hk.get('refine',  'alt+shift+w'), self._hk_refine,  suppress=True)
            keyboard.add_hotkey(hk.get('library', 'alt+shift+e'), self._hk_library, suppress=True)
            logger.info(f'Hotkeys registered: refine={hk.get("refine")} library={hk.get("library")}')
        except Exception as e:
            logger.error(f'Hotkey registration failed: {e}')

    def _hk_refine(self) -> None:
        logger.info(f'Hotkey {self._hotkey_cfg().get("refine")} fired.')
        threading.Thread(target=self._capture_and_queue, daemon=True).start()

    def _capture_and_queue(self) -> None:
        time.sleep(0.05)
        prev = pyperclip.paste()
        keyboard.send('ctrl+c')
        changed = False
        for _ in range(10):
            time.sleep(0.05)
            current = pyperclip.paste()
            if current != prev:
                changed = True
                break
        captured = current if changed else ''
        logger.info(f'Captured text ({len(captured)} chars): {captured[:80]!r}')
        self._q.put(('refine', captured))

    def _hk_library(self) -> None:
        self._q.put(('library', None))

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _on_prompt_selected(self, prompt: dict) -> None:
        self.active_prompt = prompt

    def _on_prompts_saved(self, prompts: list) -> None:
        self.prompts = prompts
        save_prompts(prompts)
        if prompts and self.active_prompt not in prompts:
            self.active_prompt = prompts[0]

    def _on_settings_saved(self, new_config: dict) -> None:
        self.config   = new_config
        save_config(new_config)
        self.provider = build_provider(new_config)
        if isinstance(self.provider, LocalProvider):
            threading.Thread(target=self._load_model, daemon=True).start()
        self._register_hotkeys()
        self._update_tray()

    # ── Pre-warm ──────────────────────────────────────────────────────────────

    def _prewarm(self) -> None:
        try:
            self.provider.refine('Hello', 'Reply with one word: OK')
            logger.info('Connection pre-warmed.')
        except Exception as e:
            logger.info(f'Pre-warm skipped: {e!s:.60}')

    # ── Model loading ─────────────────────────────────────────────────────────

    def _load_model(self) -> None:
        try:
            self.provider.load()
            self._q.put(('model_ready', None))
        except Exception as e:
            logger.error(f'Model load failed: {e}')
            self._q.put(('model_error', str(e)))

    # ── Event loop ────────────────────────────────────────────────────────────

    def _poll(self) -> None:
        try:
            while True:
                event, data = self._q.get_nowait()
                handler = self._dispatch.get(event)
                if handler:
                    handler(data)
        except queue.Empty:
            pass
        self.root.after(50, self._poll)

    def _on_done(self, result: str) -> None:
        elapsed = time.time() - self._refine_t0
        self.overlay.show_done(elapsed)
        pyperclip.copy(result)
        self.root.after(60, lambda: keyboard.send('ctrl+v'))
        logger.info(f'Refinement complete in {elapsed:.2f}s')

    def _on_model_ready(self, _) -> None:
        logger.info('Model ready.')
        self._update_tray()
        hk = self._hotkey_cfg().get('refine', 'alt+shift+w').upper()
        self._notify('Prompt Refiner is ready ⚡', f'Select any text and press {hk} to refine it.')

    def _do_refine(self, text: str) -> None:
        if not text or not text.strip():
            self.overlay.show_no_selection()
            return
        if isinstance(self.provider, LocalProvider) and not self.provider.ready:
            self.overlay.show_loading_model()
            return
        if not self.provider.ready:
            self.overlay.show_error('API key required — open Settings')
            return

        self._refine_t0 = time.time()
        self.overlay.show()
        prompt   = self.active_prompt
        provider = self.provider

        def infer() -> None:
            try:
                result = provider.refine(text, prompt['prompt'])
                self._q.put(('done', result))
            except Exception as e:
                logger.error(f'Inference error: {e}')
                self._q.put(('error', str(e)[:60]))

        threading.Thread(target=infer, daemon=True).start()

    # ── System tray ───────────────────────────────────────────────────────────

    def _make_icon(self) -> Image.Image:
        img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        d   = ImageDraw.Draw(img)
        d.rounded_rectangle([2, 2, 62, 62], radius=14, fill='#1a1a2e')
        try:
            fnt = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 24)
            d.text((10, 16), '⚡PR', fill='#a0a0ff', font=fnt)
        except Exception:
            d.text((10, 20), 'PR', fill='#a0a0ff')
        return img

    def _start_tray(self) -> None:
        self._tray = pystray.Icon(
            'PromptRefiner', self._make_icon(), self._tooltip(), self._make_menu(),
        )
        threading.Thread(target=self._tray.run, daemon=True).start()
        logger.info('Tray started.')

    def _make_menu(self) -> pystray.Menu:
        def prov_item(key: str, label: str) -> pystray.MenuItem:
            return pystray.MenuItem(
                label,
                lambda: self._q.put(('switch_provider', key)),
                checked=lambda item, k=key: self.config.get('active_provider') == k,
                radio=True,
            )
        hk = self._hotkey_cfg()
        return pystray.Menu(
            pystray.MenuItem(f'Prompt Refiner  v{VERSION}', None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Provider', pystray.Menu(
                prov_item('local',    'Qwen 2.5 1.5B (Local · Free)'),
                prov_item('groq',     'Groq'),
                prov_item('cerebras', 'Cerebras'),
            )),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(f'Prompt Library  ({hk.get("library","alt+shift+e").upper()})',
                             lambda: self._q.put(('library', None))),
            pystray.MenuItem('Settings', lambda: self._q.put(('settings', None))),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Quit', self._quit),
        )

    def _switch_provider(self, key: str) -> None:
        self.config['active_provider'] = key
        save_config(self.config)
        self.provider = build_provider(self.config)
        if isinstance(self.provider, LocalProvider):
            threading.Thread(target=self._load_model, daemon=True).start()
        self._update_tray()
        logger.info(f'Switched to provider: {key}')

    def _tooltip(self) -> str:
        active = self.config.get('active_provider', 'local')
        status = 'Ready' if self.provider.ready else 'Loading model…'
        return f'Prompt Refiner  ·  {active.title()}  ·  {status}'

    def _update_tray(self) -> None:
        try:
            self._tray.title = self._tooltip()
            self._tray.menu  = self._make_menu()
        except Exception:
            pass

    def _notify(self, title: str, msg: str) -> None:
        try:
            self._tray.notify(msg, title)
        except Exception:
            pass

    def _quit(self) -> None:
        logger.info('Shutting down.')
        keyboard.unhook_all()
        try:
            self._tray.stop()
        except Exception:
            pass
        self.root.quit()

    def run(self) -> None:
        self.root.mainloop()


# ── Entry point ───────────────────────────────────────────────────────────────

def _ensure_single_instance() -> None:
    import ctypes
    mutex = ctypes.windll.kernel32.CreateMutexW(None, True, 'PromptRefiner_SingleInstance')
    if ctypes.windll.kernel32.GetLastError() == 183:
        sys.exit(0)

if __name__ == '__main__':
    _ensure_single_instance()
    app = App()
    import signal
    signal.signal(signal.SIGTERM, lambda *_: app._quit())
    signal.signal(signal.SIGINT,  lambda *_: app._quit())
    app.run()
