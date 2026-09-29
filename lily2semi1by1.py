import re
import pyperclip

# Mapa de notas base a semitonos dentro de una octava
NOTE_MAP = {
    'c': 0, 'cis': 1, 'des': 1,
    'd': 2, 'dis': 3, 'ees': 3,
    'e': 4,
    'f': 5, 'fis': 6, 'ges': 6,
    'g': 7, 'gis': 8, 'aes': 8,
    'a': 9, 'ais': 10, 'bes': 10,
    'b': 11
}

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
            # La primera nota establece el punto de referencia absoluto.
            current_val = base_pitch + octave_shift
            last_val = current_val
            # ELIMINADO: after_pause = False
            # Al no resetearlo aquí, el primer intervalo recordará si hubo un silencio previo.
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

if __name__ == "__main__":
    print("Versión nueva de Lily2semi")
    lilycode = input("Type Lilypond code:\n")
    
    result = lilypond_to_intervals(lilycode)
    
    print("\n--- Resultado Semitonal ---")
    print(result)
    
    try:
        pyperclip.copy(result)
        print("\n¡Copiado al portapapeles! Presiona CTRL+V donde quieras pegarlo.")
    except pyperclip.PyperclipException:
        print("\n[!] No se pudo copiar al portapapeles automáticamente.")
        print("En Linux, instala la herramienta necesaria ejecutando: sudo apt install xclip")
