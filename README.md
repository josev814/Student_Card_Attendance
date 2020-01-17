# Vault Query
A Python application to query vault

#Requirements
Json

wxPython

ConfigParser

# Compress to a single exe with this command
pyinstaller --onefile --windowed scanner.py

# After running modify .spec
modify scanner.spec

analysis should exclude scanner.ini in compile so it can be referenced and updated

    a = Analysis(['scanner.py'],
        pathex=['D:\\Python\\CardReader'],
        binaries=[],
        datas=[('scanner.config', '.'), ('Class 2.csv', '.')],
run 

    pyinstaller --onefile --windowed scanner.spec
    
This will ensure that the scanner.config file is not packaged in the file