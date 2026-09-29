## Hispanic Polyphony Tools

This set of tools is designed for the management, conversion, and uploading of large amounts of musicological data—specifically regarding sources, movements, and musical incipits—to the digital platform of **Books of Hispanic Polyphony (BHP)**. The aim is to streamline data workflows, improve the consistency of uploaded data, and reduce processing time through automated SQLite database synchronization and terminal-based review scripts.

Developed by Antonio Pardo-Cayuela (University of Murcia), these tools facilitate the processing of source data. The toolkit incorporates automated routines for metadata propagation across polyphonic voices (Superius, Altus, Tenor, Bassus, etc), conversion of LilyPond notation into semitone interval sequences (`lily2semi`), and Selenium-based browser automation to seamlessly submit movement records directly into the Drupal-powered BHP platform.

The toolkit consists of the following elements:

* **SQLite Database (`BHP_dB.sqlite`)**: Contains structured tables following the design of the BHP input data forms.
* **Python Automation Scripts**:
* *Conversion Utilities*: `lily2semi` to automatically parse LilyPond code into numerical semitone intervals and convert notes into standard Latin nomenclature to be inserted automatically in the field 'starting pitch' of every voice ('lily2semi_batch'), supervised step-by-step. 
* *Web Submission*: Selenium-based scripts optimized with intelligent waits and JavaScript injection to populate Drupal forms and record generated platform URLs back into the local database ("addmovementBHP2026.py").


## About Books of Hispanic Polyphony

**Books of Hispanic Polyphony (BHP)** is a specialized research initiative and digital platform dedicated to the documentation, study, and dissemination of Renaissance polyphonic music repertories associated with the Hispanic world. Accessible via its digital platform ([https://hispanicpolyphony.eu](https://hispanicpolyphony.eu)), the project serves as a premier open-access repository for musicologists, historians, and performers.

Created under the direction of Emilio Ros-Fábregas, the platform bridges archival musicology and digital humanities. It provides detailed codicological and musical descriptions, standardizes incipits, and offers data on sources, composers, and works, fostering comparative analysis of Hispanic sacred and secular polyphony from the 15th to the 19th centuries.

The website acts as a resource for researchers, academic institutions, and early music performers exploring cultural heritage and manuscript transmission across Spain, Portugal, and the Americas. By integrating structured databases with web publishing technologies, Books of Hispanic Polyphony ensures long-term preservation and global accessibility of rare musical sources.

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
