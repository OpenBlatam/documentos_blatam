import os

def generate_html_index():
    base_dir = "Ventura_Capital_Data_Room"
    output_file = os.path.join(base_dir, "index.html")
    
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ventura Capital - Data Room</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; color: #333; margin: 0; padding: 20px; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #203764; padding-bottom: 20px; }
            h1 { color: #203764; margin: 0; font-size: 2.5em; }
            p.subtitle { color: #666; font-size: 1.2em; }
            .folder { margin-bottom: 25px; }
            .folder-title { background: #2f75b5; color: white; padding: 10px 15px; border-radius: 5px; font-weight: bold; font-size: 1.1em; display: flex; align-items: center; }
            .folder-title i { margin-right: 10px; }
            ul { list-style: none; padding: 0; margin: 10px 0 0 0; border: 1px solid #eee; border-radius: 0 0 5px 5px; }
            li { padding: 12px 20px; border-bottom: 1px solid #eee; display: flex; align-items: center; transition: background 0.2s; }
            li:last-child { border-bottom: none; }
            li:hover { background-color: #f9f9f9; }
            li a { text-decoration: none; color: #333; font-weight: 500; flex-grow: 1; }
            li span.type { background: #eee; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; color: #666; margin-left: 10px; }
            .footer { text-align: center; margin-top: 50px; font-size: 0.9em; color: #aaa; }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>VENTURA CAPITAL</h1>
                <p class="subtitle">Series A Investment Data Room</p>
            </header>
    """

    # Folder Descriptions (Mapping for niceness)
    folder_desc = {
        "01_Financials": "Master Financial Models & Projections",
        "02_Legal": "Corporate Structure & Agreements",
        "03_Investment_Deck": "Pitch Deck, Memo & Teaser",
        "04_Strategy_Market": "GTM, Exit Strategy & FAQ",
        "05_Technical_Due_Diligence": "Architecture & Security",
        "06_Customer_Traction": "Case Studies & ROI",
        "07_Governance_Compliance": "ESG & Policies",
        "08_Product_Roadmap": "Development Plans 2025",
        "09_Talent_Culture": "Key Hires & JDs",
        "10_Process_Management": "Due Diligence Tracking",
        "11_Marketing_Brand": "Brand Identity & Budgets", # New
        "12_Customer_Contracts": "MSA & Service Agreements" # New
    }

    # Get Folders
    all_dirs = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
    
    for folder in all_dirs:
        desc = folder_desc.get(folder, folder)
        html_content += f"""
            <div class="folder">
                <div class="folder-title">{desc} <span style="opacity:0.6; font-weight:normal; font-size:0.8em; margin-left:auto;">{folder}</span></div>
                <ul>
        """
        
        files = sorted([f for f in os.listdir(os.path.join(base_dir, folder)) if not f.startswith('.')])
        for file in files:
            ext = file.split('.')[-1].upper()
            html_content += f"""
                    <li>
                        <a href="{folder}/{file}">{file}</a>
                        <span class="type">{ext}</span>
                    </li>
            """
        
        html_content += "</ul></div>"

    html_content += """
            <div class="footer">
                Confidential Information - Do Not Distribute<br>
                Generated automatically by Ventura Capital System
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(output_file, "w") as f:
        f.write(html_content)
    
    print(f"HTML Index generated: {output_file}")

if __name__ == "__main__":
    generate_html_index()







