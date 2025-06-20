"""Utility for converting markdown to PDF."""
import os
import base64
from pathlib import Path
from markdown import markdown
import jinja2
from weasyprint import HTML, CSS

class PDFConverter:
    DEFAULT_CSS = """
    /* Page and Base Styles */
    @page {
        margin: 0.5cm;
    }
    
    body {
        font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
        background: #fff;
        color: #111;
        margin: 0;
        padding: 0.5rem;
        font-size: 12px;
        box-sizing: border-box;
    }
    
    body > * {
        margin-left: 0;
        margin-right: 0;
        padding-left: 0;
        padding-right: 0;
    }
    
    /* Layout */
    .container {
        max-width: 100%;
        margin: auto;
    }
    
    .content {
        padding: 0 2rem;
    }
    
    /* Header Banner */
    .banner {
        background-color: #000;
        padding: 0.5rem 1rem;
        margin-bottom: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .banner img {
        height: 40px;
        width: auto;
    }
    
    .banner .title {
        color: #fff;
        margin: 0;
        font-size: 20px;
        font-weight: 400;
        border: none;
        padding: 0;
    }
    
    /* Headings */
    h1, h2, h3 { 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
        margin-top: 24px;
        margin-bottom: 16px;
        line-height: 1.25;
        font-weight: 500;
        margin-left: 0;
    }
    
    h1 { 
        font-size: 24px;
        padding-bottom: 0.3em;
        margin-bottom: 1em;
        color: #991f1f;
        position: relative;
    }
    
    h1::after {
        content: '';
        position: absolute;
        left: 0;
        right: -2em;
        bottom: 0;
        height: 1px;
        background-color: #991f1f;
    }
    
    h2 { 
        font-size: 20px;
        margin-top: 32px;
        color: #991f1f;
        border-bottom: 1px solid #991f1f;
        padding-bottom: 0.3em;
    }
    
    h3 { 
        font-size: 16px;
        margin-top: 24px;
        font-weight: 600;
        color: #24292e;
    }
    
    /* Text Elements */
    p {
        margin-bottom: 16px;
        margin-left: 0;
        font-size: 14px;
        line-height: 1.6;
    }
    
    /* Control image size */
    img:not(.banner img) {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 1rem auto;
    }
    
    code {
        background-color: #f6f8fa;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
    }
    
    /* Lists */
    ul {
        margin: 0;
        padding-left: 2em;
        list-style-type: disc;
    }
    
    ul ul {
        padding-left: 1.5em;
        list-style-type: circle;
    }
    
    ul ul ul {
        list-style-type: square;
    }
    
    li {
        margin: 0;
        padding: 0;
        line-height: 1.4;
    }
    
    li p {
        margin: 0;
    }
    
    p + ul {
        margin-top: 0.1em;
    }
    
    strong + ul {
        margin-top: 0.2em;
    }
    
    /* Tables */
    table { 
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 1.5rem;
        table-layout: fixed;
        font-size: 11px;
        color: #666666;
    }
    
    th { 
        background-color: #000;
        color: #fff;
        padding: 0.4rem;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.05em;
        text-align: left;
    }
    
    td { 
        padding: 0.4rem;
        border-bottom: 1px solid #ccc;
        color: #666666;
    }
    
    tr:nth-child(even) { 
        background-color: #fcfcfc;
    }
    
    tr:hover {
        background-color: #f5f5f5;
    }
    
    /* Recovery Indicators */
    .recovery-low { 
        color: #991f1f; 
        font-weight: bold; 
    }
    
    .recovery-medium { 
        color: #f1c40f; 
        font-weight: bold; 
    }
    
    .recovery-high { 
        color: #27ae60; 
        font-weight: bold; 
    }
    
    /* Progress Bar */
    .progress-container {
        position: relative;
        display: flex;
        height: 24px;
        margin: 5px 0;
        border-radius: 12px;
        overflow: hidden;
        background-color: #eee;
    }
    
    .progress-protein, .progress-carbs, .progress-fat {
        height: 100%;
        float: left;
        position: relative;
    }
    
    .progress-protein { background-color: #7B1F1F; } /* Dark red for protein */
    .progress-carbs { background-color: #333333; }   /* Black for carbs */
    .progress-fat { background-color: #999999; }     /* Gray for fat */
    
    /* Text inside macro bars */
    .macro-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: white;
        font-weight: bold;
        text-shadow: 1px 1px 1px rgba(0,0,0,0.5);
        font-size: 10px;
        white-space: nowrap;
    }
    
    /* Legend */
    .legend {
        display: flex;
        justify-content: space-between;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    .legend span {
        display: inline-block;
        padding: 0.3rem 0.6rem;
        border-radius: 20px;
        font-size: 11px;
    }
    
    .legend .protein { background-color: #991f1f; color: #fff; }
    .legend .carbs { background-color: #000; color: #fff; }
    .legend .fat { background-color: #aaa; color: #000; }
    """

    def __init__(self, template_dir: str = None):
        """Initialize PDFConverter.
        
        Args:
            template_dir: Optional directory containing HTML templates
        """
        self.template_dir = template_dir
        if template_dir:
            self.jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(template_dir)
            )
        
        # Get project root directory
        self.project_root = str(Path(__file__).parent.parent.parent)
        self.assets_dir = os.path.join(self.project_root, 'assets')

    def markdown_to_pdf(
        self,
        markdown_file: str,
        output_file: str,
        template: str = None,
        css: str = None,
        **template_vars
    ) -> None:
        """Convert markdown file to PDF.
        
        Args:
            markdown_file: Path to markdown file
            output_file: Path to output PDF file
            template: Optional HTML template name (from template_dir)
            css: Optional CSS string to override default styling
            **template_vars: Variables to pass to template
        """
        # Read markdown content
        with open(markdown_file, 'r') as f:
            markdown_content = f.read()
        
        # Extract title and update content
        lines = markdown_content.split('\n')
        title = ''
        new_lines = []
        for line in lines:
            if line.startswith('# Weekly Report for'):
                title = line.replace('# Weekly Report for', '').strip()
            elif line.startswith('# '):
                new_lines.append(line.replace('# ', '## '))
            else:
                new_lines.append(line)
        
        # Add blank lines before lists for proper parsing
        final_lines = []
        prev_line = ''
        for line in new_lines:
            if line.startswith('- ') and prev_line and not prev_line.startswith('- '):
                final_lines.append('')
            final_lines.append(line)
            prev_line = line
        markdown_content = '\n'.join(final_lines)
        
        # Convert markdown to HTML
        html_content = markdown(
            markdown_content,
            extensions=[
                'tables',
                'fenced_code',
                'nl2br',
                'sane_lists'
            ]
        )
        
        # Apply template if provided
        if template and self.template_dir:
            template = self.jinja_env.get_template(template)
            html_content = template.render(
                content=html_content,
                **template_vars
            )
        else:
            # Use basic HTML wrapper
            # Read and encode logo
            logo_path = os.path.join(self.assets_dir, 'rb-logo.webp')
            with open(logo_path, 'rb') as f:
                logo_data = base64.b64encode(f.read()).decode('utf-8')
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                <div class="container">
                    <div class="banner">
                        <img src="data:image/webp;base64,{logo_data}" alt="Logo">
                        <div class="title"><em>Weekly Report for {title}</em></div>
                    </div>
                    <div class="content">
                        {html_content}
                    </div>
                </div>
            </body>
            </html>
            """
            
            # HTML content ready for PDF generation
        
        # Create PDF
        css_string = css or self.DEFAULT_CSS
        
        # Set base_url to the directory containing the markdown file
        # This ensures relative image paths are resolved correctly
        markdown_dir = os.path.dirname(os.path.abspath(markdown_file))
        html = HTML(string=html_content, base_url=markdown_dir)
        css = CSS(string=css_string)
        
        # Ensure output directory exists
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate PDF
        html.write_pdf(
            output_file,
            stylesheets=[css]
        )
