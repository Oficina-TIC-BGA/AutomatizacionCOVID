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
    # definir las palabras comunes
    common_words = {} 
    common_words['carrera'] = ['\bK','KRA', 'CRA', 'KR', 'CR\s', 'ARRERA', 'CARRRERA', 'CARRRA', 'CRR',  'CARERRA', 'CARR\s', 'CARRERA']
    common_words['calle'] = ['CLL', 'CL', 'CLEE', 'CLLE', 'CALL\b','\bCC\b']
    common_words['diagonal'] = ['DIAG\s', 'DIAGONAL', 'DG']
    common_words['transversal'] = ['TRANSVERSAL', '\sTR\s','TRV','TRANSV', 'TV', 'TRANVERSAL', 'TRANSV', 'TRANSSV\s','TRASVERSAL', 'TRANV', 'TANSVERSAL', 'TRANVS']
    common_words['numero'] = ['\bNUM\b', '\sNUM\s', 'NUMERO', 'NÚMERO', '#', '\sNO\s', 'NRO', 'Nª','Nº','N°']
    common_words['circunvalar'] = ['VIRCUNVALAR','CIRCUNVALAR', 'CIRC', 'CIR', 'CCV', 'CV', 'circunvalarv']
    common_words['avenida'] = ['AV\s+', 'AVENIDA', '\sAVD\s','AVDA', 'AVEN\s', 'avn', '\svda\s']
    common_words['quebradaseca'] = ['qdaseca', 'quebrada seca', 'quebrada']
    common_words['edificio'] = ['edif*\s', 'edf', 'edificio']
    common_words['torre'] = ['tprre\s','torr*\s', '\btor\b', '\sto\s', 'tr\s', '\st\s']
    common_words['barrio'] = ['\sbrr', '\sbario\s','barrio','BARRIO', '\sbr\s']
    common_words['apartamento'] = ['\sAPTO\s', '\sAPP\s' ,'APTO ','\sAPTO', 'ap\s', 'aparatamento','apartamento*', 'apar\s','apart\s', 'APRO\s', '\sapato', '\sapt', '\bAPTO\b', '\saparta\s']
    common_words['bloque'] = ['BLOQUE', '\sblo\s', 'bloq\s']
    common_words['sector'] = ['SECTOR', 'sect\s', 'sec\s'] 
    common_words['kilometro'] = ['KM\s*', 'KILOMETRO', 'KM ']
    common_words['vereda'] = ['\bVDA\s', '\bVER\s']
    common_words['manzana'] = ['\sMANZANA\s','\smz\s*', '\smanza\s']

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
    pattern_kilometro = re.compile(r'|'.join(common_words['kilometro']), re.IGNORECASE)
    pattern_guion = re.compile(r'-|\.|·|\|º|°')#|Nª|º|°
    pattern_nume2 = re.compile(r'\sNO\d|\sNUM\d', re.IGNORECASE)
    pattern_nume3 = re.compile(r'\dNO\d|\dNUM\d', re.IGNORECASE)
    pattern_final = re.compile(r'barrio|primer piso\s*|peatonal\s*\d+|manzana\s*\d+|t\d+|casa\s*\d+|piso\s*\d+|apartamento\s*\d+|torre\s*\d+', re.IGNORECASE)
    patter_final2 = re.compile(r'conjunto residencial|torre\s[a-z]*|edificio|edificio\s*\d+|bloque\s*\d+|piso|apartamento|manzana\s*\d+|sector\s*[a-z]|manzana\s*[a-z]|sector\s*\d+', re.IGNORECASE)
    #pattern_final = re.compile(r'(\s[a-z\s*]*\s*)', re.IGNORECASE)
    pattern_barrio = re.compile(r'|'.join(common_words['barrio']), re.IGNORECASE)
    pattern_std = re.compile(r'carrera|calle|avenida|diagonal|transversal|circunvalar')
    # ejecutar las expresiones regulares
    # ejecutar los patrones iniciales
    match_specials_num = re.search(pattern_nume2, dir)
    if match_specials_num:
        found_pattern = match_specials_num.group()
        dir = dir.replace(found_pattern[:-1], ' ')
    
    match_specials_num3 = re.search(pattern_nume3, dir)
    if match_specials_num3:
        found_pattern3 = match_specials_num3.group()
        dir = dir.replace(found_pattern3[1:-1], ' ')

    match_specials = re.finditer(pattern_guion, dir)
    if match_specials:
        for match_guion in match_specials:
            found_pattern = match_guion.group()
            dir = dir.replace(found_pattern, ' ')

    match_numeros = re.search(pattern_numeros, dir)
    if match_numeros:
        x0, xt = match_numeros.span()
        if dir[x0+1]==' ':
            dir = dir[:x0+1] + dir[x0+1:].replace(' ','',1) 

    # ejecutar los patrones intermedios        
    patterns = [pattern_carrera, pattern_calle, pattern_diagonal, pattern_transversal, pattern_num, pattern_circunvalar, 
                pattern_avenida, pattern_quebradaseca, pattern_edificio, pattern_torre, pattern_apartamento, pattern_bloque, pattern_sector,
                pattern_kilometro, pattern_barrio]
    for pattern, p in zip(patterns,[' carrera ', ' calle ', ' diagonal ', ' transversal ', ' ', 'circunvalar', 'avenida', 'quebradaseca', 'edificio',
                                    ' torre ', ' apartamento ', ' bloque ', ' sector ', ' kilometro ', ' barrio ']):
        matches = re.finditer(pattern, dir)
        if matches:
            for match in matches:
                #print(match)
                found_pattern = match.group()
                dir = dir.replace(found_pattern, p)
                #print(dir)
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

    
    for pat in [pattern_final, patter_final2]:
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
def where_is(dir, data, lista_bucaramanga, lista_floridablanca, lista_giron, pattern_general):
    # ponerle la ciudad
    # ejecutar los patrones intermedios        
    # para saber si no entro a ninguna ciudad
    flag = False
    dir_copy = dir
    # si hay barrio de base de datos
    pre_barrio = data.loc[data.dir_filtradas.str.lower()==dir, 'bar_ver_'].isnull().values[0]
    patterns = [lista_bucaramanga, lista_floridablanca, lista_giron] # pattern_piedecuesta, pattern_giron,
    #print('dir ori', dir)
    flag_b = False
    for pattern, p in zip(patterns,['bucaramanga', 'floridablanca', 'giron']):
        # selecciona de a 20 ciudades
        for l in range(0,len(pattern),20):    
            pattern_partial = re.compile(r'|'.join(pattern[l:l+20]), re.IGNORECASE)
            matches = re.findall(pattern_partial, dir)
            # para saber si ya entro a un patron y no repita
            if len(matches)>0:
                #for found_pattern in matches:
                if p == 'floridablanca':
                    flag = True 
                    if flag_b==False:
                        dir = dir + str(', '+p)
                    flag_b = True    
                elif p == 'giron':
                    flag = True
                    if flag_b==False:
                        dir = dir + str(', '+p)
                    flag_b = True        
                elif p == 'piedecuesta':
                    flag = True
                    if flag_b==False:
                        dir = dir + str(', '+p)   
                    flag_b = True                
                elif p == 'bucaramanga':
                    flag = True
                    if flag_b==False:
                        dir = dir + str(', '+p)   
                    flag_b = True  
    
    matches_found = re.findall(pattern_general, dir)
    if len(matches_found)>1 and ~pre_barrio:
        pre_barrio_exist = data.loc[data.dir_filtradas.str.lower()==dir_copy, 'bar_ver_'].values[0]
        # TO DO: analizar  si al final quedó con más de una ciudad
        #print(matches_found, pre_barrio_exist) 
    if flag == False:
        # puede que haya algo útil en la dirección
        if dir!='nan' and dir!='sin informacion' and len(dir)>=3:
            # Descartar que no sean ciudades de otro departamento
            # si no colocar bucaramanga por defecto
            matches_general = re.findall(pattern_general, dir)
            flag_c = False
            if len(matches_general)>0:
                # que ciudad encontro?
                ciudad = matches_general[0]
                flag_c = True

            if flag_c==False:
                dir = dir + str(', bucaramanga')
                # TODO antes de colocar mirar si decia otra ciudad 
                #if ~pre_barrio:
                #    pre_barrio_exist = data.loc[data.dir_filtradas.str.lower()==dir_copy, 'bar_ver_'].values[0]
                #    # TO DO: cuando devuelvan el barrio hay que considerar eliminarla
                #    #dir = dir + str(', '+str(pre_barrio_exist).lower()+', bucaramanga')
                #    pass
                #else: 
                #    dir = dir + str(', bucaramanga')  
        # si no hay ningún match ya sea porque esta vacia o porque no es una dirección útil
        else:
            # DEVOLVER DIRECCIONES VACIAS
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
        elif np.isnan(x): 
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
        elif np.isnan(x): 
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
                # valida si hay algo en la cidad de argis y que no se halla encontrado barrio por poly
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
    ###### GIRON #########################
    ###### PIEDECUESTA #########################
    #---------------------------------------------
    arcgis['score'] = arcgis.respuesta.apply(lambda x: score(x))
    arcgis['ciudad_geo'] = arcgis.respuesta.apply(lambda x: ciudad(x, pattern_general))
    arcgis['barrio_geo'] = arcgis.respuesta.apply(lambda x: barrios(x))
    # buscar barrio por poligono
    # pasarle todos los barrios
    # por ahora solo le paso los de bucaramanga despues sera la concatenación de todos
    result = buscar_solo_barrio(datos_todos_bucaramanga, arcgis)

    return result 

