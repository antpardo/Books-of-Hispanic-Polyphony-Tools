## Hispanic Polyphony Tools

This set of tools is designed for the management, conversion, and uploading of large amounts of musicological data—specifically regarding sources, movements, and musical incipits—to the digital platform of **Books of Hispanic Polyphony (BHP)**. The aim is to streamline data workflows, improve the consistency of uploaded data, and reduce processing time through automated SQLite database synchronization and terminal-based review scripts.

Developed by Antonio Pardo-Cayuela (University of Murcia), these tools facilitate the processing of source data. The toolkit incorporates automated routines for metadata propagation across polyphonic voices (Superius, Altus, Tenor, Bassus, etc), conversion of LilyPond notation into semitone interval sequences (`lily2semi`), and Selenium-based browser automation to seamlessly submit movement records directly into the Drupal-powered BHP platform.

The toolkit consists of the following elements:

### 'BHP_database_design' (BHP SQLite Database) 

Playing the SQL sentences in the file 'BHP_database_design.txt' in a SQL console produces a database which follows the same schema of Books of Hispanic Polyphony (BHP) platform, defining three interconnected tables for data management:

* **"source"** Table: Stores general data about sources ---printed or ms books of polyphony---, such as sigla, geographic location, archive, physical descriptions, watermarks, composers, and  concordances.

* **"work"** Table: Manages information regarding specific musical compositions included in a source, such as work titles, text incipits, genres, liturgical contexts, ascriptions, and modern editions. It connects to the source table via a foreign key (S_ID).

* **"movement"** Table: Tracks individual movements and compositional parts, linked to both sources and works (S_ID and W_ID). It includes detailed voice-specific musical parameters for polyphonic parts, capturing clefs, mensurations, start pitches, semitone interval incipits (_incipit), and the incipits in LilyPond code.

   
### `addmovementBHP`:

`addmovementBHPreg` is a Python automation script powered by **Selenium** designed to bridge your local SQLite database with the Drupal-powered web platform of **Books of Hispanic Polyphony (BHP)**. Its primary goal is to automate the creation and submission of musical movement records.

#### Key Functions

* **Form Automation:** Automatically navigates the web form and fills in metadata fields, including complex WYSIWYG text editors (for fields like Remarks and Comments) using direct JavaScript injection to bypass interface blocks.
* **Smart Submission Handling:** Clicks the submit button and uses intelligent web driver waits (`EC.url_changes`) to ensure the server has fully processed the creation of the new record.
* **Database Synchronization:** Captures the newly generated platform URL (`URL_BHP`) upon a successful upload and writes it back to the local SQLite database (in the "movemen" table).
* **Error Management:** Detects if Drupal rejects a form due to validation errors, alerting you in the terminal so you can review problematic records without corrupting your data tracking.

There are availabe two versios of "addmovementBHP":

* **addmovementBHPreg.py** (OS Evironment Version): This version runs directly using the global system Python installation and system-wide packages. While it doesn't require activating a virtual environment beforehand, it is more susceptible to breaking if global Python packages or system libraries are updated or changed, which can occasionally cause compatibility issues with browser automation tools.

* **addmovementBHPvenv.py** (Virtual Environment Version): This version runs inside an isolated Python virtual environment configured specifically for your project. Its main advantage is that all dependencies (such as Selenium, WebDriver binaries, colorama, etc.) are self-contained within that environment. This prevents version conflicts with other Python packages installed globally on your Linux system and ensures a stable, predictable execution environment every time you activate it.

---

### 'alter_mens_clonerBHP'

`alter_mens_clonerBHP` is an interactive Python script designed to streamline the propagation of musicological metadata across multiple voice parts within your local SQLite database for specific sources.

#### Key Functions

* **Metadata Cloning:** It reads the values of **armadura (key signature)** (e. g. 'S_alter') and **mensuración (time signature) or mensuration sign** ('S_mens') from the Superius voice of a movement.
* **Voice Validation:** It checks whether the respective lower voices—Altus (`A_start_pitch`), Tenor (`T_start_pitch`), and Bassus (`B_start_pitch`) contain active musical data, ensuring it only targets voices that actually exist in that specific piece.
* **Dynamic SQL Updates:** It propagates the Superius key signature and mensuration values into the equivalent fields for the active lower voices (`A_alter`/`A_mens`, `T_alter`/`T_mens`, `B_alter`/`B_mens`).
* **Interactive Control:** Running directly in your terminal, it pauses at each record allowing you to review and choose whether to save (`ENTER`), skip (`s`), or exit (`q`) step-by-step.

---

### `lily2semi_batch.py`

`lily2semi_batch` is a development of `lily2semi1by1`, in which the LilyPond code must be copied one by one into the terminal to be translated into semitone code.
The script automates the musicological data processing workflow directly from your terminal in an interactive, step-by-step manner:

1. **Filters Records**: Connects to your SQLite database and retrieves records from a specific source (such as `E-VAc 06`) that still need processing.
2. **Converts LilyPond Code**: Reads the LilyPond melodic string (e. g. `S_LYincipit`) and transforms it into numerical semitone intervals which are inserted in the corresponding field (e. g. `S_incipit`).
3. **Extracts Starting Pitch**: Parses the first note from the LilyPond code (ignoring initial pauses) and translates it into standard Latin pitch nomenclature (e.g., *Do*, *Re#/Mib*, *La#/Sib*) inserting this string in the correspondig voice field (e. g. `S_start_pitch`).
4. **Interactive Terminal Review**: Displays the original LilyPond code alongside the calculated smitonal code for each record, letting you review, save (`ENTER`), skip (`s`), or exit (`q`) safely before updating the database.

#### Configuration Parameters

To make the script work you need to adjust the variables located at the very bottom of the script:

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
