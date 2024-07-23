# appBundler

The Application Bundler tool helps users package their applications into `.vbt` compressed files, with options to control whether the source code is open.

## Directory Structure

- `bundle.py` - Main script for bundling applications
- `mpy-cross/` - Contains the MicroPython cross-compiler programs

## Installation

To install and run the Application Bundler tool, follow these steps:

1. Navigate to the `appBundler` directory:
    ```bash
    cd appBundler
    ```

2. Set up and use a virtual environment:
    ```bash
    python3 -m venv env
    source env/bin/activate
    ```
    > `env` is the name of the virtual environment. Installing third-party libraries in the virtual environment ensures that only the necessary libraries are included.

3. Install the required Python packages using pip:
    ```bash
    pip3 install -r requirements.txt
    ```

## Usage

With the virtual environment activated, start the bundling process:

```bash
python bundle.py
```

This will launch an interactive UI where you can select the folder to be bundled and choose whether to make the source code open. The tool will then bundle the selected folder into a .vbt file.

## Packaging the Application

To package the Application Bundler tool into a standalone executable, follow these steps:

1. Ensure the virtual environment is activated:
    ```bash
    source env/bin/activate
    ```

2. Install PyInstaller:
    ```bash
    pip3 install pyinstaller
    ```

3. Use a spec file to package files from multiple directories:
    - Generate the spec file:
        ```bash
        pyi-makespec --noconsole -F bundle.py
        ```
    - This will generate a `bundle.spec` file. Modify the `bundle.spec` file as needed to include the required directories. Add the `datas` section in the `bundle.spec` file (refer to the [PyInstaller documentation](https://pyinstaller.org/en/stable/spec-files.html#using-spec-files) for details):
        ```python
        datas=[
            ('./mpy-cross/mpy-cross-win.exe', 'mpy-cross'),
            ('./mpy-cross/mpy-cross-mac-intel', 'mpy-cross'),
            ('./mpy-cross/mpy-cross-mac-arm', 'mpy-cross'),
            ('./mpy-cross/mpy-cross-linux-x86_64', 'mpy-cross'),
            ('./mpy-cross/mpy-cross-linux-arm', 'mpy-cross')
        ]
        ```
    - After making the necessary modifications, run:
        ```bash
        pyinstaller bundle.spec
        ```

4. You can find the executable in the `appBundler/dist` directory.

## Notes

1. Ensure that the source directory contains all necessary files for the application to run.
2. The output .vbt file can be distributed and used to deploy the application.
3. The bundling tool will check for a manifest.yml file in the selected folder to determine which files and folders to include. If manifest.yml is not present, the tool will default to bundling all files and folders, including __init__.py.

## Contributing

If you have any suggestions or improvements, please submit a Pull Request or create an Issue.
