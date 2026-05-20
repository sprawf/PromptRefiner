"""Prompt Library — sticky-note grid with full CRUD."""
import tkinter as tk
from tkinter import messagebox
from typing import Callable

import customtkinter as ctk

from theme import (
    BG, SURFACE, SURF2, SURF3, BORDER2,
    ACCENT, ACCENTL, TEXT_P, TEXT_S,
    CARD_COLORS, CARD_TEXT, CARD_TEXT_S,
    FONT_FAMILY, FONT_SM_BOLD,
    PAD, PAD_SM, RADIUS, RADIUS_SM,
)

COLS   = 2
CARD_W = 300
CARD_H = 260


# ── Helper ────────────────────────────────────────────────────────────────────

def _btn(parent, text, command, width=None, fg_color=SURF2,
         hover=SURF3, text_color=TEXT_P, corner=RADIUS_SM, **kw):
    kw.update(text=text, command=command, fg_color=fg_color, hover_color=hover,
              text_color=text_color, corner_radius=corner, font=(FONT_FAMILY, 13))
    if width:
        kw['width'] = width
    return ctk.CTkButton(parent, **kw)


# ── Edit / New Prompt Dialog ──────────────────────────────────────────────────

class EditDialog(ctk.CTkToplevel):
    def __init__(self, parent, prompt: dict | None = None) -> None:
        super().__init__(parent)
        is_new = prompt is None
        self.title('New Prompt' if is_new else 'Edit Prompt')
        self.configure(fg_color=BG)
        self.resizable(False, False)
        self.grab_set()
        self.result: dict | None = None

        data = prompt or {'title': '', 'prompt': '', 'color': CARD_COLORS[0]}

        # Header
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        hdr.pack(fill='x')
        ctk.CTkLabel(hdr, text='New Prompt' if is_new else 'Edit Prompt',
                     font=(FONT_FAMILY, 16, 'bold'),
                     text_color=TEXT_P).pack(anchor='w', padx=PAD, pady=PAD_SM)

        # Body
        body = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        body.pack(fill='both', expand=True, padx=PAD, pady=PAD)

        ctk.CTkLabel(body, text='Title', font=FONT_SM_BOLD, text_color=TEXT_S).pack(anchor='w')
        self._title_var = tk.StringVar(value=data.get('title', ''))
        ctk.CTkEntry(body, textvariable=self._title_var, width=420,
                     fg_color=SURFACE, border_color=BORDER2, border_width=1,
                     text_color=TEXT_P, font=(FONT_FAMILY, 13),
                     corner_radius=RADIUS_SM).pack(fill='x', pady=(4, PAD))

        ctk.CTkLabel(body, text='Card colour', font=FONT_SM_BOLD, text_color=TEXT_S).pack(anchor='w')
        cf = ctk.CTkFrame(body, fg_color='transparent')
        cf.pack(anchor='w', pady=(4, PAD))

        self._color_var  = tk.StringVar(value=data.get('color', CARD_COLORS[0]))
        self._color_btns: dict[str, ctk.CTkButton] = {}
        for c in CARD_COLORS:
            btn = ctk.CTkButton(
                cf, text='', width=28, height=28, corner_radius=6,
                fg_color=c, hover_color=c, border_width=2,
                border_color=ACCENT if c == self._color_var.get() else BG,
                command=lambda col=c: self._pick(col),
            )
            btn.pack(side='left', padx=2)
            self._color_btns[c] = btn

        ctk.CTkLabel(body, text='Prompt', font=FONT_SM_BOLD, text_color=TEXT_S).pack(anchor='w')
        self._text = ctk.CTkTextbox(
            body, width=420, height=180, wrap='word',
            fg_color=SURFACE, border_color=BORDER2, border_width=1,
            text_color=TEXT_P, font=(FONT_FAMILY, 13), corner_radius=RADIUS_SM,
        )
        self._text.insert('1.0', data.get('prompt', ''))
        self._text.pack(fill='x', pady=(4, 0))

        # Footer
        foot = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        foot.pack(fill='x')
        _btn(foot, 'Save',   self._save,   width=100, fg_color=ACCENT, hover=ACCENTL).pack(side='right', padx=PAD, pady=PAD_SM)
        _btn(foot, 'Cancel', self.destroy, width=80).pack(side='right', pady=PAD_SM)

        self._center(parent)

    def _pick(self, color: str) -> None:
        self._color_var.set(color)
        for c, btn in self._color_btns.items():
            btn.configure(border_color=ACCENT if c == color else BG)

    def _save(self) -> None:
        title  = self._title_var.get().strip()
        prompt = self._text.get('1.0', 'end-1c').strip()
        if not title or not prompt:
            messagebox.showwarning('Required', 'Title and Prompt cannot be empty.', parent=self)
            return
        self.result = {'title': title, 'prompt': prompt, 'color': self._color_var.get()}
        self.destroy()

    def _center(self, parent) -> None:
        self.update_idletasks()
        try:
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            pw, ph = parent.winfo_width(),  parent.winfo_height()
            w,  h  = self.winfo_reqwidth(), self.winfo_reqheight()
            self.geometry(f'+{px + (pw - w) // 2}+{py + (ph - h) // 2}')
        except Exception:
            pass


