import os
import sys
import sqlite3
import time
from datetime import datetime
from colorama import Fore, Style, init

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# 1. Inicializar colorama
init(autoreset=True)

# 2. Configuración del sistema de registros (Logs)
class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, text):
        for f in self.files:
            f.write(text)
            f.flush()

    def flush(self):
        for f in self.files:
            f.flush()

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
file_name = f"addmovement_{timestamp}.log"
log_file = open(file_name, 'w', encoding='utf-8')

# Redirigir la salida estándar
tee = Tee(sys.stdout, log_file)
sys.stdout = tee
sys.stdout.isatty = lambda: True 

# Credenciales y rutas
usr = 'Antonio'
psw = 'anatema2001'
db_path = '/home/antonio/Dropbox/CSIC-IMF_BHP/valencia_BHP/BHP_dB.sqlite'

def clean_data(value):
    """Convierte nulos a cadenas vacías y limpia saltos de línea."""
    if value is None:
        return ''
    val_str = str(value)
    if '\n' in val_str:
        return val_str.replace('\n', '')
    return val_str

# 3. Conexión a la Base de Datos y Extracción
try:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row 
    cur = con.cursor()
    print(Fore.GREEN + '[ok]' + Fore.RESET + ' Conexión con tabla MOVEMENTS\n')
except Exception as e:
    print(Fore.RED + '[--]' + Fore.RESET + f' Fallo al conectar con la base de datos: {e}')
    sys.exit()

columnas = [
    "M_ID", "URL_BHP", "Movement_title", "Order_nr", "Txt_incipit", "Work_ID", 
    "Source", "Ascription", "Attribution", "Nr_voices", "Language", "Text_under", 
    "Genre_1", "Genre_2", "Date", "Comunidad_Autonoma", "Provincia", "Localidad", 
    "Remarks", "Comments", "Concordances_ms", "Concordances_pr", "S_clef", 
    "S_alter", "S_mens", "S_start_pitch", "S_incipit", "A_clef", "A_alter", 
    "A_mens", "A_start_pitch", "A_incipit", "T_clef", "T_alter", "T_mens", 
    "T_start_pitch", "T_incipit", "B_clef", "B_alter", "B_mens", "B_start_pitch", 
    "B_incipit", "S2_clef", "S2_alter", "S2_mens", "S2_start_pitch", "S2_incipit"
]

try:
    query = f'SELECT {", ".join(columnas)} FROM "movement02"'
    cur.execute(query)
    raw_data = cur.fetchall()
    
    movements = []
    for row in raw_data:
        cleaned_row = {col: clean_data(row[col]) for col in columnas}
        movements.append(cleaned_row)
        
    print(Fore.GREEN + '[ok] ' + Fore.RESET + f'Obtenidos los datos de {len(movements)} movimientos.\n')
except Exception as e:
    print(Fore.RED + '[--]' + Fore.RESET + f' Error al extraer datos: {e}')
    sys.exit()
finally:
    con.close()

# 4. Menú Interactivo
selection = []
while True:
    inp = input('¿Qué le gustaría hacer?\n'
                '[1] Subir a BHP todos los movimientos (escriba "All").\n'
                '[2] Subir sólo una entrada (escriba el nº ABSOLUTO).\n'
                '[3] Subir un intervalo (ej. 147-230).\n'
                '[4] Salir ("exit").\n> ').strip()
    
    if inp.lower() == 'all':
        selection = list(range(len(movements)))
        break
    elif inp.isnumeric():
        idx = int(inp) - 1
        if 0 <= idx < len(movements):
            selection = [idx]
            break
        else:
            print(Fore.RED + '[xx]' + Fore.RESET + ' Parámetro fuera de rango.')
    elif '-' in inp:
        try:
            inicio, fin = map(int, inp.split('-'))
            if 0 < inicio <= fin <= len(movements):
                selection = list(range(inicio - 1, fin))
                break
            else:
                print(Fore.RED + '[xx]' + Fore.RESET + ' Intervalo fuera de rango.')
        except ValueError:
            print(Fore.RED + '[xx]' + Fore.RESET + ' Formato de intervalo inválido.')
    elif inp.lower() == 'exit':
        log_file.close()
        sys.exit()
    else:
        print(Fore.RED + '[xx]' + Fore.RESET + ' Comando no reconocido.')

movements_to_process = [movements[i] for i in selection]

# 5. Configuración de Selenium y Login
print(Fore.WHITE + 'Iniciando navegador y accediendo a BHP...')
servicio = Service(GeckoDriverManager().install())
options = webdriver.FirefoxOptions()
# options.add_argument("--headless") # Descomenta si quieres que corra sin mostrar la ventana
driver = webdriver.Firefox(service=servicio, options=options)
wait = WebDriverWait(driver, 20)

