import os
import shutil

def finalize_data_room():
    base_dir = "Ventura_Capital_Data_Room"
    
    # Update Structure with new files
    new_files_map = {
        "01_Financials": ["Ventura_Capital_Master_Model_V5.xlsx"],
        "04_Strategy_Market": [
            "Ventura_Capital_Exit_Strategy.docx", 
            "Ventura_Capital_GTM_Playbook.docx"
        ]
    }

    for folder, files in new_files_map.items():
        folder_path = os.path.join(base_dir, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        for file in files:
            if os.path.exists(file):
                shutil.move(file, os.path.join(folder_path, file))
                print(f"Moved {file} -> {folder}/")
            else:
                print(f"Warning: {file} not found (skipping)")
                
    # Remove old versions if needed, or keep them. 
    # Let's remove V4 model to avoid confusion if V5 is present.
    v4_path = os.path.join(base_dir, "01_Financials", "Ventura_Capital_Master_Model.xlsx")
    if os.path.exists(v4_path):
        os.remove(v4_path)
        print("Removed old V4 Model to avoid confusion.")

    # Update Index
    index_path = os.path.join(base_dir, "00_DATA_ROOM_INDEX.txt")
    with open(index_path, "w") as f:
        f.write("VENTURA CAPITAL - DATA ROOM INDEX (FINAL)\n")
        f.write("=========================================\n\n")
        
        # Walk through directory to list current state
        for root, dirs, files in os.walk(base_dir):
            level = root.replace(base_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            if level == 0:
                pass # Root
            else:
                f.write(f"{indent}[{os.path.basename(root)}]\n")
                subindent = ' ' * 4 * (level + 1)
                for file in sorted(files):
                    if file != "00_DATA_ROOM_INDEX.txt" and not file.startswith("."):
                        f.write(f"{subindent}- {file}\n")
                f.write("\n")

    print("Data Room Finalized.")

if __name__ == "__main__":
    finalize_data_room()


