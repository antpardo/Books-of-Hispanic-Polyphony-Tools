import sqlite3
import re

# --- MAPAS MUSICALES ---
NOTE_MAP = {
    'c': 0, 'cis': 1, 'des': 1,
    'd': 2, 'dis': 3, 'ees': 3,
    'e': 4,
    'f': 5, 'fis': 6, 'ges': 6,
    'g': 7, 'gis': 8, 'aes': 8,
    'a': 9, 'ais': 10, 'bes': 10,
    'b': 11
}

# Mapa para la traducción a nota latina
LATIN_MAP = {
    'c': 'do', 'cis': 'Do#/Reb', 'des': 'Do#/Reb',
    'd': 're', 'dis': 'Re#/Mib', 'ees': 'Re#/Mib',
    'e': 'mi',
    'f': 'fa', 'fis': 'Fa#/Solb', 'ges': 'Fa#/Solb',
    'g': 'sol', 'gis': 'Sol#/Lab', 'aes': 'Sol#/Lab',
    'a': 'la', 'ais': 'La#/Sib', 'bes': 'La#/Sib',
    'b': 'si'
}


# --- FUNCIONES DE CONVERSIÓN ---
def lilypond_to_intervals(lilycode):
    tokens = lilycode.split()
    cleaned_tokens = [re.sub(r'[\d\.]+', '', t) for t in tokens if re.sub(r'[\d\.]+', '', t)]

    output = []
    last_val = None
    after_pause = False

    for token in cleaned_tokens:
        if token == 'r':
            after_pause = True
            continue
            
        match = re.match(r'^([a-z]+)([,]*)([\']*)$', token)
        if not match or match.group(1) not in NOTE_MAP:
            continue
            
        note_name, commas, apostrophes = match.groups()
        base_pitch = NOTE_MAP[note_name]
        octave_shift = (len(apostrophes) - len(commas)) * 12
        
        if last_val is None:
            current_val = base_pitch + octave_shift
            last_val = current_val
        else:
            prev_base = last_val % 12
            shortest_diff = (base_pitch - prev_base + 6) % 12 - 6
            
            if shortest_diff == -6 and (base_pitch - prev_base) % 12 == 6:
                shortest_diff = 6
                
            real_diff = shortest_diff + octave_shift
            current_val = last_val + real_diff
            
            prefix = "=P" if after_pause else ""
            
            if real_diff == 0:
                output.append(f"{prefix}=0")
            elif real_diff > 0:
                output.append(f"{prefix}+{real_diff}")
            else:
                output.append(f"{prefix}{real_diff}")
                
            last_val = current_val
            after_pause = False

    if after_pause and len(output) > 0:
        output.append("=P")

    return "".join(output)

def extract_first_latin_note(lilycode):
    # Separa y limpia los números/puntos igual que la función principal
    tokens = lilycode.split()
    cleaned_tokens = [re.sub(r'[\d\.]+', '', t) for t in tokens if re.sub(r'[\d\.]+', '', t)]
    
    for token in cleaned_tokens:
        if token == 'r':  # Ignoramos silencios iniciales
            continue
            
        # Busca el nombre de la nota ignorando las octavas (comas y apóstrofes)
        match = re.match(r'^([a-z]+)([,]*)([\']*)$', token)
        if match and match.group(1) in LATIN_MAP:
            return LATIN_MAP[match.group(1)]
            
    return ""  # Devuelve vacío si no encuentra ninguna nota válida


# --- PROCESAMIENTO INTERACTIVO DE LA BASE DE DATOS ---
def procesar_bd_lilypond_paso_a_paso(db_path, tabla, col_id, col_origen, col_destino, col_fuente, fuente_filtro, col_pitch):
    try:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        # Filtramos por fuente y comprobamos si falta ALGUNO de los dos campos destino
        query = f'''SELECT {col_id}, {col_origen} FROM "{tabla}" 
                    WHERE {col_origen} IS NOT NULL AND {col_origen} != "" 
                    AND ({col_destino} IS NULL OR {col_destino} = "" OR {col_pitch} IS NULL OR {col_pitch} = "")
                    AND "{col_fuente}" = ?'''
                    
        cur.execute(query, (fuente_filtro,))
        registros = cur.fetchall()
        
        print(f"[i] Encontrados {len(registros)} registros de '{fuente_filtro}' pendientes de actualizar.\n")
        
        procesados = 0
        
        for fila in registros:
            id_registro = fila[col_id]
            codigo_lily = fila[col_origen]
            
            # Conversiones
            resultado_semitonos = lilypond_to_intervals(codigo_lily)
            primera_nota_latina = extract_first_latin_note(codigo_lily)
            
            # Mostrar datos
            print(f"--- REGISTRO ID: {id_registro} ---")
            print(f"Original (LilyPond) : {codigo_lily}")
            print(f"Semitonos calculados: {resultado_semitonos}")
            print(f"Primera nota latina : {primera_nota_latina}")
            
            accion = input("Presiona ENTER para guardar (s = saltar, q = guardar y salir): ").strip().lower()
            
            if accion == 'q':
                print("\n[i] Proceso interrumpido por el usuario. Saliendo...")
                break
            elif accion == 's':
                print("  [>] Registro saltado.\n")
                continue
            else:
                # Actualizamos ambas columnas simultáneamente
                update_query = f'''UPDATE "{tabla}" 
                                   SET "{col_destino}" = ?, "{col_pitch}" = ? 
                                   WHERE "{col_id}" = ?'''
                cur.execute(update_query, (resultado_semitonos, primera_nota_latina, id_registro))
                con.commit()
                procesados += 1
                print("  [ok] Guardado.\n")
                
        print(f"\n[ok] Sesión finalizada. {procesados} registros convertidos y guardados con éxito.")
        
    except Exception as e:
        print(f"\n[xx] Fallo general en la base de datos: {e}")
    finally:
        if 'con' in locals():
            con.close()


if __name__ == "__main__":
    # --- CONFIGURACIÓN ---
    DB_PATH = '/home/antonio/Dropbox/CSIC-IMF_BHP/valencia_BHP/BHP_dB.sqlite'
    TABLA = 'movement02'
    COLUMNA_ID = 'M_ID'
    COLUMNA_FUENTE = 'Source'
    FUENTE_FILTRO = 'E-VAc 06'
    
    # Origen y Destinos
    COLUMNA_LILYPOND = 'T2_LYincipit'
    COLUMNA_SEMITONOS = 'T2_incipit'
    COLUMNA_PRIMERA_NOTA = 'T2_start_pitch' # Modifica aquí si necesitas apuntar a otra voz
    
    procesar_bd_lilypond_paso_a_paso(
        DB_PATH, TABLA, COLUMNA_ID, COLUMNA_LILYPOND, 
        COLUMNA_SEMITONOS, COLUMNA_FUENTE, FUENTE_FILTRO, COLUMNA_PRIMERA_NOTA
    )
