!pip -q install xlsxwriter
## importart librerias 
# para recibir los parametros
import argparse
import sys
import configparser
# manejo de datos
import pandas as pd
import numpy as np
# regular expressions
import re
# manejo de poligonos
import shapely.wkt
import shapely.speedups
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
# barras de progreso
import tqdm
from tqdm import tqdm
# quitar warnings
import warnings
warnings.filterwarnings('ignore')
tqdm.pandas()

############### FUNCIONES ########################
### Para la busqueda de barrios y municipios
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
    coords = data_coords.coordenadas.values
    collect_intersections_bar = dict()
    # Recorrer  los puntos
    for j,coord in enumerate(tqdm(coords, desc='Points')): 
        if isinstance(coord, tuple):
            lon = coord[0] 
            lat = coord[1]
        else:    
            lon = np.nan
            lat = np.nan
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
        if collect_intersections_bar[j] == None:
            name = buscar_cercano(point_x_y, datos_barrios, key='NOMBRE') 
            collect_intersections_bar[j] = name 
                
    # crear columnas
    barrios = list()
    for p in range(data_coords.shape[0]):
        barr = collect_intersections_bar[p]
        barrios.append(barr)
    data_coords['barrios'] = barrios

    return data_coords
# Para categorizar PRASS del día
def categorizar(x):
    if isinstance(x,int):
        if int(x) <=5:
            r = "0 a 5 días"
        elif 6 <= int(x) <=11:
            r = "6 a 11 días"
        elif 12 <= int(x) <=20:
            r = "12 a 20 días"  
        elif 21 <= int(x) <=30:
            r = "21 a 30 días"
        elif int(x)>=31:
            r = " 31 o más"
    else:
        r = ''

    return r 

