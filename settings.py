"""Settings window — General + Providers tabs, sidebar layout."""
import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from engine  import PROVIDER_KEYS, GROQ_MODELS, CEREBRAS_MODELS
from storage import set_autostart, appdata_dir
from theme   import (
    BG, SURFACE, SURF2, SURF3, BORDER, BORDER2,
    ACCENT, ACCENTL, TEXT_P, TEXT_S,
    FONT_FAMILY, FONT_SM_BOLD,
    PAD, PAD_SM, RADIUS, RADIUS_SM,
)

SIDEBAR_W = 180


class SettingsWindow:
    def __init__(self, root, config: dict, on_save: Callable) -> None:
        self.root    = root
        self.config  = config
        self.on_save = on_save
        self._api_widgets: dict[str, dict]          = {}
        self._nav_btns:    dict[str, ctk.CTkButton] = {}
        self._panels:      dict[str, ctk.CTkFrame]  = {}
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.win = ctk.CTkToplevel(self.root)
        self.win.title('Settings — Prompt Refiner')
        self.win.configure(fg_color=BG)
        self.win.resizable(False, False)
        self.win.withdraw()
        self.win.protocol('WM_DELETE_WINDOW', self.hide)

        # Header
        hdr = ctk.CTkFrame(self.win, fg_color=SURFACE, corner_radius=0, height=60)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text='Settings', font=(FONT_FAMILY, 15, 'bold'),
                     text_color=TEXT_P).pack(side='left', anchor='w', padx=PAD, pady=PAD_SM)
        ctk.CTkLabel(hdr, text='Prompt Refiner', font=(FONT_FAMILY, 9),
                     text_color=TEXT_S).pack(side='right', anchor='e', padx=PAD)

        # Body: sidebar + content
        body = ctk.CTkFrame(self.win, fg_color=BG, corner_radius=0)
        body.pack(fill='both', expand=True)

        sidebar = ctk.CTkFrame(body, fg_color=SURFACE, corner_radius=0, width=SIDEBAR_W)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        ctk.CTkLabel(sidebar, text='MENU', font=(FONT_FAMILY, 8, 'bold'),
                     text_color=TEXT_S).pack(anchor='w', padx=PAD, pady=(PAD, 4))

        content_host = ctk.CTkFrame(body, fg_color=BG, corner_radius=0)
        content_host.pack(side='left', fill='both', expand=True)

        self._panels['general']   = self._build_general(content_host)
        self._panels['providers'] = self._build_providers(content_host)

        for key, label in [('general', '⚙  General'), ('providers', '🔌  Providers')]:
            btn = ctk.CTkButton(
                sidebar, text=label, anchor='w', font=(FONT_FAMILY, 10), height=36,
                fg_color='transparent', hover_color=SURF2, text_color=TEXT_P,
                corner_radius=RADIUS_SM, command=lambda k=key: self._show_panel(k),
            )
            btn.pack(fill='x', padx=6, pady=2)
            self._nav_btns[key] = btn

        # Footer
        foot = ctk.CTkFrame(self.win, fg_color=SURFACE, corner_radius=0, height=56)
        foot.pack(fill='x', side='bottom')
        foot.pack_propagate(False)
        ctk.CTkButton(foot, text='Save',   width=100, height=34, fg_color=ACCENT,  hover_color=ACCENTL,
                      text_color=TEXT_P, font=(FONT_FAMILY, 10), corner_radius=RADIUS_SM,
                      command=self._save).pack(side='right', padx=PAD, pady=PAD_SM)
        ctk.CTkButton(foot, text='Cancel', width=80,  height=34, fg_color=SURF2,   hover_color=SURF3,
                      text_color=TEXT_P, font=(FONT_FAMILY, 10), corner_radius=RADIUS_SM,
                      command=self.hide).pack(side='right', pady=PAD_SM)

        self._show_panel('general')
        self._center()

    # ── General panel ─────────────────────────────────────────────────────────

    def _build_general(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)

        def section(title):
            ctk.CTkLabel(frame, text=title, font=(FONT_FAMILY, 9, 'bold'),
                         text_color=TEXT_S).pack(anchor='w', padx=PAD, pady=(PAD, 4))

        def divider():
            ctk.CTkFrame(frame, fg_color=BORDER, height=1,
                         corner_radius=0).pack(fill='x', padx=PAD, pady=PAD_SM)

        section('HOTKEYS')
        hk_cfg = self.config.get('hotkeys', {'refine': 'alt+shift+w', 'library': 'alt+shift+e'})
        self._hotkey_vars: dict[str, tk.StringVar] = {}
        for action, label in [('refine', 'Refine selected text'), ('library', 'Open Prompt Library')]:
            row = ctk.CTkFrame(frame, fg_color='transparent')
            row.pack(fill='x', padx=PAD, pady=3)
            ctk.CTkLabel(row, text=label, font=(FONT_FAMILY, 10),
                         text_color=TEXT_P, anchor='w', width=190).pack(side='left')
            var = tk.StringVar(value=hk_cfg.get(action, ''))
            self._hotkey_vars[action] = var
            ctk.CTkLabel(row, textvariable=var, font=(FONT_FAMILY, 9, 'bold'),
                         text_color=ACCENT, fg_color=SURF2, corner_radius=RADIUS_SM,
                         padx=10, pady=3, width=130).pack(side='left', padx=(0, 6))
            ctk.CTkButton(
                row, text='Record', width=64, height=26, font=(FONT_FAMILY, 9),
                fg_color=SURF3, hover_color=SURF2, text_color=TEXT_S, corner_radius=RADIUS_SM,
                command=lambda a=action, v=var: self._record_hotkey(a, v),
            ).pack(side='left')

        divider()

        section('STARTUP')
        row = ctk.CTkFrame(frame, fg_color='transparent')
        row.pack(fill='x', padx=PAD, pady=3)
        ctk.CTkLabel(row, text='Launch on Windows startup',
                     font=(FONT_FAMILY, 10), text_color=TEXT_P).pack(side='left')
        self._autostart_var = tk.BooleanVar(value=self.config.get('autostart', True))
        ctk.CTkSwitch(row, text='', variable=self._autostart_var, onvalue=True, offvalue=False,
                      progress_color=ACCENT, button_color=TEXT_P, fg_color=SURF3).pack(side='right')

        divider()

        section('DATA')
        path_frame = ctk.CTkFrame(frame, fg_color=SURF2, corner_radius=RADIUS_SM)
        path_frame.pack(fill='x', padx=PAD, pady=(0, PAD_SM))
        ctk.CTkLabel(path_frame, text=appdata_dir(), font=(FONT_FAMILY, 9),
                     text_color=TEXT_S, anchor='w').pack(padx=PAD_SM, pady=6, anchor='w')
        ctk.CTkLabel(frame, text='Config, prompts, and logs are stored here. Safe to back up.',
                     font=(FONT_FAMILY, 8), text_color=TEXT_S).pack(anchor='w', padx=PAD)

        return frame

    # ── Hotkey capture ────────────────────────────────────────────────────────

    def _record_hotkey(self, action: str, var: tk.StringVar) -> None:
        import threading, keyboard
        prev = var.get()
        var.set('… press keys …')

        def capture():
            try:
                combo = keyboard.read_hotkey(suppress=False)
                if combo.lower() in ('escape', 'esc'):
                    var.set(prev)
                    return
                parts = {p.lower() for p in combo.split('+')}
                if not parts & {'ctrl', 'alt', 'shift', 'windows', 'win'}:
                    var.set(prev)
                    return
                var.set(combo)
            except Exception:
                var.set(prev)

        threading.Thread(target=capture, daemon=True).start()

    # ── Providers panel ───────────────────────────────────────────────────────

    def _build_providers(self, parent) -> ctk.CTkFrame:
        frame = ctk.CTkFrame(parent, fg_color=BG, corner_radius=0)
        pcfg  = self.config.get('providers', {})

        ctk.CTkLabel(frame, text='ACTIVE PROVIDER', font=(FONT_FAMILY, 9, 'bold'),
                     text_color=TEXT_S).pack(anchor='w', padx=PAD, pady=(PAD, 4))

        self._provider_var = tk.StringVar(value=self.config.get('active_provider', 'local'))

        prov_grid = ctk.CTkFrame(frame, fg_color='transparent')
        prov_grid.pack(fill='x', padx=PAD, pady=(0, PAD_SM))
        self._prov_cards: dict[str, ctk.CTkFrame] = {}

        short_desc = {'local': 'Free · Offline', 'groq': 'Free tier', 'cerebras': 'Free tier · Fast'}
        for i, key in enumerate(PROVIDER_KEYS):
            card = ctk.CTkFrame(prov_grid, fg_color=SURF2, corner_radius=RADIUS,
                                border_width=2, border_color=BG, cursor='hand2')
            card.grid(row=0, column=i, padx=4, sticky='nsew')
            prov_grid.columnconfigure(i, weight=1)
            ctk.CTkLabel(card, text=key.upper(), font=(FONT_FAMILY, 8, 'bold'),
                         text_color=ACCENT).pack(padx=PAD_SM, pady=(8, 0))
            ctk.CTkLabel(card, text=short_desc[key], font=(FONT_FAMILY, 8),
                         text_color=TEXT_S).pack(padx=PAD_SM, pady=(0, 8))
            card.bind('<Button-1>', lambda e, k=key: self._pick_provider(k))
            for child in card.winfo_children():
                child.bind('<Button-1>', lambda e, k=key: self._pick_provider(k))
            self._prov_cards[key] = card

        self._refresh_provider_cards()

        ctk.CTkFrame(frame, fg_color=BORDER, height=1,
                     corner_radius=0).pack(fill='x', padx=PAD, pady=PAD_SM)

        ctk.CTkLabel(frame, text='CREDENTIALS', font=(FONT_FAMILY, 9, 'bold'),
                     text_color=TEXT_S).pack(anchor='w', padx=PAD, pady=(0, 4))

        self._cred_host = ctk.CTkFrame(frame, fg_color='transparent')
        self._cred_host.pack(fill='x', padx=PAD)

        models_map = {'groq': GROQ_MODELS, 'cerebras': CEREBRAS_MODELS}
        for key in ['groq', 'cerebras']:
            p      = pcfg.get(key, {})
            models = models_map[key]
            cframe = ctk.CTkFrame(self._cred_host, fg_color='transparent')
            self._api_widgets[key] = {'frame': cframe}

            ctk.CTkLabel(cframe, text='API Key', font=FONT_SM_BOLD,
                         text_color=TEXT_S).pack(anchor='w', pady=(0, 2))
            key_row = ctk.CTkFrame(cframe, fg_color='transparent')
            key_row.pack(fill='x', pady=(0, 4))

            key_var = tk.StringVar(value=p.get('api_key', ''))
            entry = ctk.CTkEntry(key_row, textvariable=key_var, width=340, show='•',
                                 fg_color=SURF2, border_color=BORDER2, border_width=1,
                                 text_color=TEXT_P, font=(FONT_FAMILY, 10),
                                 corner_radius=RADIUS_SM)
            entry.pack(side='left', fill='x', expand=True)
            ctk.CTkButton(
                key_row, text='Show', width=54, height=32,
                fg_color=SURF3, hover_color=SURF2, text_color=TEXT_S,
                font=(FONT_FAMILY, 9), corner_radius=RADIUS_SM,
                command=lambda e=entry: e.configure(show='' if e.cget('show') == '•' else '•'),
            ).pack(side='left', padx=(4, 0))
            self._api_widgets[key]['api_key'] = key_var

            ctk.CTkLabel(cframe, text='Model', font=FONT_SM_BOLD,
                         text_color=TEXT_S).pack(anchor='w', pady=(0, 2))
            model_var = tk.StringVar(value=p.get('model', models[0]))
            ctk.CTkComboBox(cframe, values=models, variable=model_var, width=260,
                            fg_color=SURF2, border_color=BORDER2, border_width=1,
                            text_color=TEXT_P, button_color=SURF3,
                            dropdown_fg_color=SURFACE, font=(FONT_FAMILY, 10),
                            state='readonly', corner_radius=RADIUS_SM).pack(anchor='w', pady=(0, PAD))
            self._api_widgets[key]['model'] = model_var

        self._refresh_cred_panel()
        return frame

    # ── Nav ───────────────────────────────────────────────────────────────────

    def _show_panel(self, key: str) -> None:
        for k, panel in self._panels.items():
            panel.pack_forget()
        self._panels[key].pack(fill='both', expand=True)
        for k, btn in self._nav_btns.items():
            btn.configure(fg_color=SURF2 if k == key else 'transparent')

    def _pick_provider(self, key: str) -> None:
        self._provider_var.set(key)
        self._refresh_provider_cards()
        self._refresh_cred_panel()

    def _refresh_provider_cards(self) -> None:
        active = self._provider_var.get()
        for k, card in self._prov_cards.items():
            card.configure(border_color=ACCENT if k == active else BG)

    def _refresh_cred_panel(self) -> None:
        selected = self._provider_var.get()
        for key, w in self._api_widgets.items():
            if key == selected:
                w['frame'].pack(fill='x')
            else:
                w['frame'].pack_forget()

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self) -> None:
        cfg = dict(self.config)
        cfg['active_provider'] = self._provider_var.get()
        cfg['autostart']       = self._autostart_var.get()
        cfg['hotkeys']         = {k: v.get() for k, v in self._hotkey_vars.items()}
        cfg.setdefault('providers', {})
        for key in ['groq', 'cerebras']:
            w = self._api_widgets[key]
            cfg['providers'].setdefault(key, {})
            cfg['providers'][key]['api_key'] = w['api_key'].get().strip()
            cfg['providers'][key]['model']   = w['model'].get()
        try:
            set_autostart(cfg['autostart'])
        except Exception:
            pass
        self.on_save(cfg)
        self.hide()

    # ── Show / hide ───────────────────────────────────────────────────────────

    def show(self) -> None:
        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()

    def hide(self) -> None:
        self.win.withdraw()

    def _center(self) -> None:
        self.win.update_idletasks()
        sw, sh = self.win.winfo_screenwidth(), self.win.winfo_screenheight()
        w = max(self.win.winfo_reqwidth()  or 560, 560)
        h = max(self.win.winfo_reqheight() or 480, 480)
        self.win.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')
