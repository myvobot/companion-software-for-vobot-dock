import os
import zipfile
import subprocess
import shutil
import sys
import platform
import tkinter as tk
from tkinter import filedialog, messagebox
import yaml
import webbrowser

required_fields = [
        'name', 'description', 'version',
        'minimum_version', 'compatible_devices'
    ]

def load_manifest(manifest_path):
    with open(manifest_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def should_include(file_path, include_paths, exclude_paths):
    # Check if it is in the include list
    if file_path.endswith(("manifest.yml", "manifest.py", "manifest.mpy")): return True
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
                if not include_paths or should_include(file_path, include_paths, exclude_paths):
                    print("------save------")
                    zipf.write(file_path, arcname)
                print(file_path)

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

def convert_yml_to_py(path, manifest):
    # Convert manifest.yml to manifest.py
    with open(path, 'w', encoding='utf-8') as file:
        for field in required_fields:
            if field in manifest.get('application', {}):
                value = manifest['application'][field]
                if type(value) is str: file.write(f"{field.upper()} = '{value}'\n")
                else: file.write(f"{field.upper()} = {value}\n")
            elif field in manifest.get('system_requirements', {}):
                value = manifest['system_requirements'][field]
                if type(value) is str: file.write(f"{field.upper()} = '{value}'\n")
                else: file.write(f"{field.upper()} = {value}\n")
        attributes = manifest.get('attributes', {})
        for key, value in attributes.items():
            if type(value) is str: file.write(f"{key.upper()} = '{value}'\n")
            else: file.write(f"{key.upper()} = {value}\n")

def manifest_import_init(path):
    # Import manifest.py in the __init__ file
    try:
        file_path = os.path.join(path, "__init__.py")
        with open(file_path, 'r+') as file:
            content = file.read()
            file.seek(0, 0)
            file.write('from . import manifest\n' + content)
    except:
       pass

def cleanup_manifest_files(folder_path):
    manifest_py_path = os.path.join(folder_path, 'manifest.py')
    if os.path.exists(manifest_py_path):
        os.remove(manifest_py_path)

    init_py_path = os.path.join(folder_path, '__init__.py')
    if os.path.exists(init_py_path):
        with open(init_py_path, 'r') as file:
            lines = file.readlines()

        lines = [line for line in lines if 'from . import manifest' not in line]

        with open(init_py_path, 'w') as file:
            file.writelines(lines)

def open_link(event):
    webbrowser.open_new(r"https://dock.myvobot.com/developer/guides/publishing-guide/manifest_file")

def show_custom_messagebox(message_text):
    custom_box = tk.Tk()
    custom_box.title("Warning")

    custom_box.geometry("300x150")
    custom_box.resizable(False, False)

    message = tk.Label(custom_box, text=message_text, wraplength=280)
    message.pack(pady=5)

    link = tk.Label(custom_box, text="Manifest.yml Requirements", fg="blue", cursor="hand2")
    link.pack(pady=4)
    link.bind("<Button-1>", open_link)

    button = tk.Button(custom_box, text="OK", command=custom_box.destroy)
    button.pack(pady=5)

    custom_box.update_idletasks()
    width = custom_box.winfo_width()
    height = custom_box.winfo_height()
    x = (custom_box.winfo_screenwidth() // 2) - (width // 2)
    y = (custom_box.winfo_screenheight() // 2) - (height // 2)
    custom_box.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    custom_box.mainloop()

def validate_manifest(manifest):
    for field in required_fields:
        if field not in manifest['application'] and field not in manifest['system_requirements']:
            return False, f"Missing required field: {field}.\nFor the content and required fields of manifest.yml, please visit: "
    return True, ""

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

    if not os.path.exists(manifest_path):
        show_custom_messagebox("Missing manifest.yml.\nFor the content and required fields of manifest.yml, please visit: ")
        return
    manifest_py_path = os.path.join(folder_path, 'manifest.py')
    manifest = load_manifest(manifest_path)
    is_valid, error_message = validate_manifest(manifest)
    if not is_valid:
        show_custom_messagebox(error_message)
        return
    convert_yml_to_py(manifest_py_path, manifest)
    manifest_import_init(folder_path)

    include_paths = exclude_paths = None

    temp_folder = os.path.join(folder_path, 'temp_mpy')
    os.makedirs(temp_folder, exist_ok=True)
    if not convert_py_to_mpy(folder_path, temp_folder, temp_folder):
        shutil.rmtree(temp_folder)  # Clean up temporary folder
        return
    folder_path = temp_folder
    try:
        if 'files' in manifest and 'include' in manifest['files']:
            include_paths = [os.path.normpath(os.path.join(folder_path, item)) for item in manifest['files'].get('include', [])]
            exclude_paths = [os.path.normpath(os.path.join(folder_path, item)) for item in manifest['files'].get('exclude', [])]
    except:
        include_paths = None
        exclude_paths = None

    output_path = filedialog.asksaveasfilename(defaultextension=".vbt", filetypes=[("VBT files", "*.vbt")], title="Save bundled file", initialfile=file_name + ".vbt")
    if not output_path:
        messagebox.showwarning("Warning", "No save path selected")
        shutil.rmtree(temp_folder)
        return

    try:
        zip_folder(file_name, folder_path, output_path, include_paths, exclude_paths)
        messagebox.showinfo("Success", f"Folder successfully bundled as {output_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Error during bundling: {e}")
    finally:
        shutil.rmtree(temp_folder)  # Clean up temporary folder
        cleanup_manifest_files(os.path.dirname(temp_folder))

if __name__ == "__main__":
    main()
