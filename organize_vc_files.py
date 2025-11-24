import os
import shutil

def organize_data_room():
    base_dir = "Ventura_Capital_Data_Room"
    
    # Folder Structure
    structure = {
        "01_Financials": [
            "Ventura_Capital_Master_Model.xlsx",
            "Ventura_Capital_Herramientas_V3.xlsx" # Keeping V3 as backup/supplement
        ],
        "02_Legal": [
            "Ventura_Capital_Documentacion_V2.docx",
            # Could move the V1 Word doc here too if needed, but V2 is better
        ],
        "03_Investment_Deck": [
            "Ventura_Capital_Pitch_Deck_V2.pptx",
            "Ventura_Capital_Teaser.docx",
            "Ventura_Capital_Investment_Memo.docx"
        ],
        "04_Strategy_Market": [
            "Ventura_Capital_Investor_FAQ.docx"
        ],
        "05_Technical_Due_Diligence": [
            "Ventura_Capital_Tech_Brief.docx"
        ]
    }

    # Create Base Directory
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"Created directory: {base_dir}")

    # Create Subdirectories and Move Files
    for folder, files in structure.items():
        folder_path = os.path.join(base_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        for file in files:
            if os.path.exists(file):
                shutil.move(file, os.path.join(folder_path, file))
                print(f"Moved {file} -> {folder}/")
            else:
                print(f"Warning: {file} not found (skipping)")

    # Create Index File
    with open(os.path.join(base_dir, "00_DATA_ROOM_INDEX.txt"), "w") as f:
        f.write("VENTURA CAPITAL - DATA ROOM INDEX\n")
        f.write("=================================\n\n")
        for folder, files in structure.items():
            f.write(f"[{folder}]\n")
            for file in files:
                f.write(f"  - {file}\n")
            f.write("\n")
            
    print("Data Room Organization Complete.")

if __name__ == "__main__":
    organize_data_room()