# Para normalizar eps
def eps_estandarizacion(x):
    try: 
        np.isnan(x)
        x = ''
    except:
        pass    
    # TODO: Resumir expresiones regulares
    common_words = {} 
    common_words['ASMET SALUD'] = ['asmet_salud_essc', 'asmet_salud_ess']
    common_words['CAFESALUD'] = ['cafesalud_eps_sa', 'cafesalud_subsidiado', 'cafe_salud']
    common_words['MEDIMAS'] = ['medimas_eps_contributivo', 'medimas_eps_movilidad_contribut', 'medimas_eps_subsidiado', 'medimas_eps_movilidad_subsidiad', 'medisanitas_sa_prepagada']
    common_words['NUEVA EPS'] = ['nueva_eps_contributivo', 'nueva_eps_sa_subsidiado', 'nueva_eps*']
    common_words['SALUD TOTAL EPS'] = ['salud_total_epss', 'salud_total_sa_eps', 'salud_total_sa_subsidiado']
    common_words['COOMEVA'] = ['coomeva_eps_sa','coomeva_epss','coomeva_medicina_prepagada_s_a', 'programa_coomeva_emergencias_me']
    common_words['COMPENSAR EPS'] = ['compensar_e_p_s_cm', 'compensar_eps']
    common_words['COOSALUD'] = ['coosalud_ess_eps_s', 'coosalud_essc']
    common_words['SANITAS'] = ['e_p_s_sanitas_s_a_cm', 'eps_colsanitas']
    common_words['FAMISANAR'] = ['famisanar_eps_ltda','famisanar_epss']
    common_words['SALUD VIDA EPS'] = ['saludvida_eps_sa','salud_vida_eps']
    common_words['SURA'] = ['compañia_suramericana_prepagada','sura_eps','sura_']
    common_words['SALUD MIA'] = ['fundacion_salud_mia_eps','salud_mia_eps']
    common_words['CCF COLSUBSIDIO'] = ['ccf_colsubsidio', 'colsubsidio_ccf'] 
    common_words['CAJACOPI CCF055'] = ['cajacopi_ccf055','cajacopi']
    common_words['SIN ESPECIFICAR'] = ['CHOICE 119', 'choice_119']
    common_words['EAPB'] = ['Entidad Prestadora de Salud (EPS)']
    common_words['NO ASEGURADO'] = ['no_tiene']
    common_words['COMFAMILIAR'] = ['ccf_comfamiliar_huila']
    common_words['ESS COOPERATIVA LA NUEVA ESPERANZA'] = ['ess_cooperativa_la_nueva_espera']
    common_words['FERROCARRILES NACIONALES'] = ['ferrocarriles_nacionales_de_col']
    common_words['SANIDAD POLICIA NACIONAL'] = ['policia_nacional']

    # definir los patrones con las expresiones regulares
    pattern_guion = re.compile(r'_')
    pattern_1 = re.compile(r'|'.join(common_words['ASMET SALUD']), re.IGNORECASE)
    pattern_2 = re.compile(r'|'.join(common_words['CAFESALUD']), re.IGNORECASE)
    pattern_3 = re.compile(r'|'.join(common_words['MEDIMAS']), re.IGNORECASE)
    pattern_4 = re.compile(r'|'.join(common_words['NUEVA EPS']), re.IGNORECASE)
    pattern_5 = re.compile(r'|'.join(common_words['SALUD TOTAL EPS']), re.IGNORECASE)
    pattern_6 = re.compile(r'|'.join(common_words['COOMEVA']), re.IGNORECASE)
    pattern_7 = re.compile(r'|'.join(common_words['COMPENSAR EPS']), re.IGNORECASE)
    pattern_8 = re.compile(r'|'.join(common_words['COOSALUD']), re.IGNORECASE)
    pattern_9 = re.compile(r'|'.join(common_words['SANITAS']), re.IGNORECASE)
    pattern_10 = re.compile(r'|'.join(common_words['FAMISANAR']), re.IGNORECASE)
    pattern_11 = re.compile(r'|'.join(common_words['SALUD VIDA EPS']), re.IGNORECASE)
    pattern_12 = re.compile(r'|'.join(common_words['SURA']), re.IGNORECASE)
    pattern_13 = re.compile(r'|'.join(common_words['SALUD MIA']), re.IGNORECASE)
    pattern_14 = re.compile(r'|'.join(common_words['CCF COLSUBSIDIO']), re.IGNORECASE)
    pattern_15 = re.compile(r'|'.join(common_words['CAJACOPI CCF055']), re.IGNORECASE)
    pattern_16 = re.compile(r'|'.join(common_words['SIN ESPECIFICAR']), re.IGNORECASE)
    pattern_17 = re.compile(r'|'.join(common_words['EAPB']), re.IGNORECASE)
    pattern_18 = re.compile(r'|'.join(common_words['NO ASEGURADO']), re.IGNORECASE)
    pattern_19 = re.compile(r'|'.join(common_words['COMFAMILIAR']), re.IGNORECASE)
    pattern_20 = re.compile(r'|'.join(common_words['ESS COOPERATIVA LA NUEVA ESPERANZA']), re.IGNORECASE)
    pattern_21 = re.compile(r'|'.join(common_words['FERROCARRILES NACIONALES']), re.IGNORECASE)
    pattern_22 = re.compile(r'|'.join(common_words['SANIDAD POLICIA NACIONAL']), re.IGNORECASE)

    # ejecutar los patrones intermedios
    # cambia los patrones por su forma correcta y agrega espacios para separar        
    patterns = [pattern_1,pattern_2,pattern_3,pattern_4,pattern_5,pattern_6,pattern_7,pattern_8,pattern_9,
                pattern_10,pattern_11,pattern_12,pattern_13,pattern_14,pattern_15,pattern_16,pattern_17,
                pattern_18,pattern_19,pattern_20,pattern_21,pattern_22]
    for pattern, p in zip(patterns,['ASMET SALUD', 'CAFESALUD', 'MEDIMAS', 'NUEVA EPS', 'SALUD TOTAL EPS', 'COOMEVA', 'COMPENSAR EPS',
                                    'COOSALUD', 'SANITAS', 'FAMISANAR', 'SALUD VIDA EPS', 'SURA', 'SALUD MIA', 'CCF COLSUBSIDIO', 'CAJACOPI CCF055',
                                    'SIN ESPECIFICAR','EAPB','NO ASEGURADO','COMFAMILIAR','ESS COOPERATIVA LA NUEVA ESPERANZA','FERROCARRILES NACIONALES',
                                    'SANIDAD POLICIA NACIONAL']):
        matches = re.finditer(pattern, x)
        if matches:
            for match in matches:
                found_pattern = match.group()
                x = x.replace(found_pattern, p)

    # elimina signos guiones bajos
    match_specials = re.finditer(pattern_guion, x)
    if match_specials:
        for match_guion in match_specials:
            found_pattern = match_guion.group()
            x = x.replace(found_pattern, ' ')
    x = x.strip().replace("  ", " ").replace("  ", " ")    
    return x.upper()           

def categorizar_base(x):
    if str(x)!='nan':
        if int(x) <=5:
            r = "0 a 5 días"
        elif 6 <= int(x) <=11:
            r = "6 a 11 días"
        elif 12 <= int(x) <=20:
            r = "12 a 20 días"  
        elif 21 <= int(x) <=30:
            r = "21 a 30 días"
        elif int(x)>=31:
            r = " 31 o más"
    else:
        r = ''

    return r  

