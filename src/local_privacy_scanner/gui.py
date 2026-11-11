"""Small desktop interface for scanning folders locally."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .scanner import Finding, scan_directory


class ScannerWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Local Privacy Scanner")
        root.geometry("780x520")
        root.minsize(600, 380)

        self.folder = tk.StringVar()
        self.status = tk.StringVar(value="Choose a folder to scan.")
        self.results: queue.Queue[tuple[str, object]] = queue.Queue()
        self.scan_button: ttk.Button

        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Local Privacy Scanner", font=("TkDefaultFont", 16, "bold")).pack(anchor="w")
        ttk.Label(
            frame,
            text="Find possible personal data and credentials on this computer. Files stay local.",
            wraplength=740,
        ).pack(anchor="w", pady=(4, 14))

        folder_row = ttk.Frame(frame)
        folder_row.pack(fill="x")
        ttk.Entry(folder_row, textvariable=self.folder).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_row, text="Choose folder…", command=self.choose_folder).pack(side="left", padx=(8, 0))

        ttk.Label(frame, text="Exclude patterns (optional; one relative pattern per line):").pack(anchor="w", pady=(12, 4))
        self.exclusions = tk.Text(frame, height=3, wrap="none")
        self.exclusions.pack(fill="x")
        self.exclusions.insert("1.0", "build/**\n*.log")

        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=10)
        self.scan_button = ttk.Button(controls, text="Scan folder", command=self.start_scan)
        self.scan_button.pack(side="left")
        ttk.Label(controls, textvariable=self.status).pack(side="left", padx=12)

        columns = ("path", "line", "finding")
        self.table = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        self.table.heading("path", text="File")
        self.table.heading("line", text="Line")
        self.table.heading("finding", text="Possible finding")
        self.table.column("path", width=390, stretch=True)
        self.table.column("line", width=70, anchor="center", stretch=False)
        self.table.column("finding", width=240, stretch=True)
        self.table.pack(fill="both", expand=True)
        ttk.Label(
            frame,
            text="Matches are clues, not proof. A clean scan cannot guarantee that a folder has no sensitive data.",
            wraplength=740,
        ).pack(anchor="w", pady=(10, 0))

    def choose_folder(self) -> None:
        selected = filedialog.askdirectory(title="Choose a folder to scan")
        if selected:
            self.folder.set(selected)

    def start_scan(self) -> None:
        folder = self.folder.get().strip()
        if not folder:
            messagebox.showinfo("Choose a folder", "Choose a folder before starting a scan.")
            return
        patterns = tuple(line.strip() for line in self.exclusions.get("1.0", "end").splitlines() if line.strip())
        self.scan_button.configure(state="disabled")
        self.status.set("Scanning…")
        for item in self.table.get_children():
            self.table.delete(item)
        threading.Thread(target=self._scan_worker, args=(folder, patterns), daemon=True).start()
        self.root.after(100, self._poll_results)

    def _scan_worker(self, folder: str, patterns: tuple[str, ...]) -> None:
        try:
            findings = scan_directory(folder, exclude=patterns)
        except (OSError, ValueError) as error:
            self.results.put(("error", str(error)))
        else:
            self.results.put(("done", findings))

    def _poll_results(self) -> None:
        try:
            state, payload = self.results.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_results)
            return
        self.scan_button.configure(state="normal")
        if state == "error":
            self.status.set("Scan failed.")
            messagebox.showerror("Could not scan folder", str(payload))
            return
        findings = payload
        assert isinstance(findings, list)
        for finding in findings:
            assert isinstance(finding, Finding)
            self.table.insert("", "end", values=(finding.path.as_posix(), finding.line, finding.kind))
        self.status.set(f"Complete: {len(findings)} possible finding(s).")


def main() -> None:
    root = tk.Tk()
    ScannerWindow(root)
    root.mainloop()

