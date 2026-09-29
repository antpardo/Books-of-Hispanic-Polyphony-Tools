## Hispanic Polyphony Tools

This set of tools is designed for the management, conversion, and uploading of large amounts of musicological data—specifically regarding sources, movements, and musical incipits—to the digital platform of **Books of Hispanic Polyphony (BHP)**. The aim is to streamline data workflows, improve the consistency of uploaded data, and reduce processing time through automated SQLite database synchronization and terminal-based review scripts.

Developed by Antonio Pardo-Cayuela (University of Murcia), these tools facilitate the processing of source data. The toolkit incorporates automated routines for metadata propagation across polyphonic voices (Superius, Altus, Tenor, Bassus, etc), conversion of LilyPond notation into semitone interval sequences (`lily2semi`), and Selenium-based browser automation to seamlessly submit movement records directly into the Drupal-powered BHP platform.

The toolkit consists of the following elements:

### SQLite Database (`BHP_dB.sqlite`)

Contains structured tables following the design of the BHP input data forms.

### `addmovementBHPreg.py`:

`addmovementBHPreg` is a Python automation script powered by **Selenium** designed to bridge your local SQLite database with the Drupal-powered web platform of **Books of Hispanic Polyphony (BHP)**. Its primary goal is to automate the creation and submission of musical movement records.

#### Key Functions

* **Form Automation:** Automatically navigates the web form and fills in metadata fields, including complex WYSIWYG text editors (for fields like Remarks and Comments) using direct JavaScript injection to bypass interface blocks.
* **Smart Submission Handling:** Clicks the submit button and uses intelligent web driver waits (`EC.url_changes`) to ensure the server has fully processed the creation of the new record.
* **Database Synchronization:** Captures the newly generated platform URL (`URL_BHP`) upon a successful upload and writes it back to the local SQLite database (`movement02` table).
* **Error Management:** Detects if Drupal rejects a form due to validation errors, alerting you in the terminal so you can review problematic records without corrupting your data tracking.

---
### What `lily2semi_batch.py` does

The script automates the musicological data processing workflow directly from your terminal in an interactive, step-by-step manner:

1. **Filters Records**: Connects to your SQLite database and retrieves records from a specific source (such as `E-VAc 06`) that still need processing.
2. **Converts LilyPond Code**: Reads the LilyPond melodic string (`S_LYincipit`) and transforms it into numerical semitone intervals (`S_incipit`) using your custom interval conversion logic (`lily2semi`).
3. **Extracts Starting Pitch**: Parses the first note from the LilyPond code (ignoring initial pauses) and translates it into standard Latin pitch nomenclature (e.g., *Do*, *Re#/Mib*, *La#/Sib*) for the designated voice column (`S_start_pitch`).
4. **Interactive Terminal Review**: Displays the original LilyPond code alongside the calculated outputs for each record, letting you review, save (`ENTER`), skip (`s`), or exit (`q`) safely before updating the database.

#### Configuration Parameters

To make the script work according to your specific database structure and source files, you need to adjust the variables located at the very bottom of the script (`if __name__ == "__main__":`):

* **`DB_PATH`**: The full file path to your SQLite database (e.g., `'/home/.../BHP_dB.sqlite'`).
* **`TABLA`**: The name of your database table (e.g., `'BHPmovements'`).
* **`COLUMNA_ID`**: The primary key column name (e.g., `'M_ID'`).
* **`COLUMNA_FUENTE`**: The column used to filter sources (e.g., `'Source'`).
* **`FUENTE_FILTRO`**: The specific source value you want to target (e.g., `'E-VAc 06'`).
* **`COLUMNA_LILYPOND`**: The source column containing the LilyPond code (e.g., `'S_LYincipit'`).
* **`COLUMNA_SEMITONOS`**: The destination column where semitone intervals will be saved (e.g., `'S_incipit'`).
* **`COLUMNA_PRIMERA_NOTA`**: The destination column where the translated Latin starting pitch will be saved (e.g., `'S_start_pitch'`).



## About Books of Hispanic Polyphony

**Books of Hispanic Polyphony (BHP)** is a digital catalogue dedicated to the documentation, study, and dissemination of Renaissance polyphonic music repertories associated with the Hispanic world. Accessible via its digital platform ([https://hispanicpolyphony.eu](https://hispanicpolyphony.eu)), the project serves as a premier open-access repository for musicologists, historians, and performers.

Created under the direction of Emilio Ros-Fábregas, the platform bridges archival musicology and digital humanities. It provides detailed codicological and musical descriptions, standardizes incipits, and offers data on sources, composers, and works, fostering comparative analysis of Hispanic sacred and secular polyphony from the 15th to the 19th centuries.

The website acts as a resource for researchers, academic institutions, and early music performers exploring cultural heritage and manuscript transmission across Spain, Portugal, and the Americas. By integrating structured databases with web publishing technologies, Books of Hispanic Polyphony ensures long-term preservation and global accessibility of musical sources.

### Project Context and Team

The development of Hispanic Polyphony initiatives has been supported by research grants and projects focused on the digital transition and heritage preservation in musicology.

**Research and Development Team:**
* Dr. Emilio Ros-Fábregas, Director
Tenured Researcher ad honorem in Musicology, IMF-CSIC, Barcelona

* Dr. María Gembero-Ustárroz
Tenured Researcher in Musicology, IMF-CSIC

* Dr. Andrea Puentes-Blanco
Tenured Researcher in Musicology, IMF-CSIC

* Juan José Pérez-Gual
Technitian PTA, IMF-CSIC
Ph.D. candidate, Musicology, Universidad de Granada

* Dr. Ascensión Mazuela-Anguita
Tenured professor, Universidad de Granada

* Dr. Giuseppe Fiorentino
Tenured professor, Universidad de Cantabria

* Dr. Javier Marín-López
Professor, Universidad de Jaén

* Dr. Antonio Pardo Cayuela
"Profesor Colaborador", Universidad de Murcia

* Dr. Pablo López-Rocamora
Universidad de Murcia