def buscar_comuna(result, division_politica_bucaramanga): 
    comunas = []
    for bn in tqdm(result['barrio_poly'].str.lower(), desc='Comunas'):
        com = division_politica_bucaramanga.COMUNA[division_politica_bucaramanga['BARRIO'].str.lower()==bn].values
        if len(com)!=0:
            comunas.append(com[0])
        else:
            if bn!=None:
                comunas.append(bn.upper())
            else:
                ## ciudad geo
                #if result.iloc[j,12].lower()!='bucaramanga':
                comunas.append(None)  
    result.COMUNA = comunas          
    return result   

### DIVISION METROPOLITANA DE BUCARAMANGA
def pattern(division_politica):
    barrios = division_politica.BARRIO.str.strip().values.tolist()
    sectores = division_politica[~division_politica.SECTOR.isnull()].SECTOR.values.tolist()
    conjuntos = division_politica[~division_politica.CONJUNTO.isnull()].CONJUNTO.values.tolist()
    conjuntos = [j.strip() for i in conjuntos for j in i.split(',')]
    sectores = [j.strip() for i in sectores for j in i.split(',')]
    todos = barrios + sectores + conjuntos  
    #pattern = re.compile(r'|'.join([i for i in todos]), re.IGNORECASE)
    return ['\s+'+i for i in todos]

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
##### TODO: ESTE PASO PODRIA SER UN MODELO DE MACHINE
## identificar y colocar el municipio
division_politica_bucaramanga = pd.read_excel(path_pol, sheet_name='DIVISION_POLITICA_BUCARAMANGA')
division_politica_floridablanca = pd.read_excel(path_pol, sheet_name='DIVISION_POLITICA_FLORIDABLANCA')
division_politica_giron = pd.read_excel(path_pol, sheet_name='DIVISION_POLITICA_GIRON')
division_politica_piedecuesta = pd.read_excel(path_pol, sheet_name='DIVISION_POLITICA_PIEDECUESTA')
division_politica_general = pd.read_excel(path_pol, sheet_name='CIUDADES')
# PATTERNS
# BUCARAMANGA
lista_bucaramanga = pattern(division_politica_bucaramanga)
# FLORIDABLANCA
lista_floridablanca = pattern(division_politica_floridablanca)
# PIEDECUESTA
#pattern_piedecuesta = pattern(division_politica_piedecuesta, ciudades, ciudad='piedecuesta')
# GIRON
lista_giron = pattern(division_politica_giron)
#pattern_giron = pattern(division_politica_giron, ciudades, ciudad='giron')
# pattern en general para considerar ciudades de otros lugares del país
pattern_general = re.compile(r'|'.join(division_politica_general.CIUDADES.values.tolist()), re.IGNORECASE)
df_addresses['dir_filtradas'] = df_addresses.dir_filtradas.apply(lambda x: where_is(x,
                                                                                    df_addresses,
                                                                                    lista_bucaramanga,
                                                                                    lista_floridablanca,
                                                                                    lista_giron,
                                                                                    pattern_general)).values
