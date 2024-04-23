import os
import shutil
import sys
import stat
import py7zlib


# Defino las variables generales
if not len(sys.argv) > 1:
    input_dir = r"d:\COMICS\Batman - Three Jockers"
else:
    input_dir = sys.argv[1]


# Defino el directorio del programa como el directorio actual 
prog_dir = os.path.dirname(os.path.realpath(__file__))
# Defino el directorio de los ficheros temporales
temp_dir = os.path.join(prog_dir, "temp")
# Defino el directorio de los ficheros logs
log_dir = os.path.join(prog_dir, "log")
# Defino el nombre del fichero log cogiendolo del nombre del directorio
log_file = os.path.join(log_dir, "%s.log" % os.path.splitext(os.path.basename(input_dir))[0])
# Defino el fichero de patrones prohibidos
patrones_prohibidos_file = os.path.join(prog_dir, "patrones_prohibidos.cfg")

''' 
Creates the log directory if it does not already exist. 
This ensures that the log file can be written to the appropriate location.
'''
try:
    os.makedirs(log_dir)
except OSError:
    pass

'''
Creates the temporary directory if it does not already exist. 
This is necessary to store temporary files used during the script's execution.
'''
try:
    os.makedirs(temp_dir)
except OSError:
    pass

"""
Deletes the temporary directory and creates it again.
This function is used to clean up the temporary directory used by the script. It first removes the entire directory tree using `shutil.rmtree()`, ignoring any errors that may occur. Then, it recreates the directory using `os.makedirs()`.
This ensures that the temporary directory is in a clean state before the script starts processing any files.
"""
def limpiar_temporal(temp_dir, log):
            # Elimino el directorio temporal y lo creo de nuevo
            log.write("Elimino el directorio temporal y lo creo de nuevo\n")
            shutil.rmtree(temp_dir, ignore_errors=True)
            os.makedirs(temp_dir)




