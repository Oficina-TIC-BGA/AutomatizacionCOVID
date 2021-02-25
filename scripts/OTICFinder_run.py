## importart librerias 
# para recibir los parametros
import argparse
import sys
import configparser
# expresiones regulares
import re
# manejo de datos
import pandas as pd
from collections import defaultdict
# manejo de geoposicionamiento
import geopy
from geopy.geocoders import ArcGIS, MapBox
from geopy.extra.rate_limiter import RateLimiter
# manejo de poligonos
import shapely.wkt
import shapely.speedups
from shapely.geometry import Point
from descartes.patch import PolygonPatch
from shapely.geometry.polygon import Polygon
# manejo de operaciones 
import numpy as np
# unicode
import unicodedata
# warning
import warnings
warnings.filterwarnings('ignore')
# barras de progreso
import tqdm
from tqdm import tqdm
tqdm.pandas()

####################### FUNCIONES ##############################
# PARA LIMPIAR DIRECCIONES
def filtering(dir):
    dir = str(dir)
    #print('Inicial {}'.format(dir))
    # definir las palabras comunes para tratar de estandarizar las direcciones
    # TODO: Resumir expresiones regulares
    common_words = {} 
    common_words['carrera'] = ['carrear\s','carrea\s','\bK','KRA', 'CDRA\s','CRA', 'KR', '\s*CR\s', '\s*carre\s','ARRERA', 'CARRRERA', 'CARRRA', 'car\s','CRR','CARERRA', '\s*CARR\s', '\s*carr\s', '\s*CRARREA\s','CARRERA']
    common_words['calle'] = ['CLL', 'CL', 'CLEE', '\s*CALL\s','\s*CC\s', 'CLLE', 'cale\s']
    common_words['diagonal'] = ['DIAG\s', 'DIAGONAL', 'DG', '\sDIG\s']
    common_words['transversal'] = ['TRANSVERSAL','trns\s', '\sTR\s','TRV','TRANSV', 'TV', 'TRANVERSAL', 'TRANSV', 'TRANSSV\s','TRASVERSAL', 'TRANV', 'TANSVERSAL', 'TRANVS', '\s*trans\s']
    common_words['numero'] = ['\bNUM\b', '\sNUM\s', 'NUMERO', 'NMERO', 'NÚMERO', '#', '\sNO\s', 'NRO', 'Nª','Nº','N°']
    common_words['circunvalar'] = ['CIRCUMBALAN\s','CIRCUMBALAR\s','circunvalara','VIRCUNVALAR','CIRCUNVALAR', '\sCIRC\s', '\sCIR\s', 'CCV', 'CV', 'circunvalarv', 'CIRCCUN\s', 'circircunvalar\s']
    common_words['avenida'] = ['AV\s+', 'AVENIDA', '\sAVD\s','AVDA', 'AVEN\s', 'avn', '\svda\s', '\savd\s']
    common_words['quebradaseca'] = ['qdaseca', 'quebrada seca', 'quebrada']
    common_words['edificio'] = ['edif*\s', 'edf', 'edificio', '\sedi\s']
    common_words['torre'] = ['tprre\s','\storr*\s', '\stor\s', '\sto\s', '\str\s', '\st\s']
    common_words['barrio'] = ['\sbrr', '\sbario\s','barrio','BARRIO', '\sbr\s', '\sbarri\s','\sbrr\s']
    common_words['apartamento'] = ['\sAPTO\s', '\sAPP\s' ,'APTO ','\sAPTO', 'ap\s', 'aparatamento','apartamento*', 'apar\s','apart\s', 'APRO\s', '\sapato', '\sapt', '\bAPTO\b', '\saparta\s', '\sapartame\s']
    common_words['bloque'] = ['BLOQUE', '\sblo\s', '\s*bloq\s']
    common_words['sector'] = ['SECTOR', '\ssect\s', '\ssec\s'] 
    common_words['kilometro'] = ['KM\s*', 'KILOMETRO', 'KM ']
    common_words['vereda'] = ['\s*VDA\s', '\s*VER\s', '\sBEREDA\s']
    common_words['urbanizacion'] = ['URBANIZAC\s', 'URBANIZACION', 'URBANIZACIÓN', 'urb']
    common_words['manzana'] = ['\s*MANZANA\s','\s*mz\s*\d+', '\s*mz\s', '\smz\s*[a-z]', '\s*manza\s', '\s*manz\s']

    # definir los patrones con las expresiones regulares
    pattern_numeros = re.compile(r'\d\s*[A-Z]\s*#', re.IGNORECASE)
    pattern_carrera = re.compile(r'|'.join(common_words['carrera']), re.IGNORECASE)
    pattern_calle = re.compile(r'|'.join(common_words['calle']), re.IGNORECASE)
    pattern_diagonal = re.compile(r'|'.join(common_words['diagonal']), re.IGNORECASE)
    pattern_transversal = re.compile(r'|'.join(common_words['transversal']), re.IGNORECASE)
    pattern_num = re.compile(r'|'.join(common_words['numero']), re.IGNORECASE)
    pattern_circunvalar = re.compile(r'|'.join(common_words['circunvalar']), re.IGNORECASE)
    pattern_avenida = re.compile(r'|'.join(common_words['avenida']), re.IGNORECASE)
    pattern_quebradaseca = re.compile(r'|'.join(common_words['quebradaseca']), re.IGNORECASE)
    pattern_edificio = re.compile(r'|'.join(common_words['edificio']), re.IGNORECASE)
    pattern_torre = re.compile(r'|'.join(common_words['torre']), re.IGNORECASE)
    pattern_apartamento = re.compile(r'|'.join(common_words['apartamento']), re.IGNORECASE)
    pattern_bloque = re.compile(r'|'.join(common_words['bloque']), re.IGNORECASE)
    pattern_sector = re.compile(r'|'.join(common_words['sector']), re.IGNORECASE)
    pattern_urbanizacion = re.compile(r'|'.join(common_words['urbanizacion']), re.IGNORECASE)
    pattern_kilometro = re.compile(r'|'.join(common_words['kilometro']), re.IGNORECASE)
    pattern_manzana = re.compile(r'|'.join(common_words['manzana']), re.IGNORECASE)
    pattern_guion = re.compile(r'-|\.|·|º|°')#|Nª|º|°
    pattern_nume2 = re.compile(r'\sNO\d|\sNUM\d', re.IGNORECASE)
    pattern_nume3 = re.compile(r'\dNO\d|\dNUM\d', re.IGNORECASE)
    pattern_final = re.compile(r'barrio|primer piso\s*|peatonal\s*\d+|manzana\s*\d+|t\d+|casa\s*\d+|piso\s*\d+|apartamento\s*\d+|torre\s*\d+', re.IGNORECASE)
    pattern_final2 = re.compile(r'conjunto residencial|torre\s[a-z]*|edificio|edificio\s*\d+|bloque\s*\d+|apartamento|manzana\s*\d+|manzana\s*[a-z]|sector\s*\d+', re.IGNORECASE)
    pattern_final3 = re.compile(r'conjunto|conj|conjunto\s*residen|segundo piso|sin dato|ninguno|direccion|local\s*\d*|piso|sector\s*[a-z]|manzana', re.IGNORECASE)
    pattern_final4 = re.compile(r'2DO|1RO|1ERO|NO ENCONTRADO|ENTRADA|PI\s+\d*|ninguno|ninguna|urbanizacion|casa\s[a-z]', re.IGNORECASE)
    #pattern_final = re.compile(r'(\s[a-z\s*]*\s*)', re.IGNORECASE)
    pattern_barrio = re.compile(r'|'.join(common_words['barrio']), re.IGNORECASE)
    pattern_std = re.compile(r'carrera|calle|avenida|diagonal|transversal|circunvalar')
    # ejecutar las expresiones regulares
    
    # Este patron separa los numeros pegados
    match_specials_num = re.search(pattern_nume2, dir)
    if match_specials_num:
        found_pattern = match_specials_num.group()
        dir = dir.replace(found_pattern[:-1], ' ')  
    # Este patron separa los numeros pegados
    match_specials_num3 = re.search(pattern_nume3, dir)
    if match_specials_num3:
        found_pattern3 = match_specials_num3.group()
        dir = dir.replace(found_pattern3[1:-1], ' ')
    # elimina signos especiales, guiones, grados, etc...
    match_specials = re.finditer(pattern_guion, dir)
    if match_specials:
        for match_guion in match_specials:
            found_pattern = match_guion.group()
            dir = dir.replace(found_pattern, ' ')
    # pega las letras de las calles si tiene
    match_numeros = re.search(pattern_numeros, dir)
    if match_numeros:
        x0, xt = match_numeros.span()
        if dir[x0+1]==' ':
            dir = dir[:x0+1] + dir[x0+1:].replace(' ','',1) 

    # ejecutar los patrones intermedios
    # cambia los patrones por su forma correcta y agrega espacios para separar        
    patterns = [pattern_carrera, pattern_calle, pattern_diagonal, pattern_transversal, pattern_num, pattern_circunvalar, 
                pattern_avenida, pattern_quebradaseca, pattern_edificio, pattern_torre, pattern_apartamento, pattern_bloque, pattern_sector,
                pattern_kilometro, pattern_barrio, pattern_urbanizacion, pattern_manzana]
    for pattern, p in zip(patterns,[' carrera ', ' calle ', ' diagonal ', ' transversal ', ' ', 'circunvalar', 'avenida', 'quebradaseca', 'edificio',
                                    ' torre ', ' apartamento ', ' bloque ', ' sector ', ' kilometro ', ' barrio ', ' urbanizacion ', ' manzana ']):
        matches = re.finditer(pattern, dir)
        if matches:
            for match in matches:
                found_pattern = match.group()
                dir = dir.replace(found_pattern, p)
                if p != ' ':
                    pattern_tem = re.compile(p)
                    found_tem = re.search(pattern_tem, dir)
                    #print('tem',found_tem)
                    try:
                        if found_tem and dir[found_tem.end()+1]!= ' ':
                            dir = dir[:found_tem.end()] + ' ' + dir[found_tem.end():]
                    except:
                        pass        
            dir = dir.strip().replace("  ", " ").replace("  ", " ").lower() 
    # Encuentra todos los patrones y los elimina 
    for pat in [pattern_final, pattern_final2, pattern_final3, pattern_final4]:
        matches_finales = re.finditer(pat, dir) 
        if matches_finales:
            for match_final in matches_finales:
                found_pattern = match_final.group()
                dir = dir.replace(found_pattern, '')
        else:    
            pass  
    dir = dir.strip().replace("  ", " ").replace("  ", " ")    
    return dir 