######### Ejecución del script
# CAPTURAR LOS PARAMETROS DE DIRECCIONES
# de este txt sacar las direcciones de los archivos
config = configparser.ConfigParser()
config.read(sys.argv[1])
path_base_dia = config['paths']['path_base_dia']
path_sismuestras = config['paths']['path_sismuestras']
path_antigenica = config['paths']['path_antigenica']
path_ira_historico = config['paths']['path_ira_historico']
path_pol = config['paths']['path_division_politica_AMB']
path_poligonos_bucaramanga = config['paths']['path_poligonos_bucaramanga']
path_poligonos_giron = config['paths']['path_poligonos_giron']
path_poligonos_piedecuesta = config['paths']['path_poligonos_piedecuesta']
path_poligonos_floridablanca = config['paths']['path_poligonos_floridablanca']
path_poligonos_mun_santander = config['paths']['path_poligonos_mun_santander']

# Cargar bases de datos de muestras - PCR y ANTIGENAS
df_sismuestras = pd.read_csv(path_sismuestras, encoding="UTF-16",sep='|', error_bad_lines=True, delimiter='|')
df_antigenica = pd.read_csv(path_antigenica, header=1) 
# Cargar prass del día
df_prass_dia = pd.read_excel(path_base_dia) 
# 1. Solo tomar a partir del 22 de agosto 
df_antigenica.fecha = df_antigenica.fecha.astype('datetime64[ns]')
df_antigenica = df_antigenica.loc[df_antigenica.fecha >= '2020-08-22']
# 1. Filtrar PCR por fecha (Mayores a 22 de agosto)
df_sismuestras.FechaMuestra = pd.to_datetime(df_sismuestras.FechaMuestra,  dayfirst=True)
df_sismuestras.Fecha_Resultado = pd.to_datetime(df_sismuestras.Fecha_Resultado,  dayfirst=True)
df_sismuestras = df_sismuestras.loc[df_sismuestras.FechaMuestra>='2020-08-22']  

df_sismuestras.Documento = df_sismuestras.Documento.str.strip()
df_antigenica.num_identificacion = df_antigenica.num_identificacion.str.strip() 

print('Numero de registros en cada base de datos PCR: {} - Antigena {}'.format(df_sismuestras.shape[0],df_antigenica.shape[0]))

### PRASS del día
df_prass_dia['Número de documento'] = df_prass_dia['Número de documento'].str.strip()
print('Registros en del día: {}'.format(df_prass_dia.shape[0]))
## Crear la estructura del prass a llenar
columnas = ['RESULTADO', 'NOMBRE', 'PRIMER APELLIDO', 'BARRIO', 
            'ESTADO VISITA', 'Fecha Resultado', 'Dias diferencias', 
            'Resultado prueba antigenica', 'Fecha prueba antigenica', 
            'Dias diferencias pba antigenica', 'Escala tiempo PCR', 'Escala tiempo antigénica']
for columna in columnas: 
    df_prass_dia[columna] = ''  

# 1. Regla de negocio. Determinar pruebas fallidas  y efectiva
df_prass_dia.loc[df_prass_dia.Nombres.isnull(),'ESTADO VISITA'] = 'FALLIDAS'
df_prass_dia.loc[~df_prass_dia.Nombres.isnull(),'ESTADO VISITA'] = 'EFECTIVAS'

# 2. Regla de negocio buscar pruebas positvas o negativas por cedula
# cedulas con prueba
cc = df_prass_dia.loc[~(df_prass_dia['Número de documento'].isnull()),'Número de documento']

# eliminar duplicados de sismuestras
df_sismuestras = df_sismuestras[~df_sismuestras['Documento'].duplicated(keep='last')]

# eliminar duplicados de antigenicas 
df_antigenica = df_antigenica[~df_antigenica['num_identificacion'].duplicated(keep='last')]

# buscar resultado de pruebas
# PCR
resultado_pcr = df_sismuestras.loc[df_sismuestras.Documento.isin(cc),['Documento','PrimerNombre', 'PrimerApellido', 'Fecha_Resultado','Resultado']]
resultado_pcr.rename(columns={'Documento':'Número de documento',
                              'PrimerNombre':'NOMBRE',
                              'PrimerApellido':'PRIMER APELLIDO',
                              'Fecha_Resultado':'Fecha Resultado',
                              'Resultado':'RESULTADO'}, inplace=True)
# antigenica
resultado_ant = df_antigenica.loc[df_antigenica.num_identificacion.isin(cc),['num_identificacion', 'nombre','fecha','resultado']]
resultado_ant.rename(columns={'num_identificacion':'Número de documento',
                              'nombre':'NOMBRE',
                              'fecha':'Fecha prueba antigenica',
                              'resultado':'Resultado prueba antigenica'}, inplace=True)

print('registros encontrados en sismuestras: {} en antogenica {}'.format(resultado_pcr.shape, resultado_ant.shape))

# Regla de negocio para cuando hay personas que tiene dos resultados para dos días diferentes
# Se deja el más reciente
resultado_pcr = resultado_pcr.loc[~resultado_pcr['Número de documento'].duplicated(keep='last')]
resultado_ant = resultado_ant.loc[~resultado_ant['Número de documento'].duplicated(keep='last')]

