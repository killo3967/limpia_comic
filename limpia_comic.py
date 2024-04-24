import os
import shutil
import sys
import stat
import zipfile
import patoolib



# Defino las variables generales
if not len(sys.argv) > 1:
    input_value = r"D:\COMICS_MALOS\COMIC_MALO.cbz"
else:
    input_value = sys.argv[1]

if os.path.isdir(input_value):
  # Es directorio
  input_dir = input_value
else:
  # Es archivo
  input_dir = os.path.dirname(input_value)
  
  

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
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir)
except OSError:
    pass

'''
Deletes the temporary directory and creates it again.
This function is used to clean up the temporary directory used by the script.
It first removes the entire directory tree using `shutil.rmtree()`, ignoring any errors that may occur.
Then, it recreates the directory using `os.makedirs()`.
This ensures that the temporary directory is in a clean state before the script starts processing any files.
'''
def limpiar_temporal(temp_dir):
            # Elimino el directorio temporal y lo creo de nuevo
            escribir_log("Elimino el directorio temporal y lo creo de nuevo")
            shutil.rmtree(temp_dir, ignore_errors=True)
            os.makedirs(temp_dir)

def descomprimir_archivo(ruta_archivo, directorio_salida):
    patoolib.extract_archive(
        ruta_archivo,
        outdir=directorio_salida
        )
    

def comprimir_directorio(ruta_directorio, archivo_salida):
  nombres_archivos = os.listdir(ruta_directorio)
  archivos = [os.path.join(ruta_directorio, nombre) for nombre in nombres_archivos]
  patoolib.create_archive(
      archivo_salida,  
      archivos, 
      format="zip",
      compression=zipfile.ZIP_STORED
  )


def escribir_log(mensaje):
    with open(log_file, 'a') as log:
        log.write(f'{mensaje}\n')
    print(f'{mensaje}\n')
    
def aplanar_directorio(directorio):

  # Mover archivos al directorio raíz
  for raiz, dirs, archivos in os.walk(directorio):
    for archivo in archivos:
      ruta_original = os.path.join(raiz, archivo)
      ruta_destino = os.path.join(directorio, archivo)
      shutil.move(ruta_original, ruta_destino)

  # Eliminar directorios vacíos    
  for raiz, dirs, archivos in os.walk(directorio, topdown=False):
    if not os.listdir(raiz):
      os.rmdir(raiz)
    
def cambiar_atributos(directorio):
  for raiz, dirs, archivos in os.walk(directorio):
    for nombre in archivos + dirs:
      ruta = os.path.join(raiz, nombre)
      atributos = os.stat(ruta).st_file_attributes

      # Quitar atributos HRS
      atributos &= ~stat.FILE_ATTRIBUTE_HIDDEN
      atributos &= ~stat.FILE_ATTRIBUTE_READONLY
      atributos &= ~stat.FILE_ATTRIBUTE_SYSTEM

      # Asignar permisos lectura y escritura
      atributos |= stat.FILE_ATTRIBUTE_ARCHIVE
      atributos |= stat.FILE_ATTRIBUTE_NORMAL

      os.chmod(ruta, atributos)


def borrar_directorios_MACOSX(directorio):
    ruta_ds_store = os.path.join(directorio, '.DS_Store')
    if os.path.exists(ruta_ds_store):
        try: 
            shutil.rmtree(ruta_ds_store)
            print(f'Borrando {ruta_ds_store}')

        except OSError:
            pass
    
    ruta_macosx = os.path.join(directorio, '__MACOSX')
    if os.path.exists(ruta_macosx):
        print(f'Borrando {ruta_macosx}') 
        try:
            shutil.rmtree(ruta_macosx)
        except OSError:
            pass

def borrar_ficheros_pequeños(directorio):
    for root, files in os.walk(directorio):
            for file_name in files:
                file_path_temp = os.path.join(root, file_name)
                if os.path.getsize(file_path_temp) < 2048:
                    os.remove(file_path_temp)
                    escribir_log("Borro %s" % file_path_temp)

def borrar_extensiones_prohibidas(directorio):
    extensiones_permitidas = [".bmp", ".jpg", ".png", ".wep", ".xml"]
    for root, files in os.walk(directorio):
        for file_name_temp in files:
            file_path_temp = os.path.join(root, file_name_temp)
            if not any(file_name.endswith(ext) for ext in extensiones_permitidas):
                try: 
                    os.remove(file_path_temp)
                    escribir_log("Borro %s" % file_path_temp)
                except PermissionError:
                    pass

def borrar_cadenas_prohibidas(directorio):
    with open(patrones_prohibidos_file, "r") as cadenas_prohibidas:
        for cadena in cadenas_prohibidas:
            cadena = cadena.strip()
            for root, dirs, files in os.walk(directorio):
                for file_name_temp in files:
                    file_path_temp = os.path.join(root, file_name_temp)
                    if cadena in file_name_temp:
                        try:
                            os.remove(file_path_temp)
                            escribir_log("Borro %s" % file_path)
                        except PermissionError:
                            escribir_log("No se pudo borrar %s" % file_path_temp)
                            limpiar_temporal(temp_dir)
                            exit(1)


escribir_log("###############################################################################")
escribir_log("###############################################################################")
escribir_log("Defino las variables")
escribir_log("FICHERO DE LOG: %s" % log_file)