###### COLOCAR BARRIO - MUNICIPIO
def pattern_row(row, dir):
    # Revisar que no este nulo los campos
    total = []
    for column in ['BARRIO','SECTOR', 'EDIFICIO', 'CONJUNTO']: 
        if isinstance(row[column], str): # si no es vacio
            total = total + [j.strip() for j in row[column].strip().split(',')]   
    if len(total)>0: 
        pattern = re.compile(r'|'.join([i for i in total]), re.IGNORECASE)
        result = re.findall(pattern, dir)
    else:
        result = total    
    return result

def buscar_pertenencia(dir, df_bucaramanga, df_floridablanca, df_giron):
    total_asign = defaultdict(list)
    for c, df_c in zip(['bucaramanga', 'floridablanca', 'giron'],[df_bucaramanga, df_floridablanca, df_giron]):
        # paso 1: Unir columnas SECTOR - CONJUNTO - EDIFICIO para cada barrio y buscar
        for index, row in df_c.iterrows():
            founded = pattern_row(row, dir)
            if len(founded)>0:
                # esto quiere decir que hubo al menos un concidencia para ese barrio
                # asignar el barrio a la ciudad
                total_asign[c].append(row.BARRIO)
    return total_asign

def where_is(dir, data, df_bucaramanga, df_floridablanca, df_giron, pattern_general):
    # ESTRUCTURA:
    # 1. Identificar si encuentra alguna residencia, conjunto, urbanizacion o edificios y asignar el barrio
    # 1.1 si asigna el barrio asigna inmediatamente la ciudad y adicionalmente guarda el barrio y comuna
    # 2. si no encuentra ninguno intenta encontrar el barrio para determinar la ciudad y la comuna, tambien se guardan
    # 3. si no encuentra ningun barrio intenta encontrar otra ciudad y guarda vacio en el resto de variables
    # 4. si no ocurre ninguna de las anteriores coloca bucaramanga por defecto  
    # la variables a añadir en el dataframe son comuna_dir, barrio_dir, ciudad_dir
    # Recorrer todas las ciudad a incluir del area metropolitana
    # Va a contener todos las coincidencias en todos los municipios coinciderados.
    # si hay barrio de base de datos
    #print(dir)
    if dir != 'nan':
        pre_barrio = data.loc[data.dir_filtradas.str.lower()==dir, 'bar_ver_'].isnull().values[0]
        # buscar en que barrios y ciudades puede haber una coincidencia
        total_asign = buscar_pertenencia(dir, df_bucaramanga, df_floridablanca, df_giron)            
        # Buscar si hay algun patron para otra ciudad)
        # construir el patron para buscar ciudades fuera del area metropolitana consideradas
        matches_found = re.findall(pattern_general, dir)
        # Si las dos listas estan vacias quiere decir que posiblemente viene solo la direccion
        # buscar si hay informacion adicional
        pre_barrio_exist = None
        if ~pre_barrio: # si no es null
            pre_barrio_exist = data.loc[data.dir_filtradas.str.lower()==dir, 'bar_ver_'].values[0]
            #print('Base de dato ...',pre_barrio_exist)
            if isinstance(pre_barrio_exist, int):
                pre_barrio = True
                
        # en caso de tener mas columnas aqui se seleccionarian los valores

        # finalmente tomar una decision en que barrio y ciudad colocar 
        if len(total_asign) == 1:
            # si las otras fuentes de datos estan vacias colocar fijo esta opción
            ciudad = str(np.squeeze(list(total_asign.keys())))
            if len(matches_found) == 0 and pre_barrio:
                dir = dir + str(', '+ciudad.lower())
                #print('Opción 1 {}'.format(dir))

            elif len(matches_found) == 0 and ~pre_barrio:
                # hay informacion desde base de datos
                if ciudad.lower()==pre_barrio_exist.strip().lower():
                    # esta comparacion deberia ser ciudad ciudad y barrio barrio pero no viene toda la info
                    dir = dir + str(', '+ciudad.lower()) 
                    #print('Opción 2 {}'.format(dir))
                    #print('opcion 2')
                else:
                    # quizas si viene un barrio en base de datos que coincida con un barrio encontrado
                    if pre_barrio_exist.strip().lower() in total_asign[ciudad]:
                        dir = dir + str(', '+ciudad.lower())
                        #print('Opción 3 {}'.format(dir))

                    else: # en ultimas colocar las dos
                        if len(re.findall(re.compile(pre_barrio_exist.strip(), re.IGNORECASE), dir))==0: # para que no repita información
                            #print(dir)
                            dir = dir + str(', '+pre_barrio_exist.lower() + ', '+ciudad.lower())  
                            #print('Opción 4 {}'.format(dir))

                        else:
                            dir = dir + str(', '+ciudad.lower())  
                            #print('Opción 4 b {}'.format(dir)) 
            
            elif len(matches_found) != 1 and ~pre_barrio: # hay info en las 3 opciones
                if matches_found[0].lower()==pre_barrio_exist.strip().lower()==ciudad[0].lower():
                    #print(dir)
                    dir = dir + str(', '+ciudad.lower())
                    #print('Opción 5 {}'.format(dir))
                        
                elif matches_found[0].lower()==pre_barrio_exist.strip().lower(): #si la diferente es lo de la direccion ignorar
                    #print(dir)
                    dir = dir + str(', '+pre_barrio_exist.lower())    
                    #print('Opción 6 {}'.format(dir))

            else:
                pass        

        elif len(total_asign) > 1: # # TODO decidir que hacer con multiples coincidencias
            # analizar si hay algo en base de datos y en coincidencias
            ciudades = list(total_asign.keys())
            if len(matches_found) != 0 and pre_barrio:
                # seleccionar el que mas veces se repite en las listas
                names, counts = np.unique(ciudades, return_counts=True)
                votos = names[np.argsort(counts)][::-1] # ordenar mayor a menor
                if len(re.findall(re.compile(votos[0].lower().strip(), re.IGNORECASE), dir))==0: # para no repetir info
                    #print(dir)
                    dir = dir + str(', '+votos[0].lower())    
                    #print(total_asign, ciudades)
                    #print('Opción 9 multi {}'.format(dir))

            elif len(matches_found) != 0 and ~pre_barrio:
                # seleccionar una opcion de las ciudades que encontro
                names, counts = np.unique(ciudades+matches_found, return_counts=True)
                votos = names[np.argsort(counts)][::-1] # ordenar mayor a menor
                seleccion = votos[0]#
                if ~(seleccion.lower()==pre_barrio_exist.lower()):
                    dir = dir + str(', '+pre_barrio_exist+', '+seleccion.lower()) 

                else:
                    dir = dir + str(', '+seleccion.lower())   

            elif len(matches_found) == 0 and pre_barrio:
                names, counts = np.unique(ciudades+matches_found, return_counts=True)
                votos = names[np.argsort(counts)][::-1] # ordenar mayor a menor
                seleccion = votos[0]
                dir = dir + str(', '+seleccion.lower())

            else:
                seleccion = np.random.choice(ciudades,1)
                dir = dir + str(', '+seleccion[0].lower())

        else:# cuando es cero
            if len(matches_found) == 0 and pre_barrio: # No hay ninguna información
                if dir!='nan' and dir!='sin informacion' and len(dir)>=3:
                    dir = dir + str(', bucaramanga')
                    #print('Opción 7 {}'.format(dir))
                else :
                    dir = np.nan    
                    #print('Opción nan {}'.format(dir))
            elif len(matches_found) == 0 and ~pre_barrio: # colocar lo que esta desde base de datos
                # esta opcion se deberia considerar eliminar porque puede ser que no hay ningun patron
                # debido a que estan mal escritos los barrios
                if len(re.findall(re.compile(pre_barrio_exist.strip(), re.IGNORECASE), dir))==0:
                    # buscar esa info a que ciudad pertenece
                    ciudad_result = buscar_pertenencia(pre_barrio_exist.strip(), df_bucaramanga, df_floridablanca, df_giron)   
                    if len(ciudad_result) == 1:
                        # si las otras fuentes de datos estan vacias colocar fijo esta opción
                        ciudad_result = str(np.squeeze(list(ciudad_result.keys())))
                        if pre_barrio_exist.strip().lower() != ciudad_result.strip().lower():
                            dir = dir + str(', '+pre_barrio_exist.lower() + ', '+ciudad_result)
                        else:
                            # buscar si hay una ciudad ya en la direccion
                            dir = dir + str(', '+pre_barrio_exist.lower())
                            matches_found = re.findall(pattern_general, dir)
                            if len(matches_found)==0:
                                dir = dir + str(', bucaramanga')
                            #print('Opción 8 {}'.format(dir))

                    elif len(ciudad_result) > 1:
                        # TODO decidir que hacer con multiples coincidencias
                        #print(dir, ciudad_result)
                        dir = dir + str(', '+pre_barrio_exist.lower() + ', '+np.random.choice(list(ciudad_result.keys()),1)[0].lower())
                        #print('Opción 8 b: {}'.format(dir))
                    else:
                        # buscar si hay una ciudad ya en la direccion
                        dir = dir + str(', '+pre_barrio_exist.lower())
                        matches_found = re.findall(pattern_general, dir)
                        if len(matches_found)==0:
                                dir = dir + str(', bucaramanga')
                else:
                    dir = dir + str(', bucaramanga')                
    else:# se puede decir que coloque el municipio
        dir = np.nan
    #print('-->',dir)                           
    return dir

