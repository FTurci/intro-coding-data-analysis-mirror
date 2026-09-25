import os
import shutil
import sys
import re

# get week we want to update to
week = input("Enter the week number to update to (e.g., 01, 02, 03): ")
# copy the contents of the week folder to the root folder safely
source_folder = os.path.join('./hide/', week)
if not os.path.exists(source_folder):
    print(f"Source folder '{source_folder}' does not exist.")
    sys.exit(1)
shutil.copytree(source_folder, f'./{week}', dirs_exist_ok=True)
# get path of teh copied folder
copied_folder_path = os.path.join('.', week)
# remove all ipynb containing "solution" in the copied folder
for root, dirs, files in os.walk(copied_folder_path):
    for file in files:
        if file.endswith('.ipynb') and 'solution' in file:
            file_path = os.path.join(root, file)
            os.remove(file_path)
            print(f"Removed: {file_path}")
# check content and print it
for root, dirs, files in os.walk(copied_folder_path):
    for file in files:
        print(f"Copied file: {os.path.join(root, file)}")

# check root folder for numerical subfolder e.g. 01 02, 03, etc. and return the highest number

subfolders = [f for f in os.listdir('.') if os.path.isdir(f) and f.isdigit()]
print("Subfolders found:", subfolders)
#  now git checkout to branch quarto-files
os.system('git checkout quarto-files')
# uncomment all the lines  inside quarto/_quarto.yml that are contain the selected week but do not contain "solution"
quarto_yml_path = os.path.join('quarto', '_quarto.yml')
if not os.path.exists(quarto_yml_path):
    print(f"File '{quarto_yml_path}' does not exist.")
    sys.exit(1)


# uncommennt new material but keep solutions commented

with open(quarto_yml_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # exclude solution or solutions
    if week in line and ('solution' not in line) and ('Solution' not in line) and ('solution' not in line) and ('solutions' not in line) and ('Solutions' not in line):
        # Preserve leading spaces, remove '#', keep the rest
        line = re.sub(r'^(\s*)#\s?', r'\1', line)
    new_lines.append(line)

with open(quarto_yml_path, 'w') as f:
    f.writelines(new_lines)

# now uncomment solution from previous weeks
with open(quarto_yml_path, 'r') as f:
    lines = f.readlines()
new_lines = []

numerical_week = int(week)
for w in range(1, numerical_week):
    week_str = f"{w:02d}"  # Format week number as two digits
    for line in lines:
        if week_str in line and ('solution' in line or 'Solution' in line or 'solutions' in line or 'Solutions' in line):
            # Preserve leading spaces, remove '#', keep the rest
            line = re.sub(r'^(\s*)#\s?', r'\1', line)
        new_lines.append(line)

with open(quarto_yml_path, 'w') as f:
    f.writelines(new_lines)
    