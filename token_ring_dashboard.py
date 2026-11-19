"""Bảng điều khiển Token Ring và chế độ mô phỏng trên một máy."""

from collections import deque
from concurrent.futures import Future
from copy import deepcopy
import tkinter as tk
from tkinter import ttk
from typing import Callable

from token_ring import RingNode


MEMBERS = ("M1", "M2", "M3", "M4")
DEVICES = {
    "DEV-01": "Máy chiếu Sony",
    "DEV-02": "Kit Arduino #02",
    "DEV-03": "Kit Arduino #03",
}
PAGE = "#eef3f8"
CARD = "#ffffff"
INK = "#14233c"
MUTED = "#526480"
ACCENTS = ("#2563eb", "#16a34a", "#ea580c", "#7c3aed")


class DemoRing:
    """Mô phỏng tầng gửi bằng hàng đợi, mỗi bước giao đúng một gói."""

    def __init__(self):
        self.messages = deque()
        self.state = {
            device: {"status": "AVAILABLE", "by": None} for device in DEVICES
        }
        self.nodes = {
            node: RingNode(
                node,
                MEMBERS,
                lambda target, message, sender=node: self.messages.append(
                    (sender, target, message)
                ),
            )
            for node in MEMBERS
        }
        self.nodes[MEMBERS[0]].start(self.state)

    def submit(self, node: str, device: str, borrow: bool) -> Future[bool]:
        def operation(state):
            entry = state[device]
            if borrow and entry["status"] == "AVAILABLE":
                entry.update(status="BORROWED", by=node)
                return True
            if not borrow and entry["by"] == node:
                entry.update(status="AVAILABLE", by=None)
                return True
            return False

        return self.nodes[node].submit(operation)

    def step(self):
        sender, target, token = self.messages.popleft()
        self.nodes[target].receive(sender, token)
        self.state = deepcopy(self.messages[0][2]["state"])
        return sender, target, token