##### GEOPOSICIONAR
def search(geolocator, df_addresses):
    # filtro inicial para no buscar las direcciones vacias
    tem = df_addresses[~df_addresses.dir_filtradas.isna()]
    tem_2 = df_addresses[df_addresses.dir_filtradas.isna()] 
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    tem['location'] = tem['dir_filtradas'].progress_apply(geocode)
    tem['coordenadas'] = tem['location'].apply(lambda loc: tuple([loc.longitude, loc.latitude]) if loc else None)
    tem['longitud'] = tem['location'].apply(lambda loc: loc.longitude if loc else None)
    tem['latitud'] = tem['location'].apply(lambda loc: loc.latitude if loc else None)
    tem['respuesta'] = tem['location'].apply(lambda loc: loc.raw if loc else None)
    del tem['location']

    return pd.concat([tem, tem_2]).sort_index() 

def buscar_barrio(path_bucaramanga,
                path_floridablanca,
                path_giron,
                path_piedecuesta,
                pattern_general,
                arcgis):
    
    def remove_accents(input_str):
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

    def ciudad(x, pattern_general):
        if isinstance(x, dict):
            r = x['address']
            match_found = re.findall(pattern_general, remove_accents(r))
            if len(match_found) >= 1:
                r = remove_accents(match_found[0])
            else:
                r = None   
        elif isinstance(x, str):    
            r = eval(x)['address']        
            match_found = re.findall(pattern_general, remove_accents(r))
            if len(match_found) >= 1:
                r = remove_accents(match_found[0])
            else:
                r = None   
        else: 
            #try:
            #    var = np.isnan(x)
            #except:
            #    pass     
            r = None   
        return r 

    def barrios(x):
        if isinstance(x, dict):
            r = x['address']
            split_r = r.split(',')
            if len(split_r)<3:
                r = None
            elif len(split_r)==4 or len(split_r)==3:
                numbers = re.compile(r'[0-9]+')
                if len(re.findall(numbers, split_r[0]))==0:
                    r = remove_accents(split_r[0].strip())
                else:
                    r = remove_accents(split_r[1].strip())   
            elif len(split_r)>=5:  
                r = remove_accents(split_r[1].strip())  
            else:
                r = None

        elif isinstance(x, str):    
            r = eval(x)['address']        
            r = x['address']
            split_r = r.split(',')
            if len(split_r)<=3:
                r = None
            elif len(split_r)==4 or len(split_r)==3:
                numbers = re.compile(r'[0-9]+')
                if len(re.findall(numbers, split_r[0]))==0:
                    r = remove_accents(split_r[0].strip())
                else:
                    r = remove_accents(split_r[1].strip())   
            elif len(split_r)>=5:  
                r = remove_accents(split_r[1].strip())  
            else:
                r = None
        else:
            r = None        
        return r         

    def score(x):
        if isinstance(x, dict):
            r = x['score']
        elif isinstance(x, str):    
            r = eval(x)['score']        
        else:
            #try: 
            #    np.isnan(x): 
            #    r = 0.0
            #except:
            #    print(x)
            r = 0.0      
        return r 

    def buscar_cercano(point_xy, datos, key='NOMBRE'):
        distancia = np.inf
        for i in range(datos.shape[0]):
            polygon_string = datos.loc[i,'geometry']
            # Extraer el nombre barrio
            name = datos.loc[i,key]
            # Convertir el poligono string al objeto poligono
            polygon = shapely.wkt.loads(polygon_string)
            distancia_pts = polygon.distance(point_xy)
            #distancia_pts = polygon.hausdorff_distance(point_xy)
    
            if distancia_pts < distancia:
                distancia = distancia_pts
                result = name  
    
        return result  

    def buscar_solo_barrio(datos_barrios, data_coords):
        # coordenadas a buscar
        #lats = data_coords.latitud.values
        #lons = data_coords.longitud.values
        coords = data_coords.coordenadas.values
        collect_intersections_bar = dict()
        ciudades_geo = data_coords.ciudad_geo.values
        ciudades_pre = data_coords.bar_ver_.values
        barrios_geo = data_coords.barrio_geo.values
        scores = data_coords.score.values
        # Recorrer  los puntos
        for j,coord in enumerate(tqdm(coords, desc='Points')): 
            if isinstance(coord, tuple):
                lon = coord[0] 
                lat = coord[1]
            else:    
                lon = np.nan
                lat = np.nan
            # seleccionar la ciudad de geoposicion
            ciudad_geo = ciudades_geo[j] 
            ciudad_pre = ciudades_pre[j]
            barrio_geo = barrios_geo[j] 
            score = scores[j]   
            # crear el punto
            point_x_y = Point(lon, lat)
            #print(point_x_y)
            # Validar que las coordenadas no esten vacias
            #print('point', j)
            collect_intersections_bar[j] = None
            if np.isnan(point_x_y)[0]!=True:
                # leer los poligonos de los barrios
                for i in range(datos_barrios.shape[0]):
                    polygon_string = datos_barrios.loc[i,'geometry']
                    # Extraer el nombre barrio
                    name = datos_barrios.loc[i,'NOMBRE']
                    # Convertir el poligono string al objeto poligono
                    polygon = shapely.wkt.loads(polygon_string)
                    if polygon.contains(point_x_y):
                        # contiene el punto totalmente
                        collect_intersections_bar[j] = name
                        break
                    elif polygon.intersects(point_x_y):
                        # opcional si se intersectan el barrio y el punto 
                        collect_intersections_bar[j] = name 
                        break
                # busca el barrio mas cercano solo si es zona metropolitana TODO
                # valida si hay algo en la ciudad de argis y que no se halla encontrado barrio por poly
                if collect_intersections_bar[j] == None and ciudad_geo != None:
                    # aqui solo mando a buscar el más cercano en bucaramanga 
                    if str(ciudad_geo).lower() == 'bucaramanga':
                        name = buscar_cercano(point_x_y, datos_barrios, key='NOMBRE') 
                        collect_intersections_bar[j] = name 
                    # esta es para usar información de base de datos    
                    elif ciudad_pre != None:
                        # si es la misma que la que da argis pero no hay nada en barrio la uso 
                        # (fuera de las ciudades que indico que busque)
                        if str(ciudad_pre).lower()==str(ciudad_geo).lower():
                            collect_intersections_bar[j] = ciudad_pre 
                        else:
                            # para colocar lo que hay en barrio geo en caso que haya discordancias
                            # pero haya un score de 100
                            if int(score)>=98 and barrio_geo==None:
                                collect_intersections_bar[j] = str(ciudad_geo).upper()         
                    # score de 0 indica que no hay datos en la direccion 
                    elif int(score)==0:
                        collect_intersections_bar[j] = ciudad_pre               
                    else:
                        collect_intersections_bar[j] = None                                   
            else:
                collect_intersections_bar[j] = None
        # crear columnas
        barrios = list()
        for p in range(data_coords.shape[0]):
            barr = collect_intersections_bar[p]
            barrios.append(barr)
        data_coords['barrio_poly'] = barrios

        return data_coords   

    # cargar archivo barrios, veredas, comunas y manzanas para cada municipio
    ####### Bucaramanga ############
    datos_bucaramanga = pd.read_csv(path_bucaramanga)
    datos_todos_bucaramanga = datos_bucaramanga[datos_bucaramanga.CATEGORIA.isin(['BARRIO', 'VEREDA','A. URBANO', 'A. RURAL'])]
    ###### Floridablanca #########################
    datos_floridablanca = pd.read_csv(path_floridablanca)
    # en floridablanca solo se va a considerar barrios
    datos_todos_floridablanca = datos_floridablanca[datos_floridablanca.CATEGORIA.isin(['BARRIO', 'VEREDA'])]
    ###### GIRON #########################
    ###### PIEDECUESTA #########################
    #---------------------------------------------
    arcgis['score'] = arcgis.respuesta.apply(lambda x: score(x))
    arcgis['ciudad_geo'] = arcgis.respuesta.apply(lambda x: ciudad(x, pattern_general))
    arcgis['barrio_geo'] = arcgis.respuesta.apply(lambda x: barrios(x))
    # buscar barrio por poligono
    # pasarle todos los barrios
    # por ahora solo le paso los de bucaramanga despues sera la concatenación de todos
    datos_todos = pd.concat([datos_todos_bucaramanga, datos_todos_floridablanca], ignore_index=True)
    result = buscar_solo_barrio(datos_todos, arcgis)

    return result 