try:
    df_addresses.to_excel('check_point.xlsx', index=False)
except:
    df_addresses.to_csv('check_point.csv', index=False)
## Buscar coordenadas 
print('Geoposicionando ...')
# ArcGIS - la mejor opción a google
geolocator_arcgis = ArcGIS(username=None, password=None, user_agent=addresses_path.split('/')[-1])
# usando arcgis
arcgis = search(geolocator_arcgis, df_addresses)
try:
    arcgis.to_excel('check_point_geo.xlsx', index=False)
except:
    arcgis.to_csv('check_point_geo.csv', index=False)
    
# buscar el barrio con las coordenadas
print('Cruzando información de polígonos (barrios)...')
result = buscar_barrio(path_poligonos_bucaramanga,
                  path_poligonos_floridablanca,
                  path_poligonos_giron,
                  path_poligonos_piedecuesta,
                  pattern_general,
                  arcgis)
try:
    result.to_excel('check_point_geo_barrio.xlsx', index=False)
except:
    result.to_csv('check_point_geo_barrio.csv', index=False)
print('Buscando (comunas)...')
# por ahora solo se hace la busqueda para bucaramanga
result = buscar_comuna(result, division_politica_bucaramanga)  
try:
    result.to_excel('check_point_geo_barrio_comuna.xlsx', index=False)
