import sqlite3

def duplicar_armaduras_mensuraciones(db_path, tabla, fuente_filtro):
    try:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        
        # Seleccionamos los registros de la fuente indicada que tengan datos en el Superius
        query = f'''SELECT M_ID, S_alter, S_mens, 
                           A_start_pitch, T_start_pitch, B_start_pitch 
                    FROM "{tabla}" 
                    WHERE Source = ? AND (S_alter IS NOT NULL OR S_mens IS NOT NULL)'''
                    
        cur.execute(query, (fuente_filtro,))
        registros = cur.fetchall()
        
        print(f"[i] Encontrados {len(registros)} registros en '{fuente_filtro}' para revisar.\n")
        
        procesados = 0
        
        for fila in registros:
            m_id = fila['M_ID']
            s_alter = fila['S_alter']
            s_mens = fila['S_mens']
            
            # Aquí almacenaremos los trozos de la consulta SQL y los valores a inyectar
            updates = []
            params = []
            voces_actualizadas = []
            
            # 1. Comprobar Altus
            if fila['A_start_pitch'] and str(fila['A_start_pitch']).strip():
                updates.append("A_alter = ?, A_mens = ?")
                params.extend([s_alter, s_mens])
                voces_actualizadas.append("Altus")
                
            # 2. Comprobar Tenor
            if fila['T_start_pitch'] and str(fila['T_start_pitch']).strip():
                updates.append("T_alter = ?, T_mens = ?")
                params.extend([s_alter, s_mens])
                voces_actualizadas.append("Tenor")
                
            # 3. Comprobar Bassus
            if fila['B_start_pitch'] and str(fila['B_start_pitch']).strip():
                updates.append("B_alter = ?, B_mens = ?")
                params.extend([s_alter, s_mens])
                voces_actualizadas.append("Bassus")
            
            # Si ninguna de las 3 voces tiene start_pitch, pasamos al siguiente registro en silencio
            if not updates:
                continue
                
            # Mostrar datos en pantalla
            print(f"--- REGISTRO ID: {m_id} ---")
            print(f"Valores base (Superius) -> Armadura: '{s_alter}' | Mensuración: '{s_mens}'")
            print(f"Voces detectadas para copiar : {', '.join(voces_actualizadas)}")
            
            accion = input("Presiona ENTER para clonar (s = saltar, q = guardar y salir): ").strip().lower()
            
            if accion == 'q':
                print("\n[i] Proceso interrumpido por el usuario. Saliendo...")
                break
            elif accion == 's':
                print("  [>] Registro saltado.\n")
                continue
            else:
                # Construimos la consulta UPDATE uniendo solo las partes de las voces que existen
                update_query = f'''UPDATE "{tabla}" 
                                   SET {", ".join(updates)} 
                                   WHERE M_ID = ?'''
                
                # Añadimos el ID al final de la lista de parámetros
                params.append(m_id)
                
                cur.execute(update_query, tuple(params))
                con.commit()
                procesados += 1
                print("  [ok] Voces clonadas.\n")
                
        print(f"\n[ok] Sesión finalizada. {procesados} registros actualizados con éxito.")
        
    except Exception as e:
        print(f"\n[xx] Fallo general en la base de datos: {e}")
    finally:
        if 'con' in locals():
            con.close()


if __name__ == "__main__":
    # --- CONFIGURACIÓN ---
    DB_PATH = '/home/antonio/Dropbox/CSIC-IMF_BHP/valencia_BHP/BHP_dB.sqlite'
    TABLA = 'movement02'
    FUENTE_FILTRO = 'E-VAc 06'
    
    duplicar_armaduras_mensuraciones(DB_PATH, TABLA, FUENTE_FILTRO)
