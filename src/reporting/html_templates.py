"""HTML templates for PDF generation."""


def get_report_template():
    """Return the HTML template for the weekly report.

    The template uses the following variables:
    - logo_html: HTML for the logo
    - report_start: Start date of the report period (MM-DD format)
    - report_end: End date of the report period (MM-DD format)
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
        
        /* Premium Header Banner - inspired by the provided image */
        .banner {{
            background: linear-gradient(to bottom, #2a2a2a, #1a1a1a);
            padding: 1.5rem 2rem;
            margin-bottom: 2rem;
            display: flex;
            justify-content: flex-start; /* Align items to the left for better balance */
            align-items: center;
            position: relative;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2), 0px 4px 8px rgba(0, 0, 0, 0.2); /* Added soft outer shadow */
            border-radius: 0; /* Sharper corners for a more premium look */
            overflow: hidden;
            font-style: normal; /* Ensure no italics in the banner */
        }}
        
        /* Ensure no italics in any element within the banner */
        .banner * {{
            font-style: normal;
        }}
        
        /* Red accent line at the bottom of the banner */
        .banner::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background-color: #B3001B; /* Deeper, richer red that pops more on dark background */
            box-shadow: 0 0 8px rgba(179, 0, 27, 0.7); /* Enhanced glow effect */
        }}
        
        .banner img {{
            height: 60px;
            width: auto;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
            margin-right: 20px; /* Reduced space to account for divider */
        }}
        
        /* Semi-transparent vertical divider between logo and text */
        .vertical-divider {{
            height: 50px; /* Extended to about 85% of the text block height */
            width: 1px;
            background-color: rgba(255, 255, 255, 0.25); /* Semi-transparent white */
            margin: 0 20px;
            align-self: center;
        }}
        
        .banner .title {{
            color: #fff;
            margin: 0;
            font-size: 28px;
            font-weight: 300;
            font-style: normal; /* Explicitly set to normal to prevent italics */
            letter-spacing: 1px;
            border: none;
            padding: 0;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            flex: 1; /* Allow title to take remaining space */
            transform: translateY(-2px); /* Slight upward nudge for optical centering */
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
        
        /* Tables - using compact styling for all tables */
        table {{ 
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1.5rem;
            table-layout: fixed;
            font-size: 0.75em;
            color: {text_color};
        }}
        
        th {{ 
            background-color: {carbs_color};
            color: #fff;
            padding: 5px;
            text-align: left;
            font-weight: bold;
            font-size: 0.85em;
        }}
        
        td {{ 
            padding: 3px 5px;
        }}
        
        /* Right-justify numeric columns */
        td.right-align,
        th.right-align {{ 
            text-align: right;
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
            width: 80%;  /* Reduced width to allow for centering */
            height: 20px;
            margin: 1rem auto;  /* Auto margins for horizontal centering */
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
                <div class="vertical-divider"></div>
                <div class="title">
                    <div style="font-size: 28px; font-weight: 500; font-style: normal;">Thomas Newton</div>
                    <div style="font-size: 22px; font-weight: 300; font-style: normal; margin-top: 15px; color: #CCCCCC;">{report_start} to {report_end}</div>
                </div>
            </div>
            <div class="content">
                {html_content}
            </div>
        </div>
    </body>
    </html>
    """
