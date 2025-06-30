"""HTML templates for PDF generation."""


def get_report_template():
    """Return the HTML template for the weekly report.

    The template uses the following variables:
    - rb_logo_html: HTML for the RB logo (left side)
    - newtonlabs_logo_html: HTML for the NewtonLabs logo (right side)
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
            font-size: 14px;
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
            background: #1a1a1a;
            background: linear-gradient(135deg, #1a1a1a 0%, #111111 50%, #000000 100%);
            padding: 1.8rem 2.5rem; /* Increased padding for more breathing room */
            margin-bottom: 2rem;
            display: flex;
            justify-content: space-between; /* Space between left and right sections */
            align-items: center;
            position: relative;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3), 0px 2px 10px rgba(0, 0, 0, 0.2); /* Enhanced shadow depth */
            border-radius: 0; /* Sharper corners for a more premium look */
            overflow: hidden;
            font-style: normal; /* Ensure no italics in the banner */
        }}
        
        /* Ensure no italics in any element within the banner */
        .banner * {{
            font-style: normal;
        }}
        
        /* Red-cyan gradient bottom border unifying both sides */
        .banner::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, 
                #B3001B 0%,     /* Bright red start (RB side) */
                #8B0000 25%,    /* Dark red */
                #4a4a4a 50%,    /* Neutral middle */
                #00a8cc 75%,    /* Darker cyan */
                #00d4ff 100%    /* Cyan end (NewtonLabs side) */
            );
            box-shadow: 0 0 6px rgba(100, 100, 255, 0.4); /* Unified glow effect */
        }}
        
        /* Cyan accent line under NewtonLabs logo */
        .banner .right-section::after {{
            content: '';
            position: absolute;
            bottom: 30px; /* Positioned even higher to match shifted logo */
            right: 2.5rem;
            width: 115px; /* Match increased logo width */
            height: 2px;
            background: linear-gradient(90deg, transparent 0%, #00d4ff 20%, #00a8cc 80%, transparent 100%);
            box-shadow: 0 0 4px rgba(0, 212, 255, 0.6); /* Reduced blur for crisper edge */
            border-radius: 1px;
        }}
        

        
        .banner img {{
            height: 60px;
            width: auto;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
        }}
        
        .banner .left-section {{
            display: flex;
            align-items: center;
        }}
        
        .banner .left-section img {{
            margin-right: 0; /* Remove margin since no divider */
        }}
        
        .banner .right-section {{
            display: flex;
            align-items: flex-start; /* Align to top for higher positioning */
            padding-top: 5px; /* Shift NewtonLabs logo even higher */
        }}
        
        .banner .right-section img {{
            margin-left: 0; /* Remove margin since no divider */
            height: 115px; /* Increased by additional 5-10% to equal RB logo weight */
            position: relative;
        }}
        
        .banner .title {{
            color: #fff;
            margin: 0;
            border: none;
            padding: 0 40px; /* Increased padding for better centering */
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Subtle shadow to elevate text block */
            background: rgba(0, 0, 0, 0.1); /* Very subtle background for shadow effect */
            border-radius: 8px; /* Rounded corners for elevated look */
            flex: 1; /* Allow title to take remaining space */
            display: flex;
            flex-direction: column;
            justify-content: center; /* Center vertically with logos */
            align-items: center; /* Center horizontally */
            position: relative;
            text-align: center; /* Center text alignment */
        }}
        
        .banner .title .name {{
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            font-size: 32px;
            font-weight: 600; /* Bold for name */
            font-style: normal;
            letter-spacing: 0.5px;
            margin: 0;
            line-height: 1.1;
        }}
        
        .banner .title .date-range {{
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            font-size: 18px;
            font-weight: 300; /* Lighter font for date */
            font-style: normal;
            margin-top: 8px;
            color: #CCCCCC;
            letter-spacing: 0.3px;
            line-height: 1.2;
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
            font-size: 14px; /* Match the body font size */
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
                <div class="left-section">
                    {rb_logo_html}
                </div>
                <div class="title">
                    <div class="name">Thomas Newton</div>
                    <div class="date-range">{report_start} to {report_end}</div>
                </div>
                <div class="right-section">
                    {newtonlabs_logo_html}
                </div>
            </div>
            <div class="content">
                {html_content}
            </div>
        </div>
    </body>
    </html>
    """