# crear pivot para poder ordenar por documento
pivot_pcr = df_prass_dia.loc[df_prass_dia['Número de documento'].isin(resultado_pcr['Número de documento']),['CreationDate',
                                                                                                             'Número de documento', 
                                                                                                             'Fecha Resultado']]
pivot_pcr = pivot_pcr.loc[~pivot_pcr['Número de documento'].duplicated(keep='last')]

# si encontro algun documento
if pivot_pcr.shape[0]!=0:
    # Colocar el tipo prueba todo PCR por que hay unos que no vienen
    # se hace el ajuste de tipo de prueba para los que no tienen 
    df_prass_dia.loc[df_prass_dia['Número de documento'].isin(resultado_pcr['Número de documento']),'Tipo de prueba de hisopado'] = 'PCR'
    # hacer el remplazo de los encontrados PCR
    df_prass_dia.loc[(df_prass_dia['Número de documento'].isin(resultado_pcr['Número de documento']))
                    &(~df_prass_dia['Número de documento'].duplicated(keep='last')),['NOMBRE',
                                                                                    'PRIMER APELLIDO',
                                                                                    'Fecha Resultado',
                                                                                    'RESULTADO']] = pd.merge(pivot_pcr['Número de documento'], 
                                                                                                                        resultado_pcr, 
                                                                                                                        on='Número de documento').drop('Número de documento', axis=1).values

# crear pivot para poder ordenar por documento
pivot_ant = df_prass_dia.loc[df_prass_dia['Número de documento'].isin(resultado_ant['Número de documento']),['CreationDate',
                                                                                                             'Número de documento', 
                                                                                                             'Fecha prueba antigenica']]
pivot_ant = pivot_ant.loc[~pivot_ant['Número de documento'].duplicated(keep='last')]
  
# aqui puede pasar que se reemplaze un pcr por una antigenica en tipo prueba este caso se corrige mas adelate
# si encontro alguno documento
if pivot_ant.shape[0]!=0:
    # Colocar el tipo prueba todo antigenica por que hay unos que no vienen
    df_prass_dia.loc[df_prass_dia['Número de documento'].isin(resultado_ant['Número de documento']),'Tipo de prueba de hisopado'] = 'Antigénica'
    # hacer el remplazo de los encontrados antigenica
    df_prass_dia.loc[(df_prass_dia['Número de documento'].isin(resultado_ant['Número de documento']))
                    &(~df_prass_dia['Número de documento'].duplicated(keep='last')),['NOMBRE',
                                                                                    'Fecha prueba antigenica',
                                                                                    'Resultado prueba antigenica']] = pd.merge(pivot_ant['Número de documento'], 
                                                                                                                            resultado_ant, 
                                                                                                                            on='Número de documento').drop('Número de documento', axis=1).values   

# Colocar el no acepta toma de muestra
df_prass_dia.loc[df_prass_dia['Muestras y notificación'].astype(str)=='la_persona_no_acepta_la_toma_de','RESULTADO'] = 'No acepta toma muestra'

# ahora si tiene PCR - antigenica y no fecha colocar pendiente
df_prass_dia.loc[(df_prass_dia['Tipo de prueba de hisopado']=='PCR')&(df_prass_dia['RESULTADO']==''),'RESULTADO'] = 'Pendiente'
# para las antigenicas
df_prass_dia.loc[(df_prass_dia['Tipo de prueba de hisopado']=='Antigénica')&(df_prass_dia['Resultado prueba antigenica']==''),
                 'Resultado prueba antigenica'] = 'Pendiente'

# Para sacar diferencias se adiciona un día a la cuenta ya que pandas hace el conteo en hora tomando así al día anterior
# sacar diferencias
df_prass_dia['Fecha Resultado'] = df_prass_dia['Fecha Resultado'].astype('datetime64[ns]')
df_prass_dia.loc[~df_prass_dia['Fecha Resultado'].isnull(), 'Dias diferencias'] = (df_prass_dia.loc[~df_prass_dia['Fecha Resultado'].isnull(), 'Fecha Resultado'] - df_prass_dia.loc[~df_prass_dia['Fecha Resultado'].isnull(), 'CreationDate']).dt.days+1    

# sacar diferencias
df_prass_dia['Fecha prueba antigenica'] = df_prass_dia['Fecha prueba antigenica'].astype('datetime64[ns]')
df_prass_dia.loc[~df_prass_dia['Fecha prueba antigenica'].isnull(), 'Dias diferencias pba antigenica'] = (df_prass_dia.loc[~df_prass_dia['Fecha prueba antigenica'].isnull(), 'Fecha prueba antigenica'] - df_prass_dia.loc[~df_prass_dia['Fecha prueba antigenica'].isnull(), 'CreationDate']).dt.days+1

