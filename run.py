"""Launch the vehicle sizing desktop workbench."""

import json
import os
from pathlib import Path
from queue import Empty, Queue
import subprocess
import tempfile
from threading import Thread
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from dynamics_export import build_dynamics_export
from project import FIELDS, PROJECT_FORMAT, SCHEMA, FieldError, default_project, read_project, validate_inputs
from vehicle_initial_sizing import solve
from vehicle_initial_sizing_report import build_report, render_csv_results


WEB = Path(__file__).resolve().with_name("web")
PROJECTS = WEB.parent / "projects"


def write_text(path, content, encoding="utf-8"):
    staging = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding=encoding, newline="",
                                         dir=path.parent, delete=False) as handle:
            staging = Path(handle.name)
            handle.write(content)
        staging.replace(path)
    finally:
        if staging is not None:
            staging.unlink(missing_ok=True)


class WorkbenchWindow(tk.Tk):
    def __init__(self):
        defaults = default_project()
        super().__init__()
        self.title("Vehicle Initial Sizing Lab · 車輛初步設計")
        self.geometry("1380x860")
        self.minsize(960, 620)
        self.markdown = ""
        self.snapshot = None
        self.inputs = {}
        self.project_path = None
        self.saved_inputs = {}
        self.loading_inputs = False
        self.busy = False
        self.ready = False
        self.closing = False
        self.host = None
        self.events = Queue()
        self.status = tk.StringVar(value="正在載入報告檢視器…")
        self.protocol("WM_DELETE_WINDOW", self.close)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font=("Microsoft JhengHei UI", 10))
        style.configure("TFrame", background="#f1f5f9")
        style.configure("TLabel", background="#f1f5f9")
        style.configure("TNotebook.Tab", padding=(12, 8))
        style.configure("TButton", padding=(7, 4))
        self.configure(background="#f1f5f9")

        header = ttk.Frame(self, padding=(14, 10))
        header.pack(fill="x")
        ttk.Label(header, text="Vehicle Initial Sizing Lab", foreground="#0f172a",
                  font=("Segoe UI", 18, "bold")).pack(side="left")
        ttk.Label(header, text="車輛初步設計與估算", padding=(14, 0)).pack(side="left")
        toolbar = ttk.Frame(self, padding=(12, 0, 12, 8))
        toolbar.pack(fill="x")
        for label, command in (
            ("新增專案", self.new_project),
            ("匯入", self.open_project),
            ("儲存", self.save_project),
            ("另存", lambda: self.save_project(as_new=True)),
        ):
            ttk.Button(toolbar, text=label, command=command).pack(side="left", padx=3)
        footer = ttk.Frame(self, padding=(12, 6))
        footer.pack(side="bottom", fill="x")
        self.save_button = ttk.Button(footer, text="儲存 Markdown", command=self.save_markdown, state="disabled")
        self.save_button.pack(side="right")
        self.csv_button = ttk.Button(footer, text="匯出 CSV", command=self.save_csv, state="disabled")
        self.csv_button.pack(side="right", padx=(0, 6))
        self.dynamics_button = ttk.Button(
            footer, text="匯出json", command=self.save_dynamics, state="disabled")
        self.dynamics_button.pack(side="right", padx=(0, 6))
        ttk.Label(footer, textvariable=self.status).pack(side="left", fill="x", expand=True)

        split = ttk.Panedwindow(self, orient="horizontal")
        split.pack(fill="both", expand=True, padx=12)
        left = ttk.Frame(split, padding=6, width=360)
        right = ttk.Frame(split, padding=6)
        split.add(left, weight=0)
        split.add(right, weight=1)

        ttk.Label(left, text="車輛參數").pack(anchor="w", pady=(0, 4))
        self.solve_button = ttk.Button(left, text="求解　F5", command=self.calculate, state="disabled")
        self.solve_button.pack(fill="x", pady=(0, 6))
        self.groups = ttk.Notebook(left)
        self.groups.pack(fill="both", expand=True)
        for group in SCHEMA:
            self.add_group(group)

        result_tools = ttk.Frame(right)
        result_tools.pack(fill="x", pady=(0, 6))
        ttk.Label(result_tools, text="跳至章節").pack(side="left", padx=(0, 8))
        self.chapters = ttk.Combobox(result_tools, state="disabled")
        self.chapters.pack(side="left", fill="x", expand=True)
        self.chapters.bind("<<ComboboxSelected>>", self.jump_chapter)
        tabs = ttk.Notebook(right)
        tabs.pack(fill="both", expand=True)
        self.report_frame = tk.Frame(tabs, background="white", highlightthickness=0)
        tabs.add(self.report_frame, text="求解報告")

        self.bind("<F5>", lambda event: self.calculate())
        self.bind("<Control-Return>", lambda event: self.calculate())
        self.bind("<Control-o>", lambda event: self.open_project())
        self.bind("<Control-s>", lambda event: self.save_project())
        self.apply_project(defaults, None)
        self.resize_timer = None
        self.bind("<Configure>", self.schedule_resize)
        self.after_idle(self.start_preview)

    def add_group(self, group):
        page = ttk.Frame(self.groups)
        self.groups.add(page, text=group["tab"])
        self.groups.tab(page, padding=3)
        canvas = tk.Canvas(page, width=350, background="#f1f5f9", highlightthickness=0)
        scroll = ttk.Scrollbar(page, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = ttk.Frame(canvas, padding=8)
        item = canvas.create_window(0, 0, window=content, anchor="nw")
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(item, width=event.width))
        content.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox(item)))
        content.columnconfigure(1, weight=1)
        ttk.Label(content, text=group["title"], font=("Microsoft JhengHei UI", 10, "bold")).grid(
            row=0, columnspan=2, sticky="w", pady=(0, 6))
        fields = [field for field in group["fields"] if field["name"] != "brake_ax"]
        for row, field in enumerate(fields, start=1):
            label = f"{field['label']} ({field['unit']})" if field["unit"] else field["label"]
            ttk.Label(content, text=label, wraplength=172).grid(row=row, column=0, sticky="w", padx=(0, 6), pady=3)
            if field["kind"] == "checkbox":
                variable = tk.BooleanVar(self)
                widget = ttk.Checkbutton(content, variable=variable)
            else:
                variable = tk.StringVar(self)
                widget = ttk.Entry(content, textvariable=variable, width=14, justify="right")
            widget.grid(row=row, column=1, sticky="ew", pady=3)
            variable.trace_add("write", self.mark_pending)
            self.inputs[field["name"]] = (variable, widget, page)
            if field.get("hint"):
                ttk.Label(content, text=field["hint"], foreground="#475569").grid(
                    row=len(fields) + 1, columnspan=2, sticky="w", pady=(6, 0))

        def wheel(event):
            if str(event.widget).startswith(str(page) + "."):
                canvas.yview_scroll(-int(event.delta / 120), "units")
        page.bind_all("<MouseWheel>", wheel, add="+")

    def start_preview(self):
        executable = WEB.parent / "build" / "webview2" / "ReportHost.exe"
        if not executable.is_file():
            self.preview_failed("請先執行 Build-WebView2Host.ps1。")
            return
        profile = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "VehicleInitialSizingLab" / "WebView2"
        try:
            self.host = subprocess.Popen(
                [str(executable), str(self.report_frame.winfo_id()), str(WEB), str(profile)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except OSError as error:
            self.preview_failed(str(error))
            return
        Thread(target=self.read_preview, args=(self.host,), daemon=True).start()
        self.after(30, self.poll_preview)

    def read_preview(self, host):
        detail = ""
        with host.stdout:
            for line in host.stdout:
                try:
                    self.events.put(json.loads(line))
                except ValueError:
                    if not detail and line.strip():
                        detail = line.strip()
        self.events.put({"event": "closed", "detail": detail})

    def poll_preview(self):
        if self.closing:
            return
        try:
            while True:
                message = self.events.get_nowait()
                event = message.get("event")
                if event == "ready":
                    self.ready = True
                    self.solve_button.state(["!disabled"])
                    self.status.set("就緒 · 設定參數後按 F5 求解。")
                    self.send("resize")
                elif event == "rendered":
                    self.report_rendered(message)
                elif event == "solve":
                    self.calculate()
                elif event == "save":
                    self.save_project()
                elif event == "open":
                    self.open_project()
                elif event == "closed":
                    self.preview_failed(message["detail"])
                    return
        except Empty:
            self.after(30, self.poll_preview)

    def preview_failed(self, detail):
        self.ready = self.busy = False
        self.solve_button.state(["disabled"])
        self.chapters.configure(state="disabled")
        if self.markdown:
            self.save_button.state(["!disabled"])
            self.csv_button.state(["!disabled"])
            self.dynamics_button.state(["!disabled"])
        self.status.set("無法載入 WebView2 報告檢視器。 " + detail)

    def send(self, message):
        if not self.host or not self.ready:
            return
        payload = message if isinstance(message, str) else json.dumps(message, ensure_ascii=False)
        try:
            self.host.stdin.write(payload + "\n")
            self.host.stdin.flush()
        except OSError:
            self.preview_failed("檢視器已關閉。")

    def schedule_resize(self, event):
        if event.widget not in (self, self.report_frame) or not self.ready:
            return
        if self.resize_timer is not None:
            self.after_cancel(self.resize_timer)
        self.resize_timer = self.after(25, self.resize_preview)

    def resize_preview(self):
        self.resize_timer = None
        self.send("resize")

    def jump_chapter(self, event=None):
        self.send({"event": "chapter", "index": self.chapters.current()})

    def mark_pending(self, *_):
        if self.loading_inputs:
            return
        self.update_title()
        if self.markdown and not self.busy:
            self.status.set("參數已變更 · 右側顯示上次求解結果。")

    def load_defaults(self):
        try:
            return default_project()
        except (OSError, ValueError, ArithmeticError) as error:
            messagebox.showwarning("無法載入預設參數", str(error), parent=self)
            return None

    def input_snapshot(self):
        return {name: variable.get() for name, (variable, _, _) in self.inputs.items()}

    def update_title(self):
        marker = "* " if self.input_snapshot() != self.saved_inputs else ""
        name = self.project_path.stem if self.project_path else "未命名專案"
        self.title(f"{marker}{name} · Vehicle Initial Sizing Lab")

    def set_inputs(self, values):
        self.loading_inputs = True
        try:
            for name, (variable, _, _) in self.inputs.items():
                value = values[name]
                variable.set("" if value is None else value)
        finally:
            self.loading_inputs = False

    def apply_project(self, values, path):
        self.set_inputs(values)
        # Keep explicit braking targets from imported projects. None uses ax.
        self.brake_ax = values["brake_ax"]
        self.project_path = path
        self.saved_inputs = self.input_snapshot()
        self.update_title()
        self.markdown = ""
        self.snapshot = None
        self.save_button.state(["disabled"])
        self.csv_button.state(["disabled"])
        self.dynamics_button.state(["disabled"])
        self.chapters.configure(values=(), state="disabled")
        self.chapters.set("")
        self.send({"event": "clear"})

    def discard_ok(self):
        if self.input_snapshot() == self.saved_inputs:
            return True
        choice = messagebox.askyesnocancel("未儲存的專案", "要先儲存目前的車輛參數嗎？", parent=self)
        return self.save_project() if choice is True else choice is False

    def new_project(self):
        if not self.busy and self.discard_ok():
            defaults = self.load_defaults()
            if defaults is not None:
                self.apply_project(defaults, None)
                self.status.set("已新增專案 · 設定參數後按 F5 求解。")

    def open_project(self):
        if self.busy:
            return
        filename = filedialog.askopenfilename(
            parent=self, title="開啟車輛參數專案",
            initialdir=self.project_path.parent if self.project_path else (
                PROJECTS if PROJECTS.is_dir() else WEB.parent),
            filetypes=[("車輛參數專案", "*.json")],
        )
        if not filename:
            return
        path = Path(filename)
        try:
            values = read_project(path)
        except (ValueError, OSError, ArithmeticError) as error:
            messagebox.showwarning("開啟失敗", str(error), parent=self)
            return
        if self.discard_ok():
            self.apply_project(values, path)
            self.status.set(f"已開啟專案 · {path.name}")

    def save_project(self, as_new=False):
        try:
            values = validate_inputs(self.values())
            path = self.project_path
            if path is None or as_new:
                if path is None:
                    PROJECTS.mkdir(exist_ok=True)
                filename = filedialog.asksaveasfilename(
                    parent=self, title="儲存車輛參數專案",
                    initialdir=path.parent if path else PROJECTS,
                    initialfile=path.name if path else "vehicle_project.json",
                    defaultextension=".json", filetypes=[("車輛參數專案", "*.json")],
                )
                if not filename:
                    return False
                path = Path(filename)
            payload = {"application": PROJECT_FORMAT, "schema_version": 1, "parameters": values}
            write_text(path, json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        except (OSError, ValueError, ArithmeticError) as error:
            messagebox.showwarning("專案儲存失敗", str(error), parent=self)
            return False
        self.project_path = path
        self.saved_inputs = self.input_snapshot()
        self.update_title()
        self.status.set(f"已儲存專案 · {path.name}")
        return True

    def values(self):
        values = {"brake_ax": self.brake_ax}
        for name in FIELDS:
            if name == "brake_ax":
                continue
            variable, _, _ = self.inputs[name]
            value = variable.get()
            if isinstance(variable, tk.BooleanVar):
                values[name] = value
                continue
            text = value.strip()
            try:
                values[name] = float(text)
            except ValueError as error:
                raise FieldError(FIELDS[name], "須填入有限數值。") from error
        return values

    def calculate(self):
        if not self.ready or self.busy:
            return
        try:
            snapshot = solve(**self.values())
            result = build_report(snapshot)
        except (ValueError, ArithmeticError) as error:
            if isinstance(error, FieldError):
                _, widget, page = self.inputs[error.field]
                self.groups.select(page)
                widget.focus_set()
            self.status.set(str(error))
            messagebox.showwarning("求解未完成", str(error), parent=self)
            return
        self.busy = True
        self.solve_button.state(["disabled"])
        self.save_button.state(["disabled"])
        self.csv_button.state(["disabled"])
        self.dynamics_button.state(["disabled"])
        self.chapters.configure(state="disabled")
        self.markdown = result["markdown"]
        self.snapshot = snapshot
        self.status.set("正在排版報告…")
        self.send({"event": "render", "report": result})

    def report_rendered(self, message):
        self.busy = False
        self.solve_button.state(["!disabled"])
        self.save_button.state(["!disabled"])
        self.csv_button.state(["!disabled"])
        self.dynamics_button.state(["!disabled"])
        chapters = message["chapters"]
        self.chapters.configure(values=chapters, state="readonly" if chapters else "disabled")
        if chapters:
            self.chapters.current(0)
        else:
            self.chapters.set("")
        self.status.set("求解完成 · 顯示本次報告。" if message["ok"] else "報告排版遇到錯誤，可儲存 Markdown。")

    def save_markdown(self):
        if not self.markdown or self.busy:
            return
        filename = filedialog.asksaveasfilename(
            parent=self, title="儲存 Markdown 報告", initialfile="vehicle_initial_sizing_report.md",
            defaultextension=".md", filetypes=[("Markdown", "*.md")],
        )
        if not filename:
            return
        path = Path(filename)
        try:
            write_text(path, self.markdown)
        except OSError as error:
            messagebox.showwarning("儲存失敗", str(error), parent=self)
        else:
            self.status.set(f"已儲存 · {path.name}")

    def save_csv(self):
        if self.snapshot is None or self.busy:
            return
        filename = filedialog.asksaveasfilename(
            parent=self, title="匯出車輛估算資料", initialfile="vehicle_initial_sizing_results.csv",
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
        )
        if not filename:
            return
        path = Path(filename)
        try:
            write_text(path, render_csv_results(self.snapshot), encoding="utf-8-sig")
        except OSError as error:
            messagebox.showwarning("匯出失敗", str(error), parent=self)
        else:
            self.status.set(f"已匯出 CSV · {path.name}")

    def save_dynamics(self):
        if self.snapshot is None or self.busy:
            return
        name = self.project_path.stem if self.project_path else "車輛初步設計"
        try:
            project = build_dynamics_export(self.snapshot, name)
        except (OSError, ValueError, ArithmeticError) as error:
            messagebox.showwarning("JSON 匯出失敗", str(error), parent=self)
            return
        filename = filedialog.asksaveasfilename(
            parent=self, title="匯出json",
            initialdir=self.project_path.parent if self.project_path else WEB.parent,
            initialfile="Vehicle_initial_settings.json",
            defaultextension=".json", filetypes=[("JSON", "*.json")],
        )
        if not filename:
            return
        path = Path(filename)
        if self.project_path is not None and path.resolve() == self.project_path.resolve():
            messagebox.showwarning("JSON 匯出失敗", "請選擇與目前參數專案不同的檔名。", parent=self)
            return
        try:
            write_text(path, json.dumps(project, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        except (OSError, ValueError) as error:
            messagebox.showwarning("JSON 匯出失敗", str(error), parent=self)
        else:
            self.status.set(f"已匯出 JSON · {path.name}")

    def close(self):
        if self.closing or not self.discard_ok():
            return
        self.closing = True
        self.ready = False
        if self.host:
            self.host.stdin.close()
            self.finish_close(100)
        else:
            self.destroy()

    def finish_close(self, attempts):
        if self.host.poll() is not None:
            self.destroy()
        elif attempts:
            self.after(30, self.finish_close, attempts - 1)
        else:
            self.host.terminate()
            self.destroy()


def main():
    try:
        window = WorkbenchWindow()
    except (OSError, ValueError, ArithmeticError) as error:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("無法載入 default_project.json", str(error), parent=root)
        root.destroy()
        return
    window.mainloop()


if __name__ == "__main__":
    main()