def buscar_comuna(result, division_politica_bucaramanga): 
    comunas = []
    for bn in tqdm(result['barrio_poly'].str.lower(), desc='Comunas'):
        com = division_politica_bucaramanga.COMUNA[division_politica_bucaramanga['BARRIO'].str.lower()==bn].values
        if len(com)!=0:
            comunas.append(com[0].upper())
        else:
            if bn!=None:
                comunas.append(bn.upper())
            else:
                ## ciudad geo
                #if result.iloc[j,12].lower()!='bucaramanga':
                comunas.append(None)  
    result.COMUNA = comunas          
    return result 

def filternan(x):
    if len(str(x))<10:
        r = 'nan'
    else:
        r = x
    return r              

### DIVISION METROPOLITANA DE BUCARAMANGA
### EJECUTAR EL SCRIPT
# CAPTURAR LOS PARAMETROS DE DIRECCIONES
# de este txt sacar las direcciones de los archivos
config = configparser.ConfigParser()
config.read(sys.argv[1])
addresses_path = config['paths']['path_direcciones']
path_pol = config['paths']['path_division_politica_AMB']
path_poligonos_bucaramanga = config['paths']['path_poligonos_bucaramanga']
path_poligonos_giron = config['paths']['path_poligonos_giron']
path_poligonos_piedecuesta = config['paths']['path_poligonos_piedecuesta']
path_poligonos_floridablanca = config['paths']['path_poligonos_floridablanca']
## Leer el archivo de direcciones
df_addresses = pd.read_excel(addresses_path, sheet_name='Hoja1')
# ejecutar funcion de filtrado
print('Limpiando direcciónes ....')
df_addresses['dir_filtradas'] = df_addresses.dir_res_.apply(lambda x: filtering(x)).values
df_addresses['dir_filtradas'] = df_addresses['dir_filtradas'].apply(lambda x: filternan(x)).values
print('Limpiado de direcciones finalizado ...')
##### TODO: ESTE PASO PODRIA SER UN MODELO DE MACHINE
## identificar y colocar el municipio
division_politica_bucaramanga = pd.read_excel(path_pol, sheet_name='DIVISION_POLITICA_BUCARAMANGA')
division_politica_floridablanca = pd.read_excel(path_pol, sheet_name='DIVISION_POLITICA_FLORIDABLANCA')
division_politica_giron = pd.read_excel(path_pol, sheet_name='DIVISION_POLITICA_GIRON')
division_politica_piedecuesta = pd.read_excel(path_pol, sheet_name='DIVISION_POLITICA_PIEDECUESTA')
division_politica_general = pd.read_excel(path_pol, sheet_name='CIUDADES')
# concatenar las divisiones politicas a buscar comuna
todos_div_pol = pd.concat([division_politica_bucaramanga, division_politica_floridablanca], ignore_index=True)
# PATTERNS
# pattern en general para considerar ciudades de otros lugares del país
pattern_general_ = re.compile(r'|'.join(division_politica_general.CIUDADES.values.tolist()+['floridablanca', 'bucaramanga', 'giron']), re.IGNORECASE)
# Ejecutar la función para aplicar todos los filtros para tratar de identificar en que ciudad podria estar
df_addresses['dir_filtradas'] = df_addresses.dir_filtradas.apply(lambda x: where_is(x,
                                                                                    df_addresses,
                                                                                    division_politica_bucaramanga,
                                                                                    division_politica_floridablanca,
                                                                                    division_politica_giron,
                                                                                    pattern_general_)).values