# para completar la regla de negocio colocar no aplica en el resto de filas de cada tipo de prueba
df_prass_dia.loc[df_prass_dia['RESULTADO']=='','RESULTADO'] = 'No aplica'
df_prass_dia.loc[df_prass_dia['Resultado prueba antigenica']=='','Resultado prueba antigenica'] = 'No aplica'

# importante lo que cuantifica si es posterior a fecha prass
# finalmente si la diferencia es negativa quiere decir que era resultado de antes por lo tanto queda pendiente
for index, row in df_prass_dia.iterrows():
    if row['Tipo de prueba de hisopado']=='PCR':
        if row['Dias diferencias']!='':
            if int(row['Dias diferencias'])<0:
                # quiere decir que le hicieron PCR y falta el resultado
                #print(df_prass_dia.loc[df_prass_dia.index==index,'RESULTADO'])
                df_prass_dia.loc[df_prass_dia.index==index,'RESULTADO'] = 'Pendiente'
                df_prass_dia.loc[df_prass_dia.index==index,'Dias diferencias'] = ''
    elif row['Tipo de prueba de hisopado']=='Antigénica':
        if row['Dias diferencias pba antigenica']!='':
            if int(row['Dias diferencias pba antigenica'])<0:
                # quiere decir que le hicieron PCR y falta el resultado
                #print(df_prass_dia.loc[df_prass_dia.index==index,'Resultado prueba antigenica'])
                df_prass_dia.loc[df_prass_dia.index==index,'Resultado prueba antigenica'] = 'Pendiente'
                df_prass_dia.loc[df_prass_dia.index==index,'Dias diferencias pba antigenica'] = ''
    # regla de negocio para considerar aquellos que tiene ambas pruebas 
    #para PCR
    try: 
        if int(row['Dias diferencias'])<0:
            df_prass_dia.loc[df_prass_dia.index==index,'RESULTADO'] = 'Pendiente'
            df_prass_dia.loc[df_prass_dia.index==index,'Dias diferencias'] = ''
    except:
        pass    
    #para antigenica
    try: 
        if int(row['Dias diferencias pba antigenica'])<0:
            df_prass_dia.loc[df_prass_dia.index==index,'Resultado prueba antigenica'] = 'Pendiente'
            df_prass_dia.loc[df_prass_dia.index==index,'Dias diferencias pba antigenica'] = ''
    except:
        pass                    

# Regla para crear la categorización de la demora de pruebas
df_prass_dia['Escala tiempo PCR'] = df_prass_dia['Dias diferencias'].apply(lambda x: categorizar(x)) 
df_prass_dia['Escala tiempo antigénica'] = df_prass_dia['Dias diferencias pba antigenica'].apply(lambda x: categorizar(x))

# cargar los poligonos de barrios para cada municipio
####### Bucaramanga ############
datos_bucaramanga = pd.read_csv(path_poligonos_bucaramanga)
datos_todos_bucaramanga = datos_bucaramanga[datos_bucaramanga.CATEGORIA.isin(['BARRIO', 'VEREDA','A. URBANO', 'A. RURAL'])]
###### Floridablanca #########################
datos_floridablanca = pd.read_csv(path_poligonos_floridablanca)
# en floridablanca solo se va a considerar barrios
datos_todos_floridablanca = datos_floridablanca[datos_floridablanca.CATEGORIA.isin(['BARRIO', 'VEREDA'])]
# municipios
muni = pd.read_csv(path_poligonos_mun_santander)
muni_alrededores = muni[(muni.NOMBRE.isin(['FLORIDABLANCA', 'BARRANCABERMEJA', 'GIRON', 'PIEDECUESTA']))]
# coordenadas
data_coords = pd.DataFrame([zip(df_prass_dia.x, df_prass_dia.y)]).T.rename(columns={0:'coordenadas'})
datos_todos = pd.concat([datos_todos_bucaramanga, muni_alrededores], ignore_index=True) #datos_todos_floridablanca cuando lleguen de floridablanca
result = buscar_solo_barrio(datos_todos, data_coords)

# asignar el barrio final
df_prass_dia['BARRIO'] = result.barrios.values

# 6 Regla de negocio - NORMALIZAR las eps
df_prass_dia['Entidad Prestadora de Salud (EPS)'] = df_prass_dia['Entidad Prestadora de Salud (EPS)'].apply(lambda x: eps_estandarizacion(x))

# cambiar antigénica por Antigénica
df_prass_dia.loc[df_prass_dia['Tipo de prueba de hisopado']=='antigénica', 'Tipo de prueba de hisopado'] = 'Antigénica'

df_prass_dia.RESULTADO = df_prass_dia.RESULTADO.str.strip().str.replace("'","")

df_prass_dia['RESULTADO'] = df_prass_dia['RESULTADO'].str.strip()
df_prass_dia['Resultado prueba antigenica'] = df_prass_dia['Resultado prueba antigenica'].str.strip()

