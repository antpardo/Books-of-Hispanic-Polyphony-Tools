import os
import sys
import sqlite3
import time
import traceback
from datetime import datetime
from colorama import Fore, Style, init
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select

# 1. Inicializar colorama
init(autoreset=True)

# 2. EL TRUCO VITAL: Redirigir la carpeta temporal de Geckodriver a la zona segura de Snap
# Si no hacemos esto, AppArmor bloqueará la comunicación y cerrará el proceso.
os.environ['TMPDIR'] = os.path.expanduser('~/snap/firefox/common/')

# 3. Configurar opciones del navegador
options = Options()
options.binary_location = '/snap/firefox/current/usr/lib/firefox/firefox'

# 4. Asignar el perfil persistente en la zona permitida
ruta_perfil = os.path.expanduser('~/snap/firefox/common/perfil_selenium')
os.makedirs(ruta_perfil, exist_ok=True)
options.add_argument('-profile')
options.add_argument(ruta_perfil)

# 5. Iniciar el servicio LIMPIO (Sin usar GeckoDriverManager)
service = Service()

# 6. Lanzar el navegador
# ¡Atención! Asegúrate de que usas 'options' (en plural) para que coincida con la variable de arriba.
driver = webdriver.Firefox(service=service, options=options)

# A partir de aquí sigue el resto de tu código...

# Redirigir la salida estándar al archivo de registro y también a la consola
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

# Crear el log
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
file_name = f"addmovement_{timestamp}.log"
log_file = open(file_name, 'w', encoding='utf-8')

# Configurar el Tee
tee = Tee(sys.stdout, log_file)
sys.stdout = tee
# Hack para que colorama siga funcionando en consola aunque sys.stdout esté redirigido
sys.stdout.isatty = lambda: True 

# Credenciales (¡Recomendable usar variables de entorno en lugar de texto plano!)
usr = os.getenv('BHP_USER', 'user')
psw = os.getenv('BHP_PASS', 'yourpassword')
submission_author = 'your_name'

db_path = '/home/antonio/Dropbox/CSIC-IMF_BHP/valencia_BHP/BHP_dB.sqlite'

def clean_data(value):
    """Convierte nulos a cadenas vacías y limpia saltos de línea."""
    if value is None:
        return ''
    val_str = str(value)
    if '\n' in val_str:
        return val_str.replace('\n', '')
    return val_str

# ----------------- CONEXIÓN DB Y EXTRACCIÓN DE DATOS -----------------
try:
    con = sqlite3.connect(db_path)
    # Usar sqlite3.Row permite acceder a las columnas por nombre (como un diccionario)
    con.row_factory = sqlite3.Row 
    cur = con.cursor()
    print(Fore.GREEN + '[ok]' + Fore.RESET + ' Conexión con tabla MOVEMENTS\n')
except Exception as e:
    print(Fore.RED + '[--]' + Fore.RESET + f' Fallo al conectar con la base de datos: {e}')
    sys.exit()

# Lista de columnas que necesitas
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
    
    # Limpiamos los datos fila por fila y creamos una lista de diccionarios
    movements = []
    for row in raw_data:
        cleaned_row = {col: clean_data(row[col]) for col in columnas}
        movements.append(cleaned_row)
        
    print(Fore.GREEN + '[ok] ' + Fore.RESET + f'Obtenidos los datos de {len(movements)} movimientos.')
except Exception as e:
    print(Fore.RED + '[--]' + Fore.RESET + f' Error al extraer datos: {e}')
    sys.exit()

# ----------------- MENÚ INTERACTIVO -----------------
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

# Los movimientos que vas a procesar están ahora en esta variable:
movements_to_process = [movements[i] for i in selection]

# ----------------- CONFIGURACIÓN SELENIUM Y LOGIN -----------------
print(Fore.WHITE + 'Iniciando navegador y accediendo a BHP...')

