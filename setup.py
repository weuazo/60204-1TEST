from setuptools import setup, find_packages

setup(
    name="gemini_report_generator",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for generating intelligent reports using AI",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-repo/gemini_report_generator",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pandas",
        "openpyxl",
        "PyPDF2",
        "python-docx",
        "tkinterdnd2",
        "difflib",
    ],
    entry_points={
        "console_scripts": [
            "gemini-report=main:main",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)