class RingView(ttk.Frame):
    """Giao diện nhận thao tác qua callback và nhận trạng thái qua update_token."""

    def __init__(
        self,
        parent,
        members: tuple[str, ...],
        submit: Callable[[str, str, bool], Future[bool]],
        batch: Callable[[str, bool], None] | None = None,
    ):
        super().__init__(parent, padding=20, style="Page.TFrame")
        style = ttk.Style(self)
        style.theme_use("clam")
        self._dark = False
        self._last_target = None
        self.members = members
        self.submit = submit
        self.device = tk.StringVar(value=next(iter(DEVICES)))
        self.status = {node: tk.StringVar(value="Sẵn sàng") for node in members}
        self.nodes = {}
        self.controls = {}

        header = tk.Frame(self, bg=CARD, padx=16, pady=12)
        header.pack(fill="x", pady=(0, 10))
        self.theme_button = ttk.Button(
            header, style="Theme.TButton", width=2, command=self.toggle_theme
        )
        self.theme_button.pack(side="right", anchor="n")
        heading = tk.Frame(header, bg=CARD)
        heading.pack(side="left")
        self._label(heading, "Token Ring Lab", size=20, bold=True).pack(anchor="w")
        self._label(heading, "Mượn trả thiết bị phòng lab", color=MUTED).pack(anchor="w")

        toolbar = tk.Frame(self, bg=CARD, padx=12, pady=8)
        toolbar.pack(fill="x", pady=(0, 10))
        if batch:
            ttk.Button(
                toolbar, text="4 máy cùng mượn", style="Batch.TButton",
                command=lambda: batch(self.device.get(), True),
            ).pack(side="left")
            ttk.Button(
                toolbar, text="4 máy cùng trả", style="Return.TButton",
                command=lambda: batch(self.device.get(), False),
            ).pack(side="left", padx=(8, 0))
        self.token_status = tk.StringVar(value="Đang chờ token đầu tiên")
        self._label(toolbar, variable=self.token_status, color=MUTED).pack(
            side="right", padx=(10, 0)
        )

        overview = tk.Frame(self, bg=CARD, padx=14, pady=10)
        overview.pack(fill="x", pady=(0, 10))
        self._label(overview, "Vòng token", bold=True).pack(side="left", padx=(0, 12))
        ring = tk.Frame(overview, bg=CARD)
        ring.pack(side="left")
        for index, node in enumerate(members):
            badge = tk.Label(ring, text=node, padx=16, pady=8)
            badge.grid(row=0, column=index * 2)
            self.nodes[node] = badge
            self._label(ring, " → " if index < len(members) - 1 else " ↻").grid(
                row=0, column=index * 2 + 1
            )

        inventory = tk.Frame(self, bg=CARD, padx=14, pady=10)
        inventory.pack(fill="x", pady=(0, 10))
        self._label(inventory, "Kho thiết bị · Chọn một thiết bị để thao tác",
                    bold=True).pack(anchor="w", pady=(0, 6))
        self.table = ttk.Treeview(
            inventory, columns=("id", "name", "status", "owner"), show="headings", height=3
        )
        for column, label, width in (
            ("id", "Mã", 90), ("name", "Thiết bị", 210),
            ("status", "Trạng thái", 130), ("owner", "Máy đang mượn", 140),
        ):
            self.table.heading(column, text=label)
            self.table.column(column, width=width)
        for device, name in DEVICES.items():
            self.table.insert("", "end", iid=device, values=(device, name, "—", "—"))
        self.table.pack(fill="x")
        self.table.selection_set(self.device.get())
        self.table.bind("<<TreeviewSelect>>", self._select_device)

        panel = tk.Frame(self, bg=PAGE)
        panel.pack(fill="x", pady=(0, 10))
        for index, node in enumerate(members):
            panel.columnconfigure(index, weight=1, uniform="nodes")
            card = tk.Frame(panel, bg=CARD)
            card.grid(row=0, column=index, sticky="nsew",
                      padx=(0, 8 if index < len(members) - 1 else 0))
            tk.Frame(card, height=4, bg=ACCENTS[index % len(ACCENTS)]).pack(fill="x")
            body = tk.Frame(card, bg=CARD, padx=12, pady=10)
            body.pack(fill="both", expand=True)
            self._label(body, f"Máy {node}", size=12, bold=True).pack(anchor="w")
            buttons = []
            for label, borrow, button_style in (
                ("Mượn", True, "Borrow.TButton"), ("Trả", False, "Return.TButton")
            ):
                button = ttk.Button(
                    body, text=label, style=button_style,
                    command=lambda node=node, borrow=borrow: self.request(
                        node, self.device.get(), borrow
                    ),
                )
                button.pack(fill="x", pady=(5, 0))
                buttons.append(button)
            self.controls[node] = buttons
            self._label(body, variable=self.status[node], color=MUTED,
                        wraplength=155).pack(anchor="w", pady=(8, 0))

        journal = tk.Frame(self, bg=CARD, padx=14, pady=10)
        journal.pack(fill="both", expand=True)
        self._label(journal, "Nhật ký token và thao tác", bold=True).pack(anchor="w")
        self.log = tk.Text(journal, height=6, state="disabled", wrap="word",
                           bg="#f6f8fc", fg=INK, relief="flat", padx=8, pady=6,
                           font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, pady=(4, 0))
        self._theme_widgets = list(self._collect_theme_widgets(self))
        self._apply_theme()

    def _collect_theme_widgets(self, parent):
        for widget in parent.winfo_children():
            if isinstance(widget, tk.Frame) and widget["bg"] in (PAGE, CARD):
                yield widget, widget["bg"], None
            elif isinstance(widget, tk.Label) and widget not in self.nodes.values():
                yield widget, CARD, widget["fg"]
            yield from self._collect_theme_widgets(widget)

    def toggle_theme(self):
        self._dark = not self._dark
        self._apply_theme()

    def _apply_theme(self):
        colors = {
            PAGE: "#0f172a", CARD: "#1e293b", INK: "#f1f5f9", MUTED: "#cbd5e1"
        } if self._dark else {}
        page, ink, muted = (colors.get(color, color) for color in (PAGE, INK, MUTED))
        field = "#111c30" if self._dark else "#f6f8fc"
        header = "#283952" if self._dark else "#e8eef7"
        selected = "#24477a" if self._dark else "#dbeafe"
        style = ttk.Style(self)
        style.configure("Page.TFrame", background=page)
        style.configure("Treeview", background=field, fieldbackground=field,
                        foreground=ink, rowheight=26, borderwidth=0)
        style.configure("Treeview.Heading", background=header, foreground=ink)
        style.map("Treeview", background=[("selected", selected)],
                  foreground=[("selected", ink)])
        for name, color in (("Borrow", "#2563eb"), ("Return", "#a65808"),
                            ("Batch", "#7c3aed"), ("Theme", header)):
            foreground = ink if name == "Theme" else "white"
            style.configure(f"{name}.TButton", background=color, foreground=foreground,
                            borderwidth=0, padding=(4, 2) if name == "Theme" else (10, 6))
            style.map(f"{name}.TButton",
                      background=[("disabled", header), ("active", "#344b6e")],
                      foreground=[("disabled", muted), ("active", "white")])
        for widget, background, foreground in self._theme_widgets:
            widget.configure(bg=colors.get(background, background))
            if foreground is not None:
                widget.configure(fg=colors.get(foreground, foreground))
        self.log.configure(bg=field, fg=ink, selectbackground=selected, selectforeground=ink)
        self.theme_button.configure(text="☀" if self._dark else "☾")
        self._highlight_token()

    def _highlight_token(self):
        idle_bg, idle_fg = ("#293a50", "#e2e8f0") if self._dark else ("#e8eeeb", "#192b24")
        for node, badge in self.nodes.items():
            active = node == self._last_target
            badge.configure(bg="#175c48" if active else idle_bg,
                            fg="white" if active else idle_fg)

    @staticmethod
    def _label(parent, text="", *, variable=None, color=INK, size=10, bold=False,
               wraplength=0):
        return tk.Label(parent, text=text, textvariable=variable, bg=CARD, fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"),
                        justify="left", wraplength=wraplength)

    def _select_device(self, _event):
        selected = self.table.selection()
        if selected:
            self.device.set(selected[0])

    def update_token(self, sender, target, token, state):
        """Gọi trên luồng Tk sau khi nút đích xử lý gói token."""
        self.token_status.set(f"Lượt vừa xử lý: {target}   •   Số thứ tự: {token['seq']}")
        self._last_target = target
        self._highlight_token()
        for device, name in DEVICES.items():
            entry = state[device]
            label = "Sẵn sàng" if entry["status"] == "AVAILABLE" else "Đang mượn"
            self.table.item(device, values=(device, name, label, entry["by"] or "—"))
        self.write_log(f"TOKEN #{token['seq']} đến {target} từ {sender}")

    def request(self, node, device, borrow):
        if self.controls[node][0].instate(("disabled",)):
            return
        label = "Mượn" if borrow else "Trả"
        self.status[node].set(f"Đang chờ token · {label} {device}")
        for button in self.controls[node]:
            button.state(("disabled",))
        result = self.submit(node, device, borrow)
        self.write_log(f"{node} gửi yêu cầu {label.lower()} {device}")
        # Tk chạy cùng luồng xử lý token trong bản demo.
        result.add_done_callback(
            lambda future: self.after_idle(self._show_result, node, label, device, future)
        )

    def _show_result(self, node, label, device, future):
        try:
            outcome = "Thành công" if future.result() else "Bị từ chối"
        except Exception:
            outcome = "Không xử lý được yêu cầu"
        self.status[node].set(f"{outcome} · {label} {device}")
        self.write_log(f"{node} · {outcome} · {label} {device}")
        for button in self.controls[node]:
            button.state(("!disabled",))

    def write_log(self, message):
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        if int(self.log.index("end-1c").split(".")[0]) > 200:
            self.log.delete("1.0", "2.0")
        self.log.see("end")
        self.log.configure(state="disabled")


def main():
    root = tk.Tk()
    root.title("Token Ring Lab · Mô phỏng 4 nút")
    root.geometry("1020x760")
    root.minsize(780, 710)
    demo = DemoRing()

    def batch(device, borrow):
        if any(view.controls[node][0].instate(("disabled",)) for node in MEMBERS):
            view.write_log("Chờ các yêu cầu hiện tại hoàn tất trước khi thao tác đồng loạt.")
            return
        for node in MEMBERS:
            view.request(node, device, borrow)

    view = RingView(root, MEMBERS, demo.submit, batch)
    view.pack(fill="both", expand=True)

    def tick():
        sender, target, token = demo.step()
        view.update_token(sender, target, token, demo.state)
        root.after(650, tick)

    tick()
    root.mainloop()


if __name__ == "__main__":
    main()
