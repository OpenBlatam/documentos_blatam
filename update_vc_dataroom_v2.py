import os
import shutil

def update_dataroom_v2():
    base_dir = "Ventura_Capital_Data_Room"
    
    # New/Updated Folders
    structure = {
        "02_Legal": [
            "Ventura_Capital_IP_Assignment_Template.docx"
        ],
        "03_Investment_Deck": [
            "Ventura_Capital_Demo_Script.docx"
        ],
        "09_Talent_Culture": [
            "Ventura_Capital_Key_Hires_JDs.docx"
        ],
        "10_Process_Management": [
            "Ventura_Capital_DD_Request_Tracker.xlsx"
        ]
    }

    for folder, files in structure.items():
        folder_path = os.path.join(base_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created folder: {folder}")
            
        for file in files:
            if os.path.exists(file):
                shutil.move(file, os.path.join(folder_path, file))
                print(f"Moved {file} -> {folder}/")
            else:
                print(f"Warning: {file} not found in root.")

    # Update Index
    index_path = os.path.join(base_dir, "00_DATA_ROOM_INDEX.txt")
    with open(index_path, "w") as f:
        f.write("VENTURA CAPITAL - DATA ROOM INDEX (EXTENDED)\n")
        f.write("===========================================\n\n")
        
        all_folders = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
        
        for folder in all_folders:
            f.write(f"[{folder}]\n")
            folder_path = os.path.join(base_dir, folder)
            files = sorted([fil for fil in os.listdir(folder_path) if not fil.startswith('.')])
            for file in files:
                f.write(f"  - {file}\n")
            f.write("\n")

    print("Data Room V2 Update Complete.")

if __name__ == "__main__":
    update_dataroom_v2()