# Guardar un archivo temporal
try:
    df_addresses.to_excel('check_point.xlsx', index=False)
except:
    df_addresses.to_csv('check_point.csv', index=False, encoding='utf-8-sig')
## Buscar coordenadas 
print('Geoposicionando ...')
# ArcGIS - la mejor opción a google
geolocator_arcgis = ArcGIS(username=None, password=None, user_agent=addresses_path.split('/')[-1], timeout=10)
# usando arcgis
arcgis = search(geolocator_arcgis, df_addresses)
try:
    arcgis.to_excel('check_point_geo.xlsx', index=False)
except:
    arcgis.to_csv('check_point_geo.csv', index=False, encoding='utf-8-sig')
    
# buscar el barrio con las coordenadas
print('Cruzando información de polígonos (barrios)...')
result = buscar_barrio(path_poligonos_bucaramanga,
                  path_poligonos_floridablanca,
                  path_poligonos_giron,
                  path_poligonos_piedecuesta,
                  pattern_general_,
                  arcgis)
try:
    result.to_excel('check_point_geo_barrio.xlsx', index=False)
except:
    result.to_csv('check_point_geo_barrio.csv', index=False, encoding='utf-8-sig')
print('Buscando (comunas)...')
# por ahora solo se hace la busqueda para bucaramanga
result = buscar_comuna(result, todos_div_pol)  
try:
    result.to_excel('check_point_geo_barrio_comuna.xlsx', index=False)