# ── Library Window ────────────────────────────────────────────────────────────

class LibraryWindow:
    def __init__(self, root, prompts: list, on_select: Callable, on_save: Callable) -> None:
        self.root       = root
        self.prompts    = list(prompts)
        self.on_select  = on_select
        self.on_save    = on_save
        self.active_idx = 0
        self._cards: list[ctk.CTkFrame] = []
        self._build()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.win = ctk.CTkToplevel(self.root)
        self.win.title('Prompt Library — Prompt Refiner')
        self.win.configure(fg_color=BG)
        self.win.minsize(680, 460)
        self.win.withdraw()
        self.win.protocol('WM_DELETE_WINDOW', self.hide)
        self._build_header()
        self._build_grid()
        self._render_cards()
        self._center()

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(self.win, fg_color=SURFACE, corner_radius=0, height=72)
        hdr.pack(fill='x')
        hdr.pack_propagate(False)

        left = ctk.CTkFrame(hdr, fg_color='transparent')
        left.pack(side='left', fill='y', padx=PAD)
        ctk.CTkLabel(left, text='Prompt Library', font=(FONT_FAMILY, 15, 'bold'),
                     text_color=TEXT_P).pack(anchor='w', pady=(12, 0))
        self._active_lbl = ctk.CTkLabel(
            left,
            text=f'Active: {self.prompts[0]["title"] if self.prompts else "—"}',
            font=(FONT_FAMILY, 12), text_color=TEXT_S,
        )
        self._active_lbl.pack(anchor='w')

        right = ctk.CTkFrame(hdr, fg_color='transparent')
        right.pack(side='right', fill='y', padx=PAD)
        _btn(right, '＋ Add', self._add, width=88,
             fg_color=ACCENT, hover=ACCENTL).pack(anchor='e', pady=20)

        hint = ctk.CTkFrame(self.win, fg_color=SURF2, height=36, corner_radius=0)
        hint.pack(fill='x')
        hint.pack_propagate(False)
        ctk.CTkLabel(
            hint,
            text='Click to activate  ·  Double-click to edit  ·  ✕ to delete  ·  Alt+Shift+W to refine',
            font=(FONT_FAMILY, 11), text_color=TEXT_S,
        ).pack(side='left', padx=PAD)

    def _build_grid(self) -> None:
        self._scroll = ctk.CTkScrollableFrame(
            self.win, fg_color=BG,
            scrollbar_button_color=SURF2,
            scrollbar_button_hover_color=SURF3,
        )
        self._scroll.pack(fill='both', expand=True, padx=PAD, pady=PAD)

    # ── Cards ─────────────────────────────────────────────────────────────────

    def _render_cards(self) -> None:
        for w in self._scroll.winfo_children():
            w.destroy()
        self._cards.clear()
        for i, p in enumerate(self.prompts):
            row, col = divmod(i, COLS)
            card = self._make_card(i, p)
            card.grid(row=row, column=col, padx=8, pady=8, sticky='nsew')
            self._cards.append(card)
        self._highlight(self.active_idx)

    def _make_card(self, idx: int, prompt: dict) -> ctk.CTkFrame:
        color = prompt.get('color', CARD_COLORS[idx % len(CARD_COLORS)])
        outer = ctk.CTkFrame(self._scroll, fg_color=color, corner_radius=RADIUS,
                             border_width=2, border_color=BG, width=CARD_W)

        del_btn = ctk.CTkButton(
            outer, text='✕', width=24, height=24,
            fg_color='transparent', hover_color=color,
            text_color=CARD_TEXT_S, font=(FONT_FAMILY, 12), corner_radius=11,
            command=lambda i=idx: self._delete(i),
        )
        del_btn.place(relx=1.0, rely=0.0, anchor='ne', x=-4, y=4)
        del_btn.bind('<Button-1>', lambda e: 'break')

        title_lbl = ctk.CTkLabel(outer, text=prompt['title'],
                                 font=(FONT_FAMILY, 14, 'bold'), text_color=CARD_TEXT,
                                 anchor='w', wraplength=CARD_W - 36, justify='left')
        title_lbl.pack(anchor='w', padx=12, pady=(12, 4))

        ctk.CTkFrame(outer, fg_color=CARD_TEXT_S, height=1, corner_radius=0).pack(fill='x', padx=12, pady=(0, 6))

        preview = (prompt['prompt'][:300] + '…') if len(prompt['prompt']) > 300 else prompt['prompt']
        preview_lbl = ctk.CTkLabel(outer, text=preview, font=(FONT_FAMILY, 11),
                                   text_color=CARD_TEXT_S, anchor='nw',
                                   wraplength=CARD_W - 24, justify='left')
        preview_lbl.pack(fill='both', expand=True, padx=12, pady=(0, 12))

        for w in (outer, title_lbl, preview_lbl):
            w.bind('<Button-1>',        lambda e, i=idx: (self._select(i), 'break')[1])
            w.bind('<Double-Button-1>', lambda e, i=idx: (self._edit(i),   'break')[1])

        return outer

    def _highlight(self, idx: int) -> None:
        for i, card in enumerate(self._cards):
            card.configure(border_color=ACCENT if i == idx else BG)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _select(self, idx: int) -> None:
        self.active_idx = idx
        self._highlight(idx)
        self.on_select(self.prompts[idx])
        self._active_lbl.configure(text=f'Active: {self.prompts[idx]["title"]}')

    def _edit(self, idx: int) -> None:
        dlg = EditDialog(self.win, self.prompts[idx])
        self.win.wait_window(dlg)
        if dlg.result:
            self.prompts[idx] = dlg.result
            self.on_save(self.prompts)
            self._render_cards()
            self._select(idx)

    def _add(self) -> None:
        dlg = EditDialog(self.win)
        self.win.wait_window(dlg)
        if dlg.result:
            self.prompts.append(dlg.result)
            self.on_save(self.prompts)
            self._render_cards()
            self._select(len(self.prompts) - 1)

    def _delete(self, idx: int) -> None:
        if len(self.prompts) <= 1:
            messagebox.showwarning('Cannot delete', 'You need at least one prompt.', parent=self.win)
            return
        if messagebox.askyesno('Delete prompt', f'Delete "{self.prompts[idx]["title"]}"?', parent=self.win):
            self.prompts.pop(idx)
            self.active_idx = min(self.active_idx, len(self.prompts) - 1)
            self.on_save(self.prompts)
            self._render_cards()
            self._select(self.active_idx)

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
        w, h   = min(740, sw - 80), min(580, sh - 80)
        self.win.geometry(f'{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}')