df_prass_dia.loc[~(df_prass_dia['Tipo de prueba de hisopado'].isin(['PCR']))
            &(~(df_prass_dia.RESULTADO.isin(['No aplica', 'No acepta toma muestra']))
            &~(df_prass_dia['Resultado prueba antigenica'].isin(['No aplica', 'No acepta toma muestra']))), 'Tipo de prueba de hisopado'] = 'PCR'

# para el caso de las antigenicas
df_prass_dia.loc[~(df_prass_dia['Tipo de prueba de hisopado'].isin(['PCR', 'Antigénica']))
            &((df_prass_dia.RESULTADO.isin(['No aplica', 'No acepta toma muestra', 'INDETERMINADO']))
            &~(df_prass_dia['Resultado prueba antigenica'].isin(['No aplica', 'No acepta toma muestra']))), 'Tipo de prueba de hisopado'] = 'Antigénica'

df_prass_dia.loc[(df_prass_dia['Tipo de prueba de hisopado'].isna())&(df_prass_dia.RESULTADO.str.lower().isin(['positivo', 'negativo', 'pendiente'])), 'Tipo de prueba de hisopado'] = 'PCR'

# filtrado bucaramanga
barrios = datos_todos_bucaramanga.NOMBRE.values
print('{} registros encontrados de Bucaramanga'.format(df_prass_dia.loc[df_prass_dia.BARRIO.isin(barrios)].shape[0]))

df_prass_dia.loc[df_prass_dia.BARRIO.isin(barrios), 'Municipio (Código)'] = 68001.0
# quito los que no estan en bucara y venian marcados como bucara
df_prass_dia.loc[(df_prass_dia['Municipio (Código)']== 68001.0)&~(df_prass_dia.BARRIO.isin(barrios)), 'Municipio (Código)'] = np.nan


#############################################

# Actualización del historico (PRASS BASE)
print('Actualización del histórico IRA')
xls = pd.ExcelFile(path_ira_historico)
# leer la hoja PRASS
df_prass_base = pd.read_excel(xls, sheet_name='PRASS')
df_prass_base['Número de documento'] = df_prass_base['Número de documento'].str.strip()
# quitar la columna Unnamed: 0 - normalmente queda guaradada en una actualizacion anterior
if df_prass_base.keys()[0]=='Unnamed: 0':
    df_prass_base.drop(['Unnamed: 0'], axis=1, inplace=True)

# Regla de negocio buscar pruebas positvas o negativas por cedula y actualizar estados
cc_prass_a_actualizar = df_prass_base.loc[(~(df_prass_base['Número de documento'].isnull()))&(df_prass_base['RESULTADO'].isin(['No aplica','Pendiente']))]['Número de documento']    
print('Cedulas a buscar {}'.format(cc_prass_a_actualizar.shape))

# buscar resultado de pruebas
# PCR
resultado_pcr_base = df_sismuestras.loc[df_sismuestras.Documento.isin(cc_prass_a_actualizar),['Documento','PrimerNombre', 'PrimerApellido', 'Fecha_Resultado','Resultado']]
resultado_pcr_base.rename(columns={'Documento':'Número de documento',
                              'PrimerNombre':'NOMBRE',
                              'PrimerApellido':'PRIMER APELLIDO',
                              'Fecha_Resultado':'Fecha Resultado',
                              'Resultado':'RESULTADO'}, inplace=True)

# duplicadas en sismuestras
resultado_pcr_base = resultado_pcr_base[~resultado_pcr_base['Número de documento'].duplicated(keep='last')]

print('Cedulas encontradas en sismuestras: {}'.format(resultado_pcr_base.shape[0]))
# crear el pivot para actualizar registros
pivot_pcr_base = df_prass_base.loc[(df_prass_base['RESULTADO'].isin(['No aplica','Pendiente']))
                                    &(df_prass_base['Número de documento'].isin(resultado_pcr_base['Número de documento']))]

# en caso de encontrar varios mantener los más recientes
# eliminar duplicados
pivot_pcr_base = pivot_pcr_base.loc[(~(pivot_pcr_base['Número de documento'].duplicated(keep='last')))]