except:
    result.to_csv('check_point_geo_barrio_comuna.csv', index=False)
print('Creando estructura final ...')
result[['NUMERO COMUNA','NOMCOMUNA']] =  result.COMUNA.str.split(".",expand=True)
result['tem'] = result.NOMCOMUNA
result.loc[result.NOMCOMUNA.isnull(),'NOMCOMUNA'] = result.loc[result.NOMCOMUNA.isnull(),'NUMERO COMUNA']
result.loc[result.tem.isnull(),'NUMERO COMUNA'] = None
result.loc[~(result.ciudad_geo.isnull())&(result.ciudad_geo!='Bucaramanga'), 'COMUNA'] = result.loc[~(result.ciudad_geo.isnull())&(result.ciudad_geo!='Bucaramanga'), 'ciudad_geo'].str.upper()
result.loc[~(result.ciudad_geo.isnull())&(result.ciudad_geo!='Bucaramanga'), 'NOMCOMUNA'] = result.loc[~(result.ciudad_geo.isnull())&(result.ciudad_geo!='Bucaramanga'), 'ciudad_geo'].str.upper()
result._bar_ver_= result.barrio_poly
result.loc[~(result.ciudad_geo.isnull())&(result.ciudad_geo!='Bucaramanga'), '_bar_ver_'] = result.loc[~(result.ciudad_geo.isnull())&(result.ciudad_geo!='Bucaramanga'), 'ciudad_geo'].str.upper()
# sin no hay comuna se debe devolver sin informacion
# de igual manera para las columnas de barrios y ceros para las del numero
result.loc[result.COMUNA.isnull(),'COMUNA'] = 'SIN INFORMACION'
result.loc[result.bar_ver_.isnull(),'bar_ver_'] = 'SIN INFORMACION'
result.loc[result._bar_ver_.isnull(),'_bar_ver_'] = 'SIN INFORMACION'
result.loc[result.NOMCOMUNA.isnull(),'NOMCOMUNA'] = 0
result.loc[result['NUMERO COMUNA'].isnull(),'NUMERO COMUNA'] = 0
# Eliminar las columnas temporales para devolver solo el formato solicitado
del result['tem']
try:
    result.to_excel('check_point_pre_final.xlsx', index=False)  
except:
    result.to_csv('check_point_pre_final.csv', index=False)
del result['barrio_poly']
del result['barrio_geo']
del result['score']
del result['ciudad_geo']
del result['coordenadas']
del result['respuesta']
del result['dir_filtradas']
try:
    result.to_excel(addresses_path.split('/')[-1].split('.')[0]+'_estructura_final.xlsx', index=False) 
except:
    result.to_csv(addresses_path.split('/')[-1].split('.')[0]+'_estructura_final.csv', index=False) 
print('procedimiento finalizado .... Nos vemos mañana')