try:
    driver.get('https://hispanicpolyphony.eu/user/login')
    
    user_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="edit-name"]')))
    user_input.send_keys(usr)
    
    pass_input = driver.find_element(By.XPATH, '//*[@id="edit-pass"]')
    pass_input.send_keys(psw)
    
    submit_btn = driver.find_element(By.XPATH, '//*[@id="edit-submit"]')
    submit_btn.click()
    
    print(Fore.GREEN + '[ok] ' + Fore.RESET + 'Login exitoso.')

    # 6. Bucle de Automatización y Formularios
    print(Fore.WHITE + f'Iniciando la carga de {len(movements_to_process)} movimientos...')

    for mov in movements_to_process:
        print(Fore.YELLOW + f"Procesando: {mov['Movement_title']}")
        
        # Ir a la página del formulario
        driver.get('https://hispanicpolyphony.eu/node/add/movements')
        wait.until(EC.presence_of_element_located((By.ID, 'edit-title')))
        
        # Funciones auxiliares
        def rellenar_texto(xpath, valor):
            if valor:
                campo = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                campo.clear()
                campo.send_keys(valor)

        def seleccionar_desplegable(xpath, valor):
            if valor:
                try:
                    desplegable = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    desplegable.click()
                    time.sleep(0.5)
                    ActionChains(driver).send_keys(valor).pause(0.5).send_keys(Keys.RETURN).perform()
                except Exception as e:
                    print(Fore.RED + f'  [!] Error al seleccionar "{valor}" en el desplegable: {e}')

        # Rellenar Textboxes
        rellenar_texto('//*[@id="edit-title"]', mov['Movement_title'])
        rellenar_texto('//*[@id="edit-field-ord-und-0-value"]', mov['Order_nr'])
        rellenar_texto('//*[@id="edit-field-text-incipit-und-0-value"]', mov['Txt_incipit'])
        rellenar_texto('//*[@id="edit-field-work-und-0-target-id"]', mov['Work_ID'])
        rellenar_texto('//*[@id="edit-field-source1-und-0-target-id"]', mov['Source'])
        rellenar_texto('//*[@id="edit-field-ascription1-und"]', mov['Ascription'])
        rellenar_texto('//*[@id="edit-field-attribution-und-0-target-id"]', mov['Attribution'])
        rellenar_texto('//*[@id="edit-field-no-of-voices-und-0-value"]', mov['Nr_voices'])
        rellenar_texto('//*[@id="edit-field-text-underly-und-0-value"]', mov['Text_under'])
        rellenar_texto('//*[@id="edit-field-data-und-0-value"]', mov['Date'])
        rellenar_texto('//*[@id="edit-field-concordances-und-0-target-id"]', mov['Concordances_ms'])
        rellenar_texto('//*[@id="edit-field-concordances-prints-und-0-target-id"]', mov['Concordances_pr'])
        rellenar_texto('//*[@id="edit-field-music-incipit-s-und-0-value"]', mov['S_incipit'])

        # Campos de Texto Enriquecido (<p>)
        rellenar_texto('/html/body/div[1]/div[2]/div/div[3]/form/div/div[16]/div/div/div/div/div[2]/div/p', mov['Remarks'])
        rellenar_texto('/html/body/div[1]/div[2]/div/div[3]/form/div/div[17]/div/div[2]/div/div/div[2]/div/p', mov['Comments'])

        # Listas desplegables avanzadas
        seleccionar_desplegable('/html/body/div[1]/div[2]/div/div[3]/form/div/div[13]/div/div/ul/li/input', mov['Genre_1'])
        seleccionar_desplegable('/html/body/div[1]/div[2]/div/div[3]/form/div/div[15]/div/div/ul/li/input', mov['Localidad'])
        
        # Datos del Superius
        seleccionar_desplegable('/html/body/div[1]/div[2]/div/div[3]/form/div/div[23]/div/div/a/div/b', mov['S_clef'])
        seleccionar_desplegable('/html/body/div[1]/div[2]/div/div[3]/form/div/div[24]/div/div/a/span', mov['S_alter'])
        seleccionar_desplegable('/html/body/div[1]/div[2]/div/div[3]/form/div/div[25]/div/div/a/span', mov['S_mens'])
        seleccionar_desplegable('/html/body/div[1]/div[2]/div/div[3]/form/div/div[26]/div/div/a/span', mov['S_start_pitch'])

        print(Fore.GREEN + f"  [ok] Datos de {mov['Movement_title']} rellenados correctamente.")
        time.sleep(2) # Pausa de verificación visual

except Exception as e:
    print(Fore.RED + '[xx] ' + Fore.RESET + f'Error durante la ejecución: {e}')
finally:
    # driver.quit() # Descomenta cuando quieras que se cierre solo al terminar
    sys.stdout = sys.__stdout__
    log_file.close()