# proceso de actualización
counter_act = 0
nuevos = 0
for index, row in resultado_pcr_base.iterrows():
    indx = pivot_pcr_base.loc[pivot_pcr_base['Número de documento']==row['Número de documento'],'RESULTADO'].index
    if indx.values.shape[0]==1:
        # traer el registro base
        registro_base = df_prass_base.loc[df_prass_base.index==indx.values[0]]
        # verificar que sea un registro nuevo
        if np.isnan(registro_base['Fecha Resultado'].values[0]): 
            df_prass_base.loc[df_prass_base.index==indx.values[0], 'NOMBRE'] = row['NOMBRE']
            df_prass_base.loc[df_prass_base.index==indx.values[0], 'PRIMER APELLIDO'] = row['PRIMER APELLIDO']
            df_prass_base.loc[df_prass_base.index==indx.values[0], 'Fecha Resultado'] = row['Fecha Resultado']
            # sacar los dias diferencia - condiciona el resultado
            dias = (row['Fecha Resultado']-registro_base['CreationDate']).dt.days+1
            if dias.values[0]>=0:
                # cambiar fecha resultado
                df_prass_base.loc[df_prass_base.index==indx.values[0], 'RESULTADO'] = row['RESULTADO']
                # se agrega un día para hacer el ajuste en la resta (el sistema no cuenta el último día)
                df_prass_base.loc[df_prass_base.index==indx.values[0], 'Dias diferencias'] = dias
            else:
                df_prass_base.loc[df_prass_base.index==indx.values[0], 'RESULTADO'] = 'Pendiente'
            nuevos = nuevos + 1
        else:
            # quiere decir que ya hay una fecha por lo tanto mirar si la consulta arroja una nueva fecha
            # ademas verificar que no vengan fechas vacias
            if str(registro_base['Fecha Resultado'].values[0])!='nan' and str(row['Fecha Resultado'])!='nan':
                if row['Fecha Resultado'] > registro_base['Fecha Resultado'].values[0]: 
                    df_prass_base.loc[df_prass_base.index==indx.values[0], 'Fecha Resultado'] = row['Fecha Resultado']  
                    dias = (row['Fecha Resultado']-registro_base['CreationDate']).dt.days+1
                    if dias.values[0]>=0:
                        # se agrega un día para hacer el ajuste en la resta (el sistema no cuenta el último día)
                        df_prass_base.loc[df_prass_base.index==indx.values[0], 'Dias diferencias'] = dias
                        df_prass_base.loc[df_prass_base.index==indx.values[0], 'RESULTADO'] = row['RESULTADO']
                        counter_act = counter_act + 1 
                    else:
                        # fechas que son anteriores al prass se ponen pendiente
                        df_prass_base.loc[df_prass_base.index==indx.values[0], 'RESULTADO'] = 'Pendiente' 
                    
    else:
        print(row, indx.shape) 

print('{} registros actualizado por parte de prueba PCR'.format(counter_act))  
# categorizar dias diferencias en PCR
if pivot_pcr_base.shape[0]!=0:
    df_prass_base['Escala tiempo PCR'] = df_prass_base['Dias diferencias'].apply(lambda x: categorizar_base(x))     

# Regla de negocio buscar pruebas positvas o negativas por cedula y actualizar estados en antigenica
cc_prass_a_actualizar = df_prass_base.loc[(~(df_prass_base['Número de documento'].isnull()))&(df_prass_base['Resultado prueba antigenica'].isin(['No aplica','Pendiente']))]['Número de documento']  
print('Cedulas a buscar en antigenica {}'.format(cc_prass_a_actualizar.shape))  
# buscar resultado de pruebas
# antigenica
resultado_ant_base = df_antigenica.loc[df_antigenica.num_identificacion.isin(cc_prass_a_actualizar),['num_identificacion', 'nombre','fecha','resultado']]
resultado_ant_base.rename(columns={'num_identificacion':'Número de documento',
                              'nombre':'NOMBRE',
                              'fecha':'Fecha prueba antigenica',
                              'resultado':'Resultado prueba antigenica'}, inplace=True)
print('Cedulas encontradas en antigenica: {}'.format(resultado_ant_base.shape[0])) 
# hacer el pivot
resultado_ant_base = resultado_ant_base[~resultado_ant_base['Número de documento'].duplicated(keep='last')]

pivot_ant_base = df_prass_base.loc[(df_prass_base['Resultado prueba antigenica'].isin(['No aplica','Pendiente']))
                                    &(df_prass_base['Número de documento'].isin(resultado_ant_base['Número de documento']))]
pivot_ant_base = pivot_ant_base.loc[~pivot_ant_base['Número de documento'].duplicated(keep='last')]

