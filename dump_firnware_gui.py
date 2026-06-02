#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys

import dump_firmware

class H18DumperGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("H18 / Binqi H18 Firmware Dumper")
        self.root.geometry("600x500")
        self.root.resizable(True, True)

        self.create_widgets()

    def create_widgets(self):
        # Title
        tk.Label(self.root, text="Alltheway H18 / Binqi H18 Firmware Dumper", 
                font=("Arial", 16, "bold")).pack(pady=10)

        # Status
        self.status = tk.StringVar(value="Ready - Connect device in Recovery mode")
        tk.Label(self.root, textvariable=self.status, fg="blue").pack(pady=5)

        # Options frame
        frame = ttk.LabelFrame(self.root, text="Options", padding=10)
        frame.pack(fill="x", padx=20, pady=10)

        # Output folder
        tk.Label(frame, text="Output Folder:").grid(row=0, column=0, sticky="w")
        self.folder_var = tk.StringVar(value=os.getcwd())
        tk.Entry(frame, textvariable=self.folder_var, width=50).grid(row=0, column=1, padx=5)
        tk.Button(frame, text="Browse", command=self.browse_folder).grid(row=0, column=2)

        # Partitions
        tk.Label(frame, text="Partitions to dump:").grid(row=1, column=0, sticky="w", pady=5)
        self.partitions_var = tk.StringVar(value="boot,recovery,system,vendor")
        tk.Entry(frame, textvariable=self.partitions_var, width=50).grid(row=1, column=1, columnspan=2, padx=5, sticky="ew")

        # Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="CHECK DEVICE", bg="#4CAF50", fg="white", 
                 command=self.check_device, width=15).grid(row=0, column=0, padx=5)
        
        tk.Button(btn_frame, text="START DUMP", bg="#2196F3", fg="white", 
                 command=self.start_dump, width=15, height=2).grid(row=0, column=1, padx=5)

        tk.Button(btn_frame, text="EXIT", bg="#f44336", fg="white", 
                 command=self.root.quit, width=15).grid(row=0, column=2, padx=5)

        # Log box
        tk.Label(self.root, text="Log:").pack(anchor="w", padx=20)
        self.log = tk.Text(self.root, height=12, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, padx=20, pady=5)

    def log_message(self, msg, color="white"):
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.root.update()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)

    def check_device(self):
        self.log_message("Checking ADB device...")
        devices = dump_firmware.list_connected_devices()
        if not devices:
            self.log_message("❌ No device detected. Connect in Recovery mode.", "red")
            self.status.set("No device detected")
            return

        self.log_message(f"✅ Device detected: {', '.join(devices)}", "green")
        available_partitions = dump_firmware.discover_partition_paths()
        if available_partitions:
            preferred = [part for part in dump_firmware.DEFAULT_PARTITIONS if part in available_partitions]
            if preferred:
                self.partitions_var.set(",".join(preferred))
            self.log_message(
                f"Available partitions: {', '.join(sorted(available_partitions))}",
                "green",
            )
        else:
            self.log_message("⚠️  Could not read partition directories from the device.", "orange")
        self.status.set("Device OK - Ready to dump")

    def start_dump(self):
        partitions = [p.strip() for p in self.partitions_var.get().split(",") if p.strip()]
        if not partitions:
            messagebox.showerror("Error", "Enter at least one partition to dump.")
            return

        dump_dir, success_count = dump_firmware.dump_partitions(
            partitions,
            self.folder_var.get(),
            log=self.log_message,
        )
        if dump_dir is None:
            messagebox.showerror("Error", "Could not read partitions from the connected device.")
            return

        self.log_message(f"\n✅ Done! {success_count}/{len(partitions)} partitions dumped.")
        messagebox.showinfo("Complete", f"Dump finished!\n{success_count} partitions saved.\n\nCheck: {dump_dir}")

if __name__ == "__main__":
    if not dump_firmware.adb_available():
        messagebox.showerror("Error", "ADB not found in PATH!")
        sys.exit(1)
    
    app = H18DumperGUI()
    app.root.mainloop()
