# Gemini Report Generator

Gemini Report Generator is a tool for generating intelligent reports using AI. It supports various document formats and provides advanced matching and analysis capabilities.

## Features
- AI-based document matching
- Flexible and exact matching modes
- Automatic standard detection
- User-friendly UI with theme support
- Feedback system for user input

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/gemini_report_generator.git
   ```

2. Navigate to the project directory:
   ```bash
   cd gemini_report_generator/project2
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python main.py
   ```

## Creating an Executable
To create a standalone executable:
```bash
pyinstaller --onefile --name gemini_report main.py
```
The executable will be located in the `dist/` directory.

## Usage
1. Launch the application.
2. Use the tabs to navigate between features:
   - **Report Generation**: Create intelligent reports.
   - **AI Chat**: Interact with AI for assistance.
   - **Prompt Management**: Manage prompts for AI interactions.
   - **Help**: Access user guides and documentation.

## Plugin System

The Gemini Report Generator supports a plugin system to extend its functionality. Plugins are Python scripts located in the `plugins/` directory.

### How to Create a Plugin
1. Create a new Python file in the `plugins/` directory (e.g., `my_plugin.py`).
2. Define a `run` function in the file. This function will be executed when the plugin is loaded.

Example:
```python
# plugins/my_plugin.py
def run():
    print("My custom plugin is running!")
```

### How to Use Plugins
1. Place your plugin file in the `plugins/` directory.
2. Run the application. The plugin loader will automatically detect and load the plugin.
3. If the plugin has a `run` function, it will be executed.

### Sample Plugin
A sample plugin (`sample_plugin.py`) is included in the `plugins/` directory. It demonstrates the basic structure of a plugin.

---

## Project Structure

```
project2/
├── api/                # API integration modules
├── data/               # Data files and resources
├── logic/              # Core logic for report generation
├── matcher/            # Matching algorithms
├── parsers/            # File parsers (Excel, PDF, Word)
├── plugins/            # Plugin directory
├── prompts/            # Prompt templates for AI
├── tests/              # Unit tests
├── ui/                 # User interface modules
├── utils/              # Utility modules
├── main.py             # Main entry point
├── setup.py            # Packaging configuration
└── README.md           # Project documentation
```

This structure ensures modularity and ease of maintenance.

## Testing
Run the test suite to ensure functionality:
```bash
python -m unittest discover tests
```

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