except:
    result.to_csv('check_point_geo_barrio_comuna.csv', index=False, encoding='utf-8-sig')

print('Creando estructura final ...')
result[['NUMERO COMUNA','NOMCOMUNA']] =  result.COMUNA.str.split(".",expand=True)
result['tem'] = result.NOMCOMUNA
result.loc[result.NOMCOMUNA.isnull(),'NOMCOMUNA'] = result.loc[result.NOMCOMUNA.isnull(),'NUMERO COMUNA']
result.loc[result.tem.isnull(),'NUMERO COMUNA'] = None
result.loc[~(result.ciudad_geo.isnull())&(~(result.ciudad_geo.isin(['Bucaramanga', 'Floridablanca']))), 'COMUNA'] = result.loc[~(result.ciudad_geo.isnull())&(~(result.ciudad_geo.isin(['Bucaramanga', 'Floridablanca']))), 'ciudad_geo'].str.upper()
result.loc[~(result.ciudad_geo.isnull())&(~(result.ciudad_geo.isin(['Bucaramanga', 'Floridablanca']))), 'NOMCOMUNA'] = result.loc[~(result.ciudad_geo.isnull())&(~(result.ciudad_geo.isin(['Bucaramanga', 'Floridablanca']))), 'ciudad_geo'].str.upper()
result._bar_ver_= result.barrio_poly.str.upper() 
result.loc[~(result.ciudad_geo.isnull())&(~(result.ciudad_geo.isin(['Bucaramanga', 'Floridablanca']))), '_bar_ver_'] = result.loc[~(result.ciudad_geo.isnull())&(~(result.ciudad_geo.isin(['Bucaramanga', 'Floridablanca']))), 'ciudad_geo'].str.upper()
# sin no hay comuna se debe devolver sin informacion
# de igual manera para las columnas de barrios y ceros para las del numero
result.loc[result.COMUNA.isnull(),'COMUNA'] = 'SIN INFORMACION'
result.loc[result.bar_ver_.isnull(),'bar_ver_'] = 'SIN INFORMACION'
result.loc[result._bar_ver_.isnull(),'_bar_ver_'] = 'SIN INFORMACION'
result.loc[result.NOMCOMUNA.isnull(),'NOMCOMUNA'] = 0
result.loc[result['NUMERO COMUNA'].isnull(),'NUMERO COMUNA'] = 0
result['DIR'] = result['dir_filtradas']
# Eliminar las columnas temporales para devolver solo el formato solicitado
del result['tem']
try:
    result.to_excel('check_point_pre_final.xlsx', index=False)  
except:
    result.to_csv('check_point_pre_final.csv', index=False, encoding='utf-8-sig')
del result['barrio_poly']
del result['barrio_geo']
del result['score']
#del result['ciudad_geo']
del result['coordenadas']
del result['respuesta']
#del result['dir_filtradas']
try:
    result.to_excel(addresses_path.split('/')[-1].split('.')[0]+'_estructura_final.xlsx', index=False) 
except:
    result.to_csv(addresses_path.split('/')[-1].split('.')[0]+'_estructura_final.csv', index=False, encoding='utf-8-sig') 
print('procedimiento finalizado .... Nos vemos mañana')