# proceso de actualización de antigenicas
counter_act = 0
nuevos = 0
if pivot_ant_base.shape[0]!=0:
    for index, row in resultado_ant_base.iterrows():
        indx = pivot_ant_base.loc[pivot_ant_base['Número de documento']==row['Número de documento'],'Resultado prueba antigenica'].index
        if indx.values.shape[0]==1:
            # traer el registro base
            registro_base = df_prass_base.loc[df_prass_base.index==indx.values[0]]
            # verificar que sea un registro nuevo
            if np.isnan(registro_base['Fecha prueba antigenica'].values[0]): 
                df_prass_base.loc[df_prass_base.index==indx.values[0], 'NOMBRE'] = row['NOMBRE']
                df_prass_base.loc[df_prass_base.index==indx.values[0], 'Fecha prueba antigenica'] = row['Fecha prueba antigenica']
                # sacar los dias diferencia - condiciona el resultado
                dias = (row['Fecha prueba antigenica']-registro_base['CreationDate']).dt.days+1
                if dias.values[0]>=0:
                    # cambiar fecha resultado
                    df_prass_base.loc[df_prass_base.index==indx.values[0], 'Resultado prueba antigenica'] = row['Resultado prueba antigenica']
                    # se agrega un día para hacer el ajuste en la resta (el sistema no cuenta el último día)
                    df_prass_base.loc[df_prass_base.index==indx.values[0], 'Dias diferencias pba antigenica'] = dias
                else:
                    df_prass_base.loc[df_prass_base.index==indx.values[0], 'Resultado prueba antigenica'] = 'Pendiente' 
                nuevos = nuevos + 1
            else:
                # quiere decir que ya hay una fecha por lo tanto mirar si la consulta arroja una nueva fecha
                # ademas verificar que no vengan fechas vacias
                if str(registro_base['Fecha prueba antigenica'].values[0])!='nan' and str(row['Fecha prueba antigenica'])!='nan':
                    if row['Fecha prueba antigenica'] > registro_base['Fecha prueba antigenica'].values[0]: 
                        df_prass_base.loc[df_prass_base.index==indx.values[0], 'Fecha prueba antigenica'] = row['Fecha prueba antigenica']  
                        dias = (row['Fecha prueba antigenica']-registro_base['CreationDate']).dt.days+1
                        if dias.values[0]>=0:
                            # se agrega un día para hacer el ajuste en la resta (el sistema no cuenta el último día)
                            df_prass_base.loc[df_prass_base.index==indx.values[0], 'Dias diferencias pba antigenica'] = dias
                            df_prass_base.loc[df_prass_base.index==indx.values[0], 'Resultado prueba antigenica'] = row['Resultado prueba antigenica']
                            counter_act = counter_act + 1 
                        else:
                            # fechas que son anteriores al prass se ponen pendiente
                            df_prass_base.loc[df_prass_base.index==indx.values[0], 'Resultado prueba antigenica'] = 'Pendiente' 
                        
        else:
            print(row)   

print('{} registros actualizado por parte de prueba antigenica'.format(counter_act))  
# categorización en antigenicas                      
if pivot_ant_base.shape[0]!=0:
    df_prass_base['Escala tiempo antigénica'] = df_prass_base['Dias diferencias pba antigenica'].apply(lambda x: categorizar_base(x))

print('Iniciando proceso final de concatención de histórico con el del día')
PRASS = pd.concat([df_prass_base,df_prass_dia]) 

PRASS.RESULTADO = PRASS.RESULTADO.str.strip() 
PRASS['Resultado prueba antigenica'] = PRASS['Resultado prueba antigenica'].str.strip()

PRASS.loc[(PRASS['Tipo de prueba de hisopado'].isnull()|PRASS['Tipo de prueba de hisopado'].isna())
            &(PRASS.RESULTADO.isin(['NEGATIVO', 'POSITIVO', 'Pendiente'])), 'Tipo de prueba de hisopado'] = 'PCR'

# cambiar antigénica por Antigénica
PRASS.RESULTADO = PRASS.RESULTADO.str.strip().str.replace("'","")

PRASS.loc[(PRASS['Tipo de prueba de hisopado'].isnull()|PRASS['Tipo de prueba de hisopado'].isna())
            &~(PRASS.RESULTADO.isin(['NEGATIVO', 'POSITIVO', 'Pendiente']))
            &(PRASS['Resultado prueba antigenica'].isin(['NEGATIVO', 'POSITIVO', 'Pendiente'])), 'Tipo de prueba de hisopado'] = 'Antigénica'


PRASS.loc[(PRASS['Municipio (Código)']== 68001.0)].to_excel('PRASS BUCARAMANGA 2020.xlsx', index=False, sheet_name='PRASS')
# corregir las fechas . Regla rafa buitrago
PRASS.loc[(PRASS['Municipio (Código)']== 68001.0), 'EditDate'] = PRASS.loc[(PRASS['Municipio (Código)']== 68001.0), 'EditDate'].dt.strftime('%d-%m-%Y')
PRASS.loc[(PRASS['Municipio (Código)']== 68001.0), 'CreationDate'] = PRASS.loc[(PRASS['Municipio (Código)']== 68001.0), 'CreationDate'].dt.strftime('%d-%m-%Y')
PRASS.loc[(PRASS['Municipio (Código)']== 68001.0), 'Fecha de nacimiento'] = PRASS.loc[(PRASS['Municipio (Código)']== 68001.0), 'Fecha de nacimiento'].dt.strftime('%d-%m-%Y')

# se le envia a rafa
PRASS.loc[(PRASS['Municipio (Código)']== 68001.0)].to_excel('PRASS BUCARAMANGA 2020_rafa.xlsx', index=False, sheet_name='PRASS')