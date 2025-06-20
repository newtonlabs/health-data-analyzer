"""Setup script for health data analyzer."""
from setuptools import setup, find_packages

setup(
    name="health-data-analyzer",
    version="0.1.0",
    description="Analyze and report on health data from various sources",
    author="Thomas Newton",
    packages=find_packages(),
    python_requires='>=3.9',  # For type hints and dict unions
    install_requires=[
        'requests>=2.31.0',  # For API calls
        'pandas>=2.1.4',     # For data analysis
        'python-dotenv>=1.0.0',  # For environment variables
        'msal>=1.24.1',      # For Microsoft auth
        'markdown>=3.5.2',   # For markdown to HTML conversion
        'weasyprint>=60.1',  # For HTML to PDF conversion
        'jinja2>=3.1.2',     # For HTML templating
        'setuptools>=69.0.2' # For package management
    ],
    extras_require={
        'dev': [
            'pylint>=3.0.0',  # For code quality
            'black>=23.10.0',  # For code formatting
            'mypy>=1.6.0'     # For type checking
        ]
    }
)