# Borro los directorios de restos
escribir_log("Empiezo limpiando todos los restos anteriores")
try:
    os.remove("lista.txt")
except OSError:
    pass

shutil.rmtree(temp_dir, ignore_errors=True)
os.makedirs(temp_dir)

# Imprimo los datos iniciales
escribir_log("Imprimo los datos iniciales")
# os.makedirs(os.path.join(prog_dir, "temp"))

# Creo la lista de ficheros
escribir_log("DIRECTORIO DE ENTRADA: %s" % input_dir)
escribir_log("FICHEROS A PROCESAR:")

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
                escribir_log(ruta_completa)
                lista.flush()
        

# Bucle para procesar cada fichero
escribir_log("Inicio un bucle para procesar cada fichero\n")
with open(os.path.join(prog_dir, "lista.txt"), "r") as lista:
    for file_path in lista:
        file_path = file_path.strip()
        escribir_log("COMIC A PROCESAR: %s" % file_path)

        # Extraigo el comic en el directorio temporal
        escribir_log("Extraigo el comic en el directorio temporal")
        descomprimir_archivo(file_path, temp_dir)
        
        ''' Miro en el directorio temporal si hay algun fichero con extension cbr o cbz
        y si existe alguno es que ese comic tiene dentro otros comics y debe mirarse con
        detenimmient. Seguro que sera un fichero rar o zip
        '''
        escribir_log("Miro en el directorio temporal si hay algun fichero con extension cbr o cbz")
        for archivo in os.listdir(temp_dir):
            nombre, extension = os.path.splitext(archivo)
            if extension in [".cbr", ".cbz"]:
                escribir_log("Se encontró comics dentro del comic. No se procesara")
                limpiar_temporal(temp_dir)
                sys.exit(1)            

        # Cambio los atributos por si acaso alguno trae algo raro como oculto o de sistema
        escribir_log("Cambio los atributos por si acaso alguno trae algo raro como oculto o de sistema\n")
        cambiar_atributos(temp_dir)
        
        # Aplanar directorio temporal, es decir muevo todos los ficheros del directorio temporal y 
        # sus subdirectorios al raiz del temporal y borro los subdirectorios
        escribir_log("Aplanar directorios")
        aplanar_directorio(temp_dir)
        
        # Borro directorio ".DS_Store" y "__MACOSX" de forma recursiva si es que aun existen
        escribir_log("Borro directorio .DS_Store y __MACOSX")
        borrar_directorios_MACOSX(temp_dir)
        
        # Borro todos los ficheros con un tamaño menor a 2k
        escribir_log("Borro todos los ficheros con un tamaño menor a 2k")
        borrar_ficheros_pequeños(temp_dir)

        # Elimino todos los ficheros que no sean de las extensiones permitidas
        escribir_log("Elimino todos los ficheros que no sean de las extensiones permitidas")
        borrar_extensiones_prohibidas(temp_dir)
                    
        # Elimino los ficheros que contienen cadenas prohibidas
        escribir_log("Elimino las imagenes que contienen cadenas prohibidas")
        borrar_cadenas_prohibidas(temp_dir)

        # Renombro el fichero antiguo antes de borrarlo
        directorio = os.path.dirname(file_path)
        nombre_archivo = os.path.basename(file_path)
        nuevo_nombre = nombre_archivo + ".bak"
        ruta_nueva = os.path.join(directorio, nuevo_nombre)
        os.rename(file_path, ruta_nueva)


        # Comprimo todos los ficheros de nuevo en modo store con la extensión cbz
        escribir_log("Comprimo todos los ficheros de nuevo en modo store con la extensión cbz")
        try:
            comprimir_directorio(temp_dir, file_path)
        except:
            # Si no se puede comprimir hay que limpiar el temporal y salir con error
            escribir_log("No se pudo comprimir %s" % file_path)
            limpiar_temporal(temp_dir)
            exit(1)
                        
        # Si se ha creado el nuevo fichero y su longitud es aproximadamente igual al fichero original, lo borro
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0 and os.path.getsize(file_path) > os.path.getsize(ruta_nueva):
            os.remove(file_path)
            escribir_log("Se ha creado el nuevo fichero comic")
        else:
            # Borro el nuevo fichero y renombro el antiguo como era originalmente y salgo con error
            escribir_log("No se ha podido borrar el comic antiguo. Restaurandolo%s" % file_path)
            # Borro el nuevo
            os.remove(ruta_nueva)
            # renombro el antiguo.
            os.rename(file_path, nombre_archivo)
            exit(1)
            

escribir_log("Fin del bucle\n")
exit()
'''
comento esto porque hay que probar todo lo anterior

    # Renombro los ficheros usando la configuración de COMICS
    escribir_log("Renamer del comic: %s\n" % input_dir)
    os.system("call \"C:\\Program Files (x86)\\ReNamer\\ReNamer.exe\" /silent /rename \"COMICS\" %s" % input_dir)

    # Scrapping del comic en comicvine
    escribir_log("Scrapping del comic\n")
    os.system("call \"%s\\comictagger.exe\" -R -s -f -o -t cr %s" % (prog_dir, input_dir))
    os.system("call \"%s\\comictagger.exe\" -R -r -t cr %s" % (prog_dir, input_dir))
'''

escribir_log("exit 0\n")
