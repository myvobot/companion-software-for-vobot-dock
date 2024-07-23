import os
import zipfile
import subprocess
import shutil
import sys
import platform
import tkinter as tk
from tkinter import filedialog, messagebox

def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

def get_mpy_cross_executable():
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    system = platform.system().lower()
    machine = platform.machine().lower()

    if system == "windows":
        return os.path.join(base_path, "mpy-cross", "mpy-cross-win.exe")
    elif system == "darwin":
        if machine == "x86_64":
            return os.path.join(base_path, "mpy-cross", "mpy-cross-mac-intel")
        elif machine == "arm64":
            return os.path.join(base_path, "mpy-cross", "mpy-cross-mac-arm")
        else:
            raise RuntimeError("Unsupported Mac architecture")
    elif system == "linux":
        if machine == "x86_64":
            return os.path.join(base_path, "mpy-cross", "mpy-cross-linux-x86_64")
        elif "arm" in machine:
            return os.path.join(base_path, "mpy-cross", "mpy-cross-linux-arm")
        else:
            raise RuntimeError("Unsupported Linux architecture")
    else:
        raise RuntimeError("Unsupported operating system")

def convert_py_to_mpy(src_folder, dst_folder, exclude_folder):
    mpy_cross_executable = get_mpy_cross_executable()

    for root, dirs, files in os.walk(src_folder):
        # Skip the temporary folder
        if exclude_folder in root:
            continue

        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(root, src_folder)
            output_dir = os.path.join(dst_folder, relative_path)
            if file.endswith('.py'):
                mpy_path = os.path.join(output_dir, file[:-3] + '.mpy')
                try:
                    # Ensure the output directory exists
                    os.makedirs(output_dir, exist_ok=True)

                    # Run the mpy-cross tool to convert
                    subprocess.run([mpy_cross_executable, file_path], check=True)

                    # Move the generated .mpy file to the target folder
                    original_mpy_path = file_path[:-3] + '.mpy'
                    if os.path.exists(original_mpy_path):
                        shutil.move(original_mpy_path, mpy_path)

                except subprocess.CalledProcessError as e:
                    messagebox.showerror("Error", f"Error converting {file_path}: {e}")
                    return False
            else:
                # Move non-.py files to the target folder
                os.makedirs(output_dir, exist_ok=True)
                shutil.copy(file_path, output_dir)
    return True


def main():
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    folder_path = filedialog.askdirectory(title="Select folder to bundle")
    if not folder_path:
        messagebox.showwarning("Warning", "No folder selected")
        return

    open_source = messagebox.askyesno("Open Source", "Allow code to be open source?")

    if not open_source:
        temp_folder = os.path.join(folder_path, 'temp_mpy')
        os.makedirs(temp_folder, exist_ok=True)
        if not convert_py_to_mpy(folder_path, temp_folder, temp_folder):
            shutil.rmtree(temp_folder)  # Clean up temporary folder
            return
        folder_path = temp_folder

    output_path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP files", "*.zip")], title="Save bundled file")
    if not output_path:
        messagebox.showwarning("Warning", "No save path selected")
        return

    try:
        zip_folder(folder_path, output_path)
        messagebox.showinfo("Success", f"Folder successfully bundled as {output_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Error during bundling: {e}")
    finally:
        if not open_source:
            shutil.rmtree(temp_folder)  # Clean up temporary folder

if __name__ == "__main__":
    main()
