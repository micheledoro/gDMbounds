import os

# Percorso della cartella da modificare
directory = 'dmbounds/bounds'

# Testo da cercare e testo di sostituzione
old_text = '# %Part of https://github.com/moritzhuetten/DMbounds under the '
new_text = '# %Part of https://github.com/micheledoro/gDMbounds/ under the'

# Funzione per sostituire il testo nei file
def replace_text_in_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Sostituzione del testo
    content = content.replace(old_text, new_text)
    
    with open(file_path, 'w') as file:
        file.write(content)

# Scansione della directory e delle sottodirectory
for subdir, _, files in os.walk(directory):
    for file in files:
        file_path = os.path.join(subdir, file)
        replace_text_in_file(file_path)

print("Sostituzione completata.")
