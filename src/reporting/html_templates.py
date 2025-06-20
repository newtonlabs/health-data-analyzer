"""HTML templates for PDF generation."""

def get_report_template():
    """Return the HTML template for the weekly report.
    
    The template uses the following variables:
    - logo_html: HTML for the logo
    - title: Report title
    - html_content: Main content of the report
    - protein_color: Color for protein segments
    - carbs_color: Color for carbs segments
    - fat_color: Color for fat segments
    - text_color: Color for text elements
    - heading_color: Color for headings
    
    Returns:
        str: HTML template string
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
        /* Page and Base Styles */
        @page {{
            margin: 0.5cm;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            background: #fff;
            color: #111;
            margin: 0;
            padding: 0.5rem;
            font-size: 12px;
            box-sizing: border-box;
        }}
        
        body > * {{
            margin-left: 0;
            margin-right: 0;
            padding-left: 0;
            padding-right: 0;
        }}
        
        /* Layout */
        .container {{
            max-width: 100%;
            margin: auto;
        }}
        
        .content {{
            padding: 0 2rem;
        }}
        
        /* Header Banner */
        .banner {{
            background-color: #000;
            padding: 0.5rem 1rem;
            margin-bottom: 1rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .banner img {{
            height: 40px;
            width: auto;
        }}
        
        .banner .title {{
            color: #fff;
            margin: 0;
            font-size: 20px;
            font-weight: 400;
            border: none;
            padding: 0;
        }}
        
        /* Headings */
        h1, h2, h3 {{ 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            margin-top: 24px;
            margin-bottom: 16px;
            line-height: 1.25;
            font-weight: 500;
            margin-left: 0;
        }}
        
        h1 {{ 
            font-size: 24px;
            padding-bottom: 0.3em;
            margin-bottom: 1em;
            color: {heading_color};
            position: relative;
        }}
        
        h1::after {{
            content: '';
            position: absolute;
            left: 0;
            right: -2em;
            bottom: 0;
            height: 1px;
            background-color: {heading_color};
        }}
        
        h2 {{ 
            font-size: 20px;
            margin-top: 32px;
            color: {heading_color};
            border-bottom: 1px solid {heading_color};
            padding-bottom: 0.3em;
        }}
        
        h3 {{ 
            font-size: 16px;
            margin-top: 24px;
            font-weight: 600;
            color: #24292e;
        }}
        
        /* Text Elements */
        p {{
            margin-bottom: 16px;
            margin-left: 0;
            font-size: 14px;
            line-height: 1.6;
        }}
        
        /* Control image size */
        img:not(.banner img) {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1rem auto;
        }}
        
        code {{
            background-color: #f6f8fa;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
        }}
        
        /* Lists */
        ul {{
            margin: 0;
            padding-left: 2em;
            list-style-type: disc;
        }}
        
        ul ul {{
            padding-left: 1.5em;
            list-style-type: circle;
        }}
        
        ul ul ul {{
            list-style-type: square;
        }}
        
        li {{
            margin: 0;
            padding: 0;
            line-height: 1.4;
        }}
        
        li p {{
            margin: 0;
        }}
        
        p + ul {{
            margin-top: 0.1em;
        }}
        
        strong + ul {{
            margin-top: 0.2em;
        }}
        
        /* Tables */
        table {{ 
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1.5rem;
            table-layout: fixed;
            font-size: 11px;
            color: {text_color};
        }}
        
        th {{ 
            background-color: #000;
            color: #fff;
            padding: 0.4rem;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{ 
            padding: 0.4rem;
            border-top: 1px solid #ddd;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }}
        
        tr:nth-child(even) {{ 
            background-color: #f9f9f9; 
        }}
        
        /* Recovery score styling */
        .recovery-high {{  
            color: {recovery_high_color};
            font-weight: bold;
        }}
        
        .recovery-medium {{ 
            color: {recovery_medium_color};
            font-weight: bold;
        }}
        
        .recovery-low {{ 
            color: {recovery_low_color};
            font-weight: bold;
        }}
        
        /* Macro ratio bar styling */
        .progress-container {{
            display: flex;
            width: 100%;
            height: 30px;
            margin: 1rem 0;
            overflow: hidden;
            border-radius: 12px; /* Rounded corners for the entire container */
        }}
        
        .progress-protein, .progress-carbs, .progress-fat {{
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-size: 10px;
            text-align: center;
            overflow: hidden;
            white-space: nowrap;
        }}
        
        /* Apply rounded corners to the first and last segments */
        .progress-protein:first-child {{
            border-top-left-radius: 12px;
            border-bottom-left-radius: 12px;
        }}
        
        .progress-fat:last-child {{
            border-top-right-radius: 12px;
            border-bottom-right-radius: 12px;
        }}
        
        .macro-text {{
            display: inline-block;
            padding: 0 5px;
            color: white;
            font-weight: normal;
        }}
        
        .progress-protein {{ background-color: {protein_color}; }}
        .progress-carbs {{ background-color: {carbs_color}; }}
        .progress-fat {{ background-color: {fat_color}; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="banner">
                {logo_html}
                <div class="title"><em>Weekly Report for {title}</em></div>
            </div>
            <div class="content">
                {html_content}
            </div>
        </div>
    </body>
    </html>
    """
