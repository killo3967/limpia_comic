import os
import shutil
import sys
import stat
import zipfile
import patoolib



# Defino las variables generales
if not len(sys.argv) > 1:
    input_value = r"D:\COMICS_MALOS"
else:
    input_value = sys.argv[1]




if os.path.isdir(input_value):
  # Es directorio
  input_dir = input_value
else:
  # Es archivo
  input_dir = os.path.dirname(input_value)

# Compruebo que el directorio no esta vacion
if len(os.listdir(input_dir)) == 0:
    print("DIRECTORIO VACIO")
    sys.exit(1)
          

# Compruebo que existen ficheros de comics
extensiones = ['.cbr', '.cbz']
for raiz, dirs, archivos in os.walk(input_dir):
  for archivo in archivos:
    if archivo.endswith(extensiones):
      print(f'Encontrado {archivo} en {raiz}')
      encontrado = True
      sys.exit(0) 

  
# Modo whatif es el modo a prueba, solo es un modo de deteccion de fallos
whatif_mode = True  

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

# Creo directorio de log si no existe
try:
     os.makedirs(log_dir)
except OSError:
    pass

# Creo directorio temporal si no existe
try:
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir)
except OSError:
    pass

# Elimino el directorio temporal y lo creo de nuevo
def limpiar_temporal(temp_dir):
    escribir_log("Elimino el directorio temporal y lo creo de nuevo")
    shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir)

def descomprimir_archivo(ruta_archivo, directorio_salida):
    patoolib.extract_archive(ruta_archivo, verbosity=0, outdir=directorio_salida )
    

def comprimir_directorio(ruta_directorio, archivo_salida):
    # Hay que terminar con un slash para que patoollib lo tome como una ruta relativa
    ruta_directorio = ruta_directorio + '\\'
    # creo una tupla de 1 elemento para pasar el directorio a comprimir
    archivos = (ruta_directorio,)
    patoolib.create_archive(archivo_salida, archivos, verbosity=-1, program=None, interactive=False)


def escribir_log(mensaje):
    with open(log_file, 'a') as log:
        log.write(f'{mensaje}\n')
    print(f'{mensaje}')
    
    
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
            print(f'\tBorrando {ruta_ds_store}')
        except OSError:
            pass
    
    ruta_macosx = os.path.join(directorio, '__MACOSX')
    if os.path.exists(ruta_macosx):
        print(f'\tBorrando {ruta_macosx}') 
        try:
            shutil.rmtree(ruta_macosx)
        except OSError:
            pass

# Borro los ficheros pequeños excepto los xml
def borrar_ficheros_pequeños(directorio):
    for root, dirs, files in os.walk(directorio):
        for file_name in files:
            file_path_temp = os.path.join(root, file_name)
            if os.path.getsize(file_path_temp) < 2048 and not file_path_temp.endswith('.xml'):
                os.remove(file_path_temp)
                escribir_log("""\tBorro %s""" % file_path_temp)

# Borro todas las extensiones que no sean de imagenes o xml
def borrar_extensiones_prohibidas(directorio):
    extensiones_permitidas = [".bmp", ".jpg", ".png", ".wep", ".xml"]
    for root, dirs, files in os.walk(directorio):
        for file_name_temp in files:
            file_p = os.path.join(root, file_name_temp)
            if not any(file_p.endswith(ext) for ext in extensiones_permitidas):
                try: 
                    os.remove(file_p)
                    escribir_log("\tBorro %s" % file_p)
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
                            escribir_log("\tBorro %s" % file_name_temp)
                        except PermissionError:
                            escribir_log("\tNo se pudo borrar %s" % file_path_temp)
                            limpiar_temporal(temp_dir)
                            exit(1)


def crear_lista_ficheros(directorio):
    # Primero me aseguro que se borra lista.txt
    ruta_archivo = os.path.join(prog_dir, 'lista.txt')
    try:
        os.remove(ruta_archivo)
        print('\tArchivo eliminado')
    except OSError as e:
        print(f'\tError eliminando archivo: {e.strerror}')

    # Ahora creo la nueva lista de ficheros 
    with open(os.path.join(prog_dir, 'lista.txt'), 'w') as lista:
        for raiz, dirs, archivos in os.walk(directorio):
            for archivo in archivos:
                if archivo.endswith('.cbz') or archivo.endswith('.cbr'):
                    ruta_completa = os.path.join(raiz, archivo)
                    lista.write(ruta_completa + '\n')
                    escribir_log(ruta_completa)
                    lista.flush()

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

# Miro si el directorio de entrada contine algun archivo con extension cbr o cbz
# Si no lo contiene, termino el programa
extensiones = ['.cbr', '.cbz']
contiene_archivos = False
with os.scandir(input_dir) as it:
  for entrada in it:
    if not (entrada.is_file() and entrada.path.endswith(extensiones)):
        exit(1)

escribir_log("FICHEROS A PROCESAR:")

# Creo el fichero de lista de ficheros
escribir_log("Creando la lista de comics a procesar")
crear_lista_ficheros(input_dir)

# Bucle para procesar cada fichero
escribir_log("Inicio un bucle para procesar cada fichero")
escribir_log("#####################################################################################")
with open(os.path.join(prog_dir, "lista.txt"), "r") as lista:
    for file_path in lista:
        file_path = file_path.strip()
        escribir_log("COMIC A PROCESAR: %s" % file_path)

        # Extraigo el comic en el directorio temporal
        escribir_log("Extraigo el comic en el directorio temporal")
        descomprimir_archivo(file_path, temp_dir)

        # Comprobar que no hay comics dentro del comic        
        escribir_log("Miro en el directorio temporal si hay algun fichero con extension cbr o cbz")
        extensiones_comics = ['.cbr', '.cbz']
        encontrado = False
        for raiz, dirs, archivos in os.walk(temp_dir):
            for archivo in archivos:
                extension = os.path.splitext(archivo)[1]
                if extension in extensiones_comics:
                    print(f'Encontrado archivo {archivo} con extensión no permitida')
                    encontrado = True
                    break
            if encontrado:
                break
        if not encontrado:
            print('No se encontraron archivos con extensiones .cbr o .cbz')          

        # Cambio los atributos por si acaso alguno trae algo raro como oculto o de sistema
        escribir_log("Cambio los atributos por si acaso alguno trae algo raro como oculto o de sistema")
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
        comic_antiguo = os.path.join(directorio, nuevo_nombre)
        shutil.move(file_path, comic_antiguo)
        escribir_log("Renombro fichero de %s -> %s" % (nombre_archivo, nuevo_nombre))


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
        if os.path.exists(file_path) and os.path.getsize(file_path) > 50000 and ( os.path.getsize(file_path)*1.2 <= os.path.getsize(comic_antiguo) or os.path.getsize(file_path)*1.2 >= os.path.getsize(comic_antiguo)):
            os.remove(comic_antiguo)
            escribir_log("Se ha creado el nuevo fichero de comic")
        else:
            # Borro el nuevo fichero y renombro el antiguo como era originalmente y salgo con error
            escribir_log("No se ha podido borrar el comic antiguo. Restaurando: %s" % file_path)
            # Borro el nuevo
            os.remove(file_path)
            # renombro el antiguo.
            os.rename(comic_antiguo, file_path)
            exit(1)
        
        limpiar_temporal(temp_dir)
        escribir_log("#####################################################################################")
        

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
