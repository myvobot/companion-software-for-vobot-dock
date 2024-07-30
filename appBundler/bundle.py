import os
import zipfile
import subprocess
import shutil
import sys
import platform
import tkinter as tk
from tkinter import filedialog, messagebox
import yaml

def load_manifest(manifest_path):
    with open(manifest_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def should_include(file_path, include_paths, exclude_paths):
    # Check if it is in the include list
    for include in include_paths:
        if file_path.startswith(include[:-3] if include.endswith(".py") else include):
            # Check if it is in the exclude list
            for exclude in exclude_paths:
                if file_path.startswith(exclude[:-3] if exclude.endswith(".py") else exclude):
                    return False
            return True
    return False

def zip_folder(file_name, folder_path, output_path, include_paths=None, exclude_paths=None):
    parent_folder = file_name
    folder_path = os.path.abspath(folder_path)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join(parent_folder, os.path.relpath(file_path, folder_path))
                print(file_path)
                if include_paths is None or should_include(file_path, include_paths, exclude_paths):
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
    root.lift()  # Bring the window to the front
    root.attributes('-topmost', True)  # Make the window topmost
    root.after_idle(root.attributes, '-topmost', False)  # Disable topmost after it is brought to the front

    folder_path = filedialog.askdirectory(title="Select folder to bundle")
    file_name = os.path.basename(folder_path)
    if not folder_path:
        messagebox.showwarning("Warning", "No folder selected")
        return

    init_py_path = os.path.join(folder_path, '__init__.py')
    init_mpy_path = os.path.join(folder_path, '__init__.mpy')
    # Check required documents
    if not (os.path.exists(init_py_path) or os.path.exists(init_mpy_path)):
        messagebox.showwarning("Warning", "Missing required file __init__.py")
        return

    manifest_path = os.path.join(folder_path, 'manifest.yml')
    include_paths = exclude_paths = None

    open_source = messagebox.askyesno("Open Source", "Allow code to be open source?")

    if not open_source:
        temp_folder = os.path.join(folder_path, 'temp_mpy')
        os.makedirs(temp_folder, exist_ok=True)
        if not convert_py_to_mpy(folder_path, temp_folder, temp_folder):
            shutil.rmtree(temp_folder)  # Clean up temporary folder
            return
        folder_path = temp_folder

    if os.path.exists(manifest_path):
        manifest = load_manifest(manifest_path).get("manifest",{})
        include_paths = [os.path.join(folder_path, item['path']) for item in manifest.get('include', [])]
        exclude_paths = [os.path.join(folder_path, item['path']) for item in manifest.get('exclude', [])]

    output_path = filedialog.asksaveasfilename(defaultextension=".vbt", filetypes=[("VBT files", "*.vbt")], title="Save bundled file", initialfile=file_name + ".vbt")
    if not output_path:
        messagebox.showwarning("Warning", "No save path selected")
        if not open_source: shutil.rmtree(temp_folder)
        return

    try:
        zip_folder(file_name, folder_path, output_path, include_paths, exclude_paths)
        messagebox.showinfo("Success", f"Folder successfully bundled as {output_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Error during bundling: {e}")
    finally:
        if not open_source:
            shutil.rmtree(temp_folder)  # Clean up temporary folder

if __name__ == "__main__":
    main()
