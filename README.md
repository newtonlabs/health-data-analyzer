# Health Data Analyzer

A Python application that aggregates and analyzes health data from multiple sources:
- Whoop
- Oura

The application processes the data, generates visually rich reports with charts, and optionally stores results in OneDrive.

## Command Line Options

The application supports several command line flags for different operation modes. Use the `tracker` script which properly sets up all required environment variables:

```bash
# Generate data and reports
./tracker --fetch                       # Fetch yesterday's data and generate report
./tracker --fetch --date 2025-06-15     # Fetch data for specific date

# Convert markdown to PDF
./tracker --pdf                         # Convert yesterday's report to PDF
./tracker --pdf --date 2025-06-15       # Convert specific date's report to PDF

# Upload to OneDrive
./tracker --upload                      # Upload yesterday's files to OneDrive
./tracker --upload --date 2025-06-15    # Upload specific date's files

# Combine operations
./tracker --fetch --pdf                 # Fetch data, generate report, and convert to PDF
./tracker --fetch --pdf --upload        # Complete pipeline: fetch, generate, convert, and upload

# Enable debug mode for verbose logging
./tracker --fetch --debug               # Run with detailed logging

# Show help
./tracker                               # Show command line options
```

The application supports three main operations that can be combined:
1. **Fetch & Generate (`--fetch`)**: Fetch data from APIs and generate reports (CSV, markdown)
2. **Convert (`--pdf`)**: Convert existing markdown report to PDF with charts
3. **Upload (`--upload`)**: Upload existing files to OneDrive

Additional options:
- **Debug Mode (`--debug`)**: Enable verbose logging for troubleshooting
- **Date Selection (`--date YYYY-MM-DD`)**: Process a specific date instead of yesterday

If no command is provided, the application will show the help message with available options.

Files are organized in the `data` directory by date (YYYY-MM-DD) and when uploaded to OneDrive, they are stored under `Health Data/YYYY-MM-DD/` folders.

## Dependencies

### Python Dependencies
The project requires Python 3.9 or higher and several packages:
- `requests`: For API calls
- `pandas`: For data analysis
- `python-dotenv`: For environment variables
- `msal`: For Microsoft authentication
- `tabulate`: For markdown tables
- `weasyprint`: For PDF generation

### System Dependencies
On macOS, you'll need several system libraries for PDF generation with WeasyPrint:

```bash
# Install Pango and its dependencies
brew install pango

# These dependencies are automatically installed with Pango, but listed here for reference:
# brew install glib
# brew install cairo
# brew install fontconfig
# brew install freetype
# brew install harfbuzz
# brew install fribidi
```

The `tracker` script automatically sets up the necessary environment variables to ensure that the WeasyPrint library can find these system dependencies. It configures the dynamic linker paths (`DYLD_LIBRARY_PATH`, `DYLD_FALLBACK_LIBRARY_PATH`, and `LD_LIBRARY_PATH`) to include the Homebrew library paths where these dependencies are installed.

## Setup

1. Create and activate virtual environment:
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment (run this each time you open a new terminal)
source .venv/bin/activate

# When you're done, you can deactivate the virtual environment
deactivate
```

You should see `(.venv)` at the start of your prompt when the virtual environment is active.

2. Install Python dependencies:
```bash
# Install all dependencies
pip install -r requirements.txt

# Install with development tools (optional)
pip install -e '.[dev]'
```

3. Create a `.env` file with your API credentials:
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
vim .env  # or use your preferred editor
```

4. Make the tracker script executable:
```bash
chmod +x tracker
```

## API Setup Instructions

The application integrates with three external services: Whoop, Oura, and OneDrive. Here's how to set up each one:

### Whoop API Setup

1. Create a developer account at [Whoop Developer Portal](https://developer.whoop.com/)
2. Register a new application:
   - Set the redirect URI to `http://localhost:8000/callback`
   - Request scopes: `read:recovery`, `read:workout`, `read:sleep`, `read:profile`
3. Add your credentials to the `.env` file:
   ```
   WHOOP_CLIENT_ID=your-whoop-client-id
   WHOOP_CLIENT_SECRET=your-whoop-client-secret
   ```
4. When you first run the application with `--fetch`, it will:
   - Open a browser window for authentication
   - Ask you to log in to your Whoop account
   - Request permission to access your data
   - Redirect back to your local application
   - Store the authentication tokens locally for future use

### Oura API Setup

1. Create a developer account at [Oura Developer Portal](https://cloud.ouraring.com/developer)
2. Create a new Personal Access Token (PAT):
   - This is the simplest method for personal use
   - Alternatively, you can set up OAuth2 with client ID and secret
3. Add your token to the `.env` file:
   ```
   OURA_API_KEY=your-personal-access-token
   ```

### OneDrive API Setup

1. Go to the [Azure Portal](https://portal.azure.com)
2. Navigate to Azure Active Directory > App registrations
3. Create a new registration:
   - Name: Health Data Analyzer
   - Supported account types: Personal Microsoft accounts only
   - Redirect URI: Public client/native (mobile & desktop) with URI `https://login.microsoftonline.com/common/oauth2/nativeclient`
4. After registration, note your Application (client) ID
5. Under API permissions:
   - Add Microsoft Graph > Delegated permissions
   - Add `Files.ReadWrite` permission
   - Grant admin consent if required
6. Add your client ID to the `.env` file:
   ```
   ONEDRIVE_CLIENT_ID=your-client-id
   ```
7. When you first run the application with `--upload`, it will:
   - Start the device code flow authentication
   - Show a URL and code to enter
   - After authentication, tokens will be cached locally for future use

## Usage

### Basic Usage

Run the complete pipeline (fetch data, generate report, convert to PDF, and upload):
```bash
./tracker --fetch --pdf --upload
```

The `tracker` script handles all the necessary environment setup for proper PDF generation with WeasyPrint.

### Viewing Reports

Reports are generated in the following locations:
- Markdown reports: `data/YYYY-MM-DD/report.md`
- PDF reports: `data/YYYY-MM-DD/report.pdf`
- Charts: `data/charts/`

### Customizing Analysis

You can customize various aspects of the analysis by modifying the configuration files:

- `src/analysis/analyzer_config.py`: Adjust analysis parameters and thresholds
- `src/reporting/reporting_config.py`: Customize report styling, colors, and caloric targets

For example, to adjust the caloric targets for different activity types:

```python
# In src/reporting/reporting_config.py
CALORIC_TARGETS = {
    'strength': 2400,  # Target calories for strength training days
    'rest': 2000       # Target calories for rest days
}
```

## Author

Maintained by newtonlabs
