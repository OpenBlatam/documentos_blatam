import os
import shutil

def update_dataroom_v3():
    base_dir = "Ventura_Capital_Data_Room"
    
    # New Folders
    structure = {
        "01_Financials": [ # Updating financial folder
            "Ventura_Capital_Marketing_Budget_ROI.xlsx"
        ],
        "11_Marketing_Brand": [
            "Ventura_Capital_Brand_Guidelines.pptx"
        ],
        "12_Customer_Contracts": [
            "Ventura_Capital_SaaS_MSA.docx"
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

    print("Data Room V3 Update Complete.")

if __name__ == "__main__":
    update_dataroom_v3()


