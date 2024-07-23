# computerMonitor

The Hardware Monitoring software communicates with the Vobot Mini Dock via UDP unicast mode to display received computer information.

## Directory Structure

- `main.py` - Entry point, includes the GUI
- `udp_server.py` - UDP broadcasting service
- `stats.py` - Abstracts hardware data retrieval across different operating systems
- `external/` - Contains external dependencies, such as LibreHardwareMonitor
- `sensors/` - Contains sensor-related code

## Installation

To install and run the Hardware Monitoring software, follow these steps:

1. Navigate to the `computerMonitor` directory:
    ```bash
    cd computerMonitor
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

With the virtual environment activated, start the Hardware Monitoring software:

```bash
python main.py
```

After starting the program, enter the IP address of the Mini Dock to begin broadcasting PC hardware information via UDP. The Vobot Mini Dock will receive and display this information.

## Packaging the Application

To package the Hardware Monitoring application into a standalone executable, follow these steps:

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
        pyi-makespec --noconsole -F main.py
        ```
    - This will generate a `main.spec` file. Modify the `main.spec` file as needed to include the required directories. Add the `datas` section in the `main.spec` file (refer to the [PyInstaller documentation](https://pyinstaller.org/en/stable/spec-files.html#using-spec-files) for details):
        ```bash
        datas=[
            ("./external/LibreHardwareMonitor", "external/LibreHardwareMonitor"),
            ("./sensors", "sensors")
        ]
        ```
    - After making the necessary modifications, run:
        ```bash
        pyinstaller main.spec
        ```

4. You can find the executable in the `computerMonitor/dist` directory.

### Notes

1. The executable files generated for different operating systems are different:
    - For example, an executable packaged on Ubuntu can only run on Ubuntu.
    - Therefore, you need to package the application on the respective operating systems to generate executables for different operating systems.