try:
    driver.get('https://hispanicpolyphony.eu/user/login')
    
    # Comprobamos rápidamente (sin esperar 15s) si el campo de usuario existe
    elementos_login = driver.find_elements(By.XPATH, '//*[@id="edit-name"]')
    
    if len(elementos_login) > 0:
        # El campo existe, así que NO estamos logueados. Procedemos con el login normal.
        wait = WebDriverWait(driver, 15)
        
        user_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="edit-name"]')))
        user_input.send_keys(usr)
        
        pass_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="edit-pass"]')))
        pass_input.send_keys(psw)
        
        submit_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="edit-submit"]')))
        submit_btn.click()
        
        print(Fore.GREEN + '[ok] ' + Fore.RESET + 'Login exitoso.')
    else:
        # El campo no existe. Gracias al perfil persistente, la sesión ya estaba iniciada.
        print(Fore.GREEN + '[ok] ' + Fore.RESET + 'Sesión recuperada automáticamente (ya estabas logueado).')

   # ----------------- NAVEGACIÓN AL FORMULARIO -----------------
    print(Fore.WHITE + 'Navegando al formulario de nuevo movimiento...')
    
    wait = WebDriverWait(driver, 15)
    driver.get('https://hispanicpolyphony.eu/node/add/movements')
    wait.until(EC.presence_of_element_located((By.ID, 'edit-title')))
    
    print(Fore.GREEN + '[ok] ' + Fore.RESET + 'Formulario "Add Movement" listo para rellenar.')
    
    print(Fore.WHITE + f'Iniciando la carga de {len(movements_to_process)} movimientos...')

    for mov in movements_to_process:
        print(Fore.YELLOW + f"Procesando: {mov['Movement_title']}")
        
        # 1. Cargar la página en blanco para cada movimiento
        driver.get('https://hispanicpolyphony.eu/node/add/movements')
        wait.until(EC.presence_of_element_located((By.ID, 'edit-title')))
        
              
        # --- FUNCIONES AUXILIARES ---
        def rellenar_texto(xpath, valor):
            if valor:
                campo = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                campo.clear()
                campo.send_keys(valor)

        def seleccionar_lista_js(xpath_select, valor):
            if valor and str(valor).strip():
                try:
                    # Inyectamos JavaScript puro para buscar la opción y seleccionarla a la fuerza
                    script = """
                    var select = document.evaluate(arguments[0], document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
                    var valor_buscado = arguments[1];
                    if (select) {
                        for (var i = 0; i < select.options.length; i++) {
                            if (select.options[i].text === valor_buscado) {
                                select.options[i].selected = true;
                                // Disparamos los eventos para que la web actualice el menú visual
                                select.dispatchEvent(new Event('change', { bubbles: true }));
                                if (typeof jQuery !== 'undefined') jQuery(select).trigger('chosen:updated').trigger('change');
                                break;
                            }
                        }
                    }
                    """
                    # Ejecutamos el script pasándole el XPath y el valor de la base de datos
                    driver.execute_script(script, xpath_select, str(valor))
                    time.sleep(0.5)
                except Exception as e:
                    print(Fore.RED + f'  [!] Error al forzar la lista oculta. Valor: {valor}')
                    
        def rellenar_autocomplete(xpath, valor):
            if valor:
                try:
                    campo = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                    campo.clear()
                    campo.send_keys(str(valor))
                    
                    # Pausa vital para que la web busque y aparezca el desplegable AJAX
                    time.sleep(2) 
                    
                    # Pulsamos flecha abajo para marcar la coincidencia y Enter para confirmarla
                    campo.send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.5)
                    campo.send_keys(Keys.ENTER)
                except Exception:
                    print(Fore.RED + f'  [!] Error al autocompletar "{valor}". XPath: {xpath}')
                    
        def rellenar_tags(xpath, lista_valores):
            for valor in lista_valores:
                if valor and str(valor).strip(): 
                    try:
                        campo = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        
                        # 1. Clic explícito para despertar el buscador AJAX de Drupal
                        campo.click()
                        time.sleep(0.5) 
                        
                        print(Fore.CYAN + f"    Intentando insertar etiqueta: '{valor}'")
                        
                        # 2. Escribimos el texto
                        campo.send_keys(str(valor))
                        
                        # 3. Esperamos a que la lista se filtre correctamente
                        time.sleep(2) 
                        
                        # 4. Pulsamos ENTER (al teclear la palabra exacta, cazará la correcta)
                        campo.send_keys(Keys.ENTER)
                        time.sleep(1)
                        
                    except Exception as e:
                        print(Fore.RED + f'  [!] Error al rellenar la etiqueta "{valor}". XPath: {xpath}')
                        
        def rellenar_editor(xpath, valor):
            if valor and str(valor).strip():
                try:
                    # 1. Localizamos el párrafo o div del editor
                    campo = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                    
                    # 2. Desplazamos la pantalla hasta el editor (por si acaso)
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", campo)
                    time.sleep(0.3)
                    
                    # 3. Limpiamos el texto para que las comillas o saltos de línea no rompan el código JS
                    texto_limpio = str(valor).replace('\n', '<br>').replace('"', '\\"').replace("'", "\\'")
                    
                    # 4. Inyectamos el texto directo al HTML y disparamos los eventos de actualización
                    script = f"""
                    var editor = arguments[0];
                    editor.innerHTML = '{texto_limpio}';
                    editor.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    editor.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    editor.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                    """
                    driver.execute_script(script, campo)
                    
                except Exception as e:
                    print(Fore.RED + f'  [!] Error al rellenar el editor. XPath: {xpath}')
                    
                    
        def forzar_clic_por_texto(nombre_autor):
            if nombre_autor and str(nombre_autor).strip():
                # Construimos un XPath que busca cualquier <label> que contenga el nombre
                xpath_dinamico = f"//label[contains(text(), '{nombre_autor}')]"
                
                try:
                    elemento = wait.until(EC.presence_of_element_located((By.XPATH, xpath_dinamico)))
                    
                    # Centramos y hacemos clic ciego por JS sobre la etiqueta de texto
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elemento)
                    time.sleep(0.3)
                    driver.execute_script("arguments[0].click();", elemento)
                    
                except Exception as e:
                    print(Fore.RED + f'  [!] Error al intentar marcar el autor "{nombre_autor}".')
    
        def hacer_clic_submit(xpath):
            try:
                boton = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
                
                # Desplazamos la vista hasta el botón para asegurarnos de que carga en el navegador
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton)
                time.sleep(0.5)
                
                # Clic forzado por JS para evitar cualquier bloqueo visual (barras flotantes, etc.)
                driver.execute_script("arguments[0].click();", boton)
            except Exception as e:
                print(Fore.RED + f'  [!] Error al hacer clic en el botón Submit. XPath: {xpath}')
    

        # --- RELLENANDO CAMPOS ---
 
        
        rellenar_texto('//*[@id="edit-title"]', mov['Movement_title'])
        print(Fore.GREEN + f"  [ok] Datos de Título del movimiento {mov['Movement_title']} rellenados.")
        time.sleep(2)
        
        # 2. Order Number
        rellenar_texto('//*[@id="edit-field-ord-und-0-value"]', mov.get('Order_nr'))
        print(Fore.GREEN + f"  [ok] Datos de Text incipit {mov['Order_nr']} rellenados.")
        time.sleep(2)
        
        # 3. Text Incipit
        rellenar_texto('//*[@id="edit-field-text-incipit-und-0-value"]', mov.get('Txt_incipit'))
        print(Fore.GREEN + f"  [ok] Datos de Text incipit {mov['Txt_incipit']} rellenados.")
        time.sleep(2)
        
        # 4. Work ID
        rellenar_autocomplete('//*[@id="edit-field-work-und-0-target-id"]', mov.get('Work_ID'))
        print(Fore.GREEN + f"  [ok] Datos de Work ID {mov['Work_ID']} rellenados.")
        time.sleep(2)
        
        # 5. Source
        rellenar_autocomplete('//*[@id="edit-field-source1-und-0-target-id"]', mov.get('Source'))
        print(Fore.GREEN + f"  [ok] Datos de Source {mov['Source']} rellenados.")
        time.sleep(2)
        
        # 6. Ascription
        rellenar_autocomplete('//*[@id="edit-field-ascription1-und"]', mov.get('Ascription'))
        print(Fore.GREEN + f"  [ok] Datos de Ascription {mov['Ascription']} rellenados.")
        time.sleep(2)
        
        # 7. Attribution
        rellenar_autocomplete('//*[@id="edit-field-attribution-und-0-target-id"]', mov.get('Attribution'))
        print(Fore.GREEN + f"  [ok] Datos de Attribution {mov['Attribution']} rellenados.")
        time.sleep(2)
        
        # 8. Número de voces
        rellenar_texto('//*[@id="edit-field-no-of-voices-und-0-value"]', mov.get('Nr_voices'))
        print(Fore.GREEN + f"  [ok] Datos de Número de voces {mov['Nr_voices']} rellenados.")
        time.sleep(2)

        # 9. Text Underlay
        rellenar_texto('//*[@id="edit-field-text-underly-und-0-value"]', mov.get('Text_under'))
        print(Fore.GREEN + f"  [ok] Datos de Text Underlay {mov['Text_under']} rellenados.")
        time.sleep(2)
        
        # 10. Genre (Categoría y Tipo desde dos columnas)
        rellenar_tags('/html/body/div[1]/div[2]/div/div[3]/form/div/div[13]/div/div/ul/li/input', [mov.get('Genre_1'), mov.get('Genre_2')])
        print(Fore.GREEN + f"  [ok] Datos de Genre 1 y 2 ({mov.get('Genre_1', 'Genre_2')}) rellenados.")
        time.sleep(2)
        
       # 11. Date
        rellenar_texto('//*[@id="edit-field-data-und-0-value"]', mov.get('Date'))
        print(Fore.GREEN + f"  [ok] Datos de Date ({mov.get('Date')}) rellenados.")
        
      # 12. Location (Comunidad Autónoma, Provincia y Localidad)
        rellenar_tags('/html/body/div[1]/div[2]/div/div[3]/form/div/div[15]/div/div/ul/li/input', [mov.get('Comunidad_Autonoma'), mov.get('Provincia'), mov.get('Localidad')])
        print(Fore.GREEN + f"  [ok] Datos de Location ({mov.get('Comunidad_Autonoma', '')}, {mov.get('Provincia', '')}, {mov.get('Localidad', '')}) rellenados.")
        
      # 13. Remarks
        rellenar_editor('/html/body/div[1]/div[2]/div/div[3]/form/div/div[16]/div/div/div/div/div[2]/div/p', mov.get('Remarks'))
        print(Fore.GREEN + f"  [ok] Datos de Remarks rellenados.")  

      # 14. Comments
        rellenar_editor('/html/body/div[1]/div[2]/div/div[3]/form/div/div[17]/div/div[2]/div/div/div[2]/div', mov.get('Comments'))
        print(Fore.GREEN + f"  [ok] Datos de Comments rellenados.")    
         
     # 15. S_clef (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[23]//select', mov.get('S_clef'))
        print(Fore.GREEN + f"  [ok] Datos de S_clef ({mov.get('S_clef', 'vacío')}) seleccionados.")
    
    # 16. S_alter (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[24]//select', mov.get('S_alter'))
        print(Fore.GREEN + f"  [ok] Datos de S_alter ({mov.get('S_alter', 'vacío')}) seleccionados.")
        
    # 17. S_mens (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[25]//select', mov.get('S_mens'))
        print(Fore.GREEN + f"  [ok] Datos de S_mens ({mov.get('S_mens', 'vacío')}) seleccionados.")
        
    # 18. S_start_pitch (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[26]//select', mov.get('S_start_pitch'))
        print(Fore.GREEN + f"  [ok] Datos de S_start_pitch ({mov.get('S_start_pitch', 'vacío')}) seleccionados.")
    
    # 19. S_incipit (Desplegable forzado por JS)
        rellenar_texto('//*[@id="edit-field-music-incipit-s-und-0-value"]', mov.get('S_incipit'))
        print(Fore.GREEN + f"  [ok] Datos de S_incipit ({mov.get('S_incipit', 'vacío')}) seleccionados.")
    
    # 20. A_clef (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[28]//select', mov.get('A_clef'))
        print(Fore.GREEN + f"  [ok] Datos de A_clef ({mov.get('A_clef', 'vacío')}) seleccionados.")
    
    # 21. A_alter (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[29]//select', mov.get('A_alter'))
        print(Fore.GREEN + f"  [ok] Datos de A_alter ({mov.get('A_alter', 'vacío')}) seleccionados.")
        
    # 22. A_mens (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[30]//select', mov.get('A_mens'))
        print(Fore.GREEN + f"  [ok] Datos de A_mens ({mov.get('A_mens', 'vacío')}) seleccionados.")
        
    # 23. A_start_pitch (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[31]//select', mov.get('A_start_pitch'))
        print(Fore.GREEN + f"  [ok] Datos de A_start_pitch ({mov.get('A_start_pitch', 'vacío')}) seleccionados.")
   
    # 24. A_incipit
        rellenar_texto('//*[@id="edit-field-music-incipit-a-und-0-value"]', mov.get('A_incipit'))
        print(Fore.GREEN + f"  [ok] Datos de A_incipit ({mov.get('A_incipit', 'vacío')}) seleccionados.")
   
    
    # 25. T_clef (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[33]//select', mov.get('T_clef'))
        print(Fore.GREEN + f"  [ok] Datos de T_clef ({mov.get('T_clef', 'vacío')}) seleccionados.")
    
    # 26. T_alter (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[34]//select', mov.get('T_alter'))
        print(Fore.GREEN + f"  [ok] Datos de T_alter ({mov.get('T_alter', 'vacío')}) seleccionados.")
        
    # 27. T_mens (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[35]//select', mov.get('T_mens'))
        print(Fore.GREEN + f"  [ok] Datos de T_mens ({mov.get('T_mens', 'vacío')}) seleccionados.")
        
    # 28. T_start_pitch (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[36]//select', mov.get('T_start_pitch'))
        print(Fore.GREEN + f"  [ok] Datos de T_start_pitch ({mov.get('T_start_pitch', 'vacío')}) seleccionados.")
        
    # 29. T_incipit (Desplegable forzado por JS)
        rellenar_texto('//*[@id="edit-field-music-incipit-t-und-0-value"]', mov.get('T_incipit'))
        print(Fore.GREEN + f"  [ok] Datos de T_incipit ({mov.get('T_incipit', 'vacío')}) seleccionados.")
        
        
    # 30. B_clef (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[38]//select', mov.get('B_clef'))
        print(Fore.GREEN + f"  [ok] Datos de B_clef ({mov.get('B_clef', 'vacío')}) seleccionados.")
    
    # 31. B_alter (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[39]//select', mov.get('B_alter'))
        print(Fore.GREEN + f"  [ok] Datos de B_alter ({mov.get('B_alter', 'vacío')}) seleccionados.")
        
    # 32. B_mens (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[40]//select', mov.get('B_mens'))
        print(Fore.GREEN + f"  [ok] Datos de B_mens ({mov.get('B_mens', 'vacío')}) seleccionados.")
        
    # 33. B_start_pitch (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[41]//select', mov.get('B_start_pitch'))
        print(Fore.GREEN + f"  [ok] Datos de B_start_pitch ({mov.get('B_start_pitch', 'vacío')}) seleccionados.")
    
     # 34. B_incipit
        rellenar_texto('//*[@id="edit-field-music-incipit-b-und-0-value"]', mov.get('B_incipit'))
        print(Fore.GREEN + f"  [ok] Datos de B_incipit ({mov.get('B_incipit', 'vacío')}) seleccionados.")
       
    # 35. S2_clef (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[43]//select', mov.get('S2_clef'))
        print(Fore.GREEN + f"  [ok] Datos de S2_clef ({mov.get('S2_clef', 'vacío')}) seleccionados.")
    
    # 36. S2_alter (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[44]//select', mov.get('S2_alter'))
        print(Fore.GREEN + f"  [ok] Datos de S2_alter ({mov.get('S2_alter', 'vacío')}) seleccionados.")
        
    # 37. S2_mens (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[45]//select', mov.get('S2_mens'))
        print(Fore.GREEN + f"  [ok] Datos de S2_mens ({mov.get('S2_mens', 'vacío')}) seleccionados.")
        
    # 38. S2_start_pitch (Desplegable forzado por JS)
        seleccionar_lista_js('/html/body/div[1]/div[2]/div/div[3]/form/div/div[46]//select', mov.get('S2_start_pitch'))
        print(Fore.GREEN + f"  [ok] Datos de S2_start_pitch ({mov.get('S2_start_pitch', 'vacío')}) seleccionados.")
        
    # 39. S2_incipit (Desplegable forzado por JS)
        rellenar_texto('//*[@id="edit-field-music-incipit-5-und-0-value"]', mov.get('S2_incipit'))
        print(Fore.GREEN + f"  [ok] Datos de S2_incipit ({mov.get('S2_incipit', 'vacío')}) seleccionados.")
       
        

    # 40. Submission author (Búsqueda por nombre visible)
        forzar_clic_por_texto(submission_author)
        print(Fore.GREEN + f"  [ok] Autor procesado: {submission_author}")
        
    
    # 41. Botón de Guardar / Submit
        url_formulario = driver.current_url  # Memorizamos en qué página estamos
        
        hacer_clic_submit('//*[@id="edit-submit"]  ')
        print(Fore.GREEN + "  [ok] Formulario enviado.")
        
             
    # 42. Espera inteligente y guardado en SQLite
        try:
            # Esperamos hasta 15 segundos exclusivamente a que la URL cambie
            wait.until(EC.url_changes(url_formulario))
            
            # Obtenemos la URL de la página resultante donde nos ha redirigido Drupal
            url_generada = driver.current_url
            
            # Actualizamos la base de datos local
            # IMPORTANTE: Cambia 'nombre_de_tu_tabla' por el nombre real de tu tabla
            # y asegúrate de que 'id' es el nombre de la columna que usas como clave primaria.
            cur.execute('''
                UPDATE movement02 
                SET URL_BHP = ? 
                WHERE M_ID = ?
            ''', (url_generada, mov['M_ID']))
            
            # Guardamos los cambios en la base de datos
            con.commit()
            print(Fore.GREEN + f"  [ok] URL guardada en SQLite: {url_generada}")
            
        except Exception as e:
            print(Fore.RED + f"  [!] Error al guardar la URL en SQLite: {e}") 
 
        except TimeoutException:
            # Si pasan 15 segundos y la URL no ha cambiado, Drupal ha rechazado el formulario
            print(Fore.RED + f"  [!] Alerta: Drupal no aceptó el formulario del movimiento {mov['TU_COLUMNA_ID']}. Revisa si falta algún campo obligatorio.")
 
except Exception as e:
            print(Fore.RED + f"  [!] Error al guardar la URL en SQLite: {e}") 
 
except Exception as e:
    print(Fore.RED + f'[xx] Error durante la ejecución general: {e}')
    import traceback
    traceback.print_exc()

finally:
    # 1. Restauramos la salida de la terminal y cerramos el archivo de log
    sys.stdout = sys.__stdout__
    if 'log_file' in locals():
        log_file.close()
    
    # 2. Cerramos la conexión a la base de datos de forma segura
    if 'conn' in locals():
        conn.close()
        print(Fore.CYAN + "  [i] Conexión a la base de datos SQLite cerrada.")
    
    # 3. Descomentamos el cierre automático del navegador para que no consuma memoria
    if 'driver' in locals():
        driver.quit()
        print(Fore.CYAN + "  [i] Navegador cerrado. Proceso finalizado.")
