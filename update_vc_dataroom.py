import os
import shutil

def update_dataroom_structure():
    base_dir = "Ventura_Capital_Data_Room"
    
    # New Folders
    new_structure = {
        "06_Customer_Traction": [
            "Ventura_Capital_Case_Studies.docx"
        ],
        "07_Governance_Compliance": [
            "Ventura_Capital_ESG_Policy.docx"
        ],
        "08_Product_Roadmap": [
            "Ventura_Capital_Product_Roadmap.xlsx"
        ]
    }

    for folder, files in new_structure.items():
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
        f.write("VENTURA CAPITAL - DATA ROOM INDEX (FULL SUITE)\n")
        f.write("==============================================\n\n")
        
        # Sort folders to maintain order
        all_folders = sorted([d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))])
        
        for folder in all_folders:
            f.write(f"[{folder}]\n")
            folder_path = os.path.join(base_dir, folder)
            files = sorted([fil for fil in os.listdir(folder_path) if not fil.startswith('.')])
            for file in files:
                f.write(f"  - {file}\n")
            f.write("\n")

    print("Data Room Structure Updated.")

if __name__ == "__main__":
    update_dataroom_structure()







