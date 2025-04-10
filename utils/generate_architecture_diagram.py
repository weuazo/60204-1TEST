import os

# Ensure Graphviz executables are in the PATH
os.environ["PATH"] += os.pathsep + "C:\\Program Files\\Graphviz\\bin"

from graphviz import Digraph

def generate_architecture_diagram(output_path="architecture_diagram"):
    """Generate an architecture diagram for the project."""
    dot = Digraph(comment="Gemini Report Generator Architecture")

    # Main components
    dot.node("Main", "Main Entry Point")
    dot.node("UI", "User Interface")
    dot.node("Logic", "Core Logic")
    dot.node("Matchers", "Matching Algorithms")
    dot.node("Parsers", "File Parsers")
    dot.node("Plugins", "Plugin System")
    dot.node("Utils", "Utility Modules")
    dot.node("API", "API Integrations")

    # Relationships
    dot.edges([
        ("Main", "UI"),
        ("Main", "Logic"),
        ("Logic", "Matchers"),
        ("Logic", "Parsers"),
        ("Logic", "Plugins"),
        ("Logic", "Utils"),
        ("Logic", "API"),
        ("UI", "Plugins"),
        ("UI", "Utils"),
    ])

    # Render diagram
    dot.render(output_path, format="png", cleanup=True)
    print(f"Architecture diagram saved to {output_path}.png")

if __name__ == "__main__":
    generate_architecture_diagram()