with open(log_file, "w") as log:
    log.write("Defino las variables\n")
    log.write("FICHERO DE LOG: %s\n" % log_file)

    # Borro los directorios de restos
    log.write("Empiezo limpiando todos los restos anteriores\n")
    try:
        os.remove("lista.txt")
    except OSError:
        pass
    
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir)

    # Imprimo los datos iniciales
    log.write("Imprimo los datos iniciales\n")
    os.makedirs(os.path.join(prog_dir, "temp"))

    # Creo la lista de ficheros
    log.write("DIRECTORIO DE ENTRADA: %s\n" % input_dir)
    log.write("FICHEROS A PROCESAR:\n")
    
    # Creo el fichero de lista de ficheros
    """
    Writes a list of all .cbz and .cbr files in the input directory to a file named 'lista.txt' in the same directory.
    This code iterates through all files and directories in the input directory, and writes the full path of each .cbz 
    and .cbr file to the 'lista.txt' file.
    This allows the rest of the script to easily access the list of comic files that need to be processed.
    Also writes the list of comic files to the log file.
    """
    with open(os.path.join(prog_dir, 'lista.txt'), 'w') as lista:
        for raiz, dirs, archivos in os.walk(input_dir):
            for archivo in archivos:
                if archivo.endswith('.cbz') or archivo.endswith('.cbr'):
                    ruta_completa = os.path.join(raiz, archivo)
                    lista.write(ruta_completa + '\n')
        log.write(lista.read())

    # Bucle para procesar cada fichero
    log.write("Inicio un bucle para procesar cada fichero\n")
    with open(os.path.join(prog_dir, "lista.txt"), "r") as lista:
        for file_path in lista:
            file_path = file_path.strip()
            log.write("COMIC A PROCESAR: %s\n" % file_path)

            # Extraigo el comic en el directorio temporal
            log.write("Extraigo el comic en el directorio temporal\n")
            with py7zlib.SevenZipFile(file_path, 'r') as archivo: 
                archivo.extractall(temp_dir)
            
            # Cambio los atributos por si acaso alguno trae algo raro como oculto o de sistema
            log.write("Cambio los atributos por si acaso alguno trae algo raro como oculto o de sistema\n")
            atributos = os.stat(file_path).st_file_attributes

            # Quitar atributos HRS
            atributos &= ~stat.FILE_ATTRIBUTE_HIDDEN
            atributos &= ~stat.FILE_ATTRIBUTE_READONLY
            atributos &= ~stat.FILE_ATTRIBUTE_SYSTEM

            # Asignar permisos lectura y escritura 
            atributos |= stat.FILE_ATTRIBUTE_ARCHIVE
            atributos |= stat.FILE_ATTRIBUTE_NORMAL

            os.chmod(file_path, atributos)
            
            
            # Borro directorio ".DS_Store" y "__MACOSX" de forma recursiva
            log.write("Borro directorio .DS_Store y __MACOSX\n")
            ruta_ds_store = os.path.join(temp_dir, '.DS_Store')
            if os.path.exists(ruta_ds_store):
                try: 
                    shutil.rmtree(ruta_ds_store)
                    print(f'Borrando {ruta_ds_store}')

                except OSError:
                    pass
            
            ruta_macosx = os.path.join(temp_dir, '__MACOSX')
            if os.path.exists(ruta_macosx):
                print(f'Borrando {ruta_macosx}') 
                try:
                    shutil.rmtree(ruta_macosx)
                except OSError:
                    pass
            
            # Borro todos los ficheros con un tamaño menor a 2k
            log.write("Borro todos los ficheros con un tamaño menor a 2k\n")
            for root, dirs, files in os.walk(temp_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    if os.path.getsize(file_path) < 2048:
                        os.remove(file_path)
                        log.write("Borro %s\n" % file_path)


            # Elimino todos los ficheros que no sean de las extensiones permitidas
            log.write("Elimino todos los ficheros que no sean de las extensiones permitidas\n")
            extensiones_permitidas = [".bmp", ".jpg", ".png", ".wep", ".xml"]
            for root, dirs, files in os.walk(temp_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    if not any(file_name.endswith(ext) for ext in extensiones_permitidas):
                        try: 
                            os.remove(file_path)
                            log.write("Borro %s\n" % file_path)
                        except PermissionError:
                            pass
                        
            # Elimino los ficheros que contienen cadenas prohibidas
            log.write("Elimino los ficheros que contienen cadenas prohibidas\n")
            with open(patrones_prohibidos_file, "r") as cadenas_prohibidas:
                for cadena in cadenas_prohibidas:
                    cadena = cadena.strip()
                    for root, dirs, files in os.walk(temp_dir):
                        for file_name in files:
                            file_path = os.path.join(root, file_name)
                            if cadena in file_name:
                                try:
                                    os.remove(file_path)
                                    log.write("Borro %s\n" % file_path)
                                except PermissionError:
                                    log.write("No se pudo borrar %s\n" % file_path)
                                    pass
            '''
            # Borro el fichero del comic original
            log.write("Borro el fichero del comic original\n")
            comic_dir = os.path.dirname(file_path)
            comic_name = os.path.splitext(os.path.basename(file_path))[0]
            os.remove(file_path)
            '''
            # Renombro el fichero antiguo antes de borrarlo
            directorio = os.path.dirname(file_path)
            nombre_archivo = os.path.basename(file_path)
            nuevo_nombre = nombre_archivo + ".bak"
            ruta_nueva = os.path.join(directorio, nuevo_nombre)
            os.rename(file_path, ruta_nueva)


            # Comprimo todos los ficheros de nuevo en modo store con la extensión cbz
            log.write("Comprimo todos los ficheros de nuevo en modo store con la extensión cbz\n")
            with shutil.ZipFile(file_path, 'w', compression=shutil.ZIP_DEFLATED, allowZip64=True) as zf:
                for raiz, dirs, archivos in os.walk(temp_dir):
                    for archivo in archivos:
                        ruta_archivo = os.path.join(raiz, archivo)
                        try:
                            zf.write(ruta_archivo)
                        except PermissionError:
                            # Si no se puede comprimir hay que limpiar el temporal y salir con error
                            log.write("No se pudo comprimir %s\n" % ruta_archivo)
                            limpiar_temporal(temp_dir, log)
                            
            # Si se ha creado el nuevo fichero y su longitud es aproximadamente igual al fichero original, lo borro
            log.write("Si se ha creado el nuevo fichero y su longitud es aproximadamente igual al fichero original, lo borro\n")
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0 and os.path.getsize(file_path) > os.path.getsize(ruta_nueva):
                os.remove(file_path)
                log.write("Borro %s\n" % file_path)
            else:
                # Borro el nuevo fichero y renombro el antiguo como era originalmente y salgo con error
                log.write("No se ha borrado %s\n" % file_path)
                os.remove(ruta_nueva)
                os.rename(file_path, nombre_archivo)
                exit(1)
                

    log.write("Fin del bucle\n")
'''
comento esto porque hay que probar todo lo anterior

    # Renombro los ficheros usando la configuración de COMICS
    log.write("Renamer del comic: %s\n" % input_dir)
    os.system("call \"C:\\Program Files (x86)\\ReNamer\\ReNamer.exe\" /silent /rename \"COMICS\" %s" % input_dir)

    # Scrapping del comic en comicvine
    log.write("Scrapping del comic\n")
    os.system("call \"%s\\comictagger.exe\" -R -s -f -o -t cr %s" % (prog_dir, input_dir))
    os.system("call \"%s\\comictagger.exe\" -R -r -t cr %s" % (prog_dir, input_dir))
'''

    log.write("exit 0\n")
