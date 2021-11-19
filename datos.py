import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile

'**** GLOSARIO ****'

"CF = Costo Fijo de Construcción"
"CVNC = Costo Variable No Combustible"
"CVC = Costo Variable Combustible"
"CVT = Costo Variable Total"
"RI_max = Restricción de Máxima Instalación"
"A = Anualidad"


global data, centrales, f_emision, demanda_page, combustibles
global columas, columnas2, columnas3,columnas4, columnas5 

data ='C:/Users/Guillermo/OneDrive - uc.cl/Material Universidad\Ramos/2021-II/Economía Energía - Medio Ambiente/Tareas/Tarea 2/Datos.xlsx'

##### Hojas del Archivo Excel #######

centrales = pd.read_excel(data, sheet_name='Centrales')
demanda_page = pd.read_excel(data, sheet_name='Demanda')
combustibles = pd.read_excel(data, sheet_name='Combustibles')
f_emision = pd.read_excel(data, sheet_name='Factores emisión')
abatidores_page = pd.read_excel(data, sheet_name='Abatimiento')
daño_ambiental_page = pd.read_excel(data, sheet_name='Daño ambiental')

columnas = centrales.columns
columnas2= f_emision.columns
columnas3= demanda_page.columns
columnas4= abatidores_page.columns
columnas5= daño_ambiental_page.columns


def CentralesIncentivoERNC (bool_incentivo, dic_centrales_new):

    ERNC_incentivo = bool_incentivo #REDUCCION DE $/kW-neto Solar
    
    ##### APLICACION DE POLITICA ENERGÉTICA ######

    if (ERNC_incentivo == True):
        
        for i in range(0, len(dic_centrales_new)):
            
            if (dic_centrales_new[i]['tecnologia'] == 'Solar FV 2'):
                dic_centrales_new[i]['CI'] = 700
                dic_centrales_new[i]['A'] = centrales[columnas[15]][37]
                
            elif (dic_centrales_new[i]['tecnologia'] == 'Solar FV 3'):
                dic_centrales_new[i]['CI'] = 700
                dic_centrales_new[i]['A'] = centrales[columnas[15]][38]
            
    
    return dic_centrales_new
    
    

def Centrales ():
    
    lista_centrales = []
    
    ####### Centrales Existentes ########
    
    for i in range (6,28):
        
        central_ex=[]
        
        for j in range (1,20):
            
            central_ex.append(centrales[columnas[j]][i])
            
        lista_centrales.append(central_ex)
        
    
    dic_centrales =[] #lista con diccionario con las centrales existentes
    for i in range(0,len(lista_centrales)):
        
        ce = {'tecnologia': lista_centrales[i][0], 'ubicacion': lista_centrales[i][1], 'P_neta': lista_centrales[i][2], 'eff': lista_centrales[i][3],'CVNC': 
              lista_centrales[i][4], 'disp': lista_centrales[i][5], 'CVT': lista_centrales[i][6], 'CVC': lista_centrales[i][7], 
              'FEMI_MP': lista_centrales[i][8], 'FEMI_SOx': lista_centrales[i][9], 'FEMI_NOx': lista_centrales[i][10], 'FEMI_CO2': lista_centrales[i][11],
              'Norma_MP': lista_centrales[i][12], 'Norma_SOx': lista_centrales[i][13], 'Norma_NOx': lista_centrales[i][14], 
              'C_social_MP': lista_centrales[i][15], 'C_social_SOx': lista_centrales[i][16], 'C_social_NOx': lista_centrales[i][17], 'C_social_CO2': lista_centrales[i][18],}
        
        dic_centrales.append(ce)
        
    return dic_centrales

def Pneta():

    ######## POTENCIA NETA POR TECNOLOGÍA #########
    
    P_neta_value = []
    for i in range (32,41):
        
        for j in range (3,4):
            
            P_neta_value.append(centrales[columnas[j]][i])
            
    #print(P_neta_value)
        
    P_neta = {'Biomasa': P_neta_value[0], 'Carbón': P_neta_value[1], 'CC-GNL': P_neta_value[2], 'Petróleo Diesel': P_neta_value[3],
              'Hidro': P_neta_value[4],'Eolica': P_neta_value[5],'Solar':P_neta_value[6],'total':P_neta_value[8]}
    
    return P_neta
            

###### NUEVAS CENTRALES #######

def CentralesNuevas():
    
    l_nuevas_centrales =[]
    
    for i in range (45,65):
        
        central_new=[]
        
        for j in range (1,25):
            
            central_new.append(centrales[columnas[j]][i])
            
        l_nuevas_centrales.append(central_new)
        
    dic_centrales_new= []
    
    for i in range(0,len(l_nuevas_centrales)):
        
        c_new = {'tecnologia': l_nuevas_centrales[i][0], 'ubicacion': l_nuevas_centrales[i][1], 'CI': l_nuevas_centrales[i][2], 'vida_util': l_nuevas_centrales[i][3],'tasa_dcto': 
              l_nuevas_centrales[i][4], 'LP': l_nuevas_centrales[i][5], 'eff': l_nuevas_centrales[i][6], 'CVNC': l_nuevas_centrales[i][7], 'disp': l_nuevas_centrales[i][8],
              'RI_max': l_nuevas_centrales[i][9], 'A': l_nuevas_centrales[i][10], 'CVT': l_nuevas_centrales[i][11], 'CVC': l_nuevas_centrales[i][12], 
              'FEMI_MP': l_nuevas_centrales[i][13], 'FEMI_SOx': l_nuevas_centrales[i][14], 'FEMI_NOx': l_nuevas_centrales[i][15], 'FEMI_CO2': l_nuevas_centrales[i][16],
              'Norma_MP': l_nuevas_centrales[i][17], 'Norma_SOx': l_nuevas_centrales[i][18], 'Norma_NOx': l_nuevas_centrales[i][19], 
              'C_social_MP': l_nuevas_centrales[i][20], 'C_social_SOx': l_nuevas_centrales[i][21], 'C_social_NOx': l_nuevas_centrales[i][22], 'C_social_CO2': l_nuevas_centrales[i][23],}
        
        dic_centrales_new.append(c_new)
    
    return dic_centrales_new
    

def DemandaGWh():
    
    ############ DEMANDA ############
    dem_gwh=[]
    
    for i in range (10,14):
        
        bloque=[]
        
        for j in range (6,21):
            
            bloque.append(demanda_page[columnas3[j]][i])
            
        dem_gwh.append(bloque)
        
    
    dem_gwh_d =[]
    
    for i in range(0,len(dem_gwh)):
        
        b = {'2016': dem_gwh[i][0], '2017': dem_gwh[i][1],'2018': dem_gwh[i][2],'2019': dem_gwh[i][3],'2020': dem_gwh[i][4],'2021': dem_gwh[i][5],'2022': dem_gwh[i][6],
             '2023': dem_gwh[i][7],'2024': dem_gwh[i][8],'2025': dem_gwh[i][9],'2026': dem_gwh[i][10],'2027': dem_gwh[i][11],'2028': dem_gwh[i][12],'2029': dem_gwh[i][13],
             '2030': dem_gwh[i][14]}    
    
        dem_gwh_d.append(b)
        
    dic_bloques= {'bloque1': dem_gwh_d[0],'bloque2': dem_gwh_d[1],'bloque3': dem_gwh_d[2],
                  'total': dem_gwh_d[3]}
    
    return dic_bloques
    #return dem_gwh
        
    
    
def DemandaMW():
    ############ DEMANDA MW ############
    dem_gwh=[]
    
    for i in range (17,21):
        
        bloque=[]
        
        for j in range (6,21):
            
            bloque.append(demanda_page[columnas3[j]][i])
            
        dem_gwh.append(bloque)
        
    
    dem_gwh_d =[]
    
    for i in range(0,len(dem_gwh)):
        
        b = {'2016': dem_gwh[i][0], '2017': dem_gwh[i][1],'2018': dem_gwh[i][2],'2019': dem_gwh[i][3],'2020': dem_gwh[i][4],'2021': dem_gwh[i][5],'2022': dem_gwh[i][6],
             '2023': dem_gwh[i][7],'2024': dem_gwh[i][8],'2025': dem_gwh[i][9],'2026': dem_gwh[i][10],'2027': dem_gwh[i][11],'2028': dem_gwh[i][12],'2029': dem_gwh[i][13],
             '2030': dem_gwh[i][14]}    
    
        dem_gwh_d.append(b)
        
    dic_bloques= {'bloque1': dem_gwh_d[0],'bloque2': dem_gwh_d[1],'bloque3': dem_gwh_d[2],
                  'total': dem_gwh_d[3]}
    
    return dic_bloques
    
    
def Duracion():
    
    b1= demanda_page[columnas3[2]][2]
    b2= demanda_page[columnas3[2]][3]
    b3= demanda_page[columnas3[2]][4]
    
    dur={'bloque1': b1, 'bloque2':b2, 'bloque3':b3}
    
    return dur

######## ---- Datos ambientales ---- ########

def Emisiones():
    
    ######## FACTOR EMISIONES #########
    
    emisiones =[]
    
    for i in range (5,11):
        
        emision_p=[]
        
        for j in range (1,6):
            
            emision_p.append(f_emision[columnas2[j]][i])
            
        emisiones.append(emision_p)
        
    dic_emisiones= []
    
    for i in range(0,len(emisiones)):
        
        em = {'tecnologia': emisiones[i][0],'MP': emisiones[i][1], 'SOx': emisiones[i][2], 'NOx': emisiones[i][3], 'CO2':emisiones[i][4]}
        
        dic_emisiones.append(em)
        
    return dic_emisiones


def PoderCalorifico():
    
    #VALORES EN Kgr/MWh
    
    p_cal = []
    
    for i in range (16,19):
        
        for j in range (5,6):
            p_cal.append(f_emision[columnas2[j]][i])
    
    
    dic_poder_cal = {'Diesel': p_cal[0], 'Carbón': p_cal[1], 'GNL': p_cal[2]}
    
    return dic_poder_cal 
    
    

def Abatidores():
    
    abatidor_NOx = []
    abatidor_MP = []
    abatidor_SOx = []
    
    abatidores = []
    dic_abatidores = []
    
    #NOx
    for i in range(3,6):
        
        ab_nox = []
        
        for j in range(1,6):
            
            ab_nox.append(abatidores_page[columnas4[j]][i])
        
        abatidor_NOx.append(ab_nox)
       
    #MP
    for i in range(10,13):
        
        ab_mp = []
        
        for j in range(1,6):
            
            ab_mp.append(abatidores_page[columnas4[j]][i])
        
        abatidor_MP.append(ab_mp)  
            
    #SOx
    for i in range(17,20):
        
        ab_sox = []
        
        for j in range(1,6):
            
            ab_sox.append(abatidores_page[columnas4[j]][i])
        
        abatidor_SOx.append(ab_sox)  
        
    
    abatidores.append(abatidor_NOx)
    abatidores.append(abatidor_MP)
    abatidores.append(abatidor_SOx)
    
    
    for i in range(0,len(abatidores)):
        
        for j in range(0,len(abatidores)):
        
            ab = {'abatidor': abatidores[i][j][0], 'eff': abatidores[i][j][1], 'I': abatidores[i][j][2], 'CVT': abatidores[i][j][3], 'A':abatidores[i][j][4]}
            
            dic_abatidores.append(ab)
        
    return dic_abatidores


def NormaEmisiones():
    
    norma = []
    norma_d=[]
    dic_norma= []
    
    for i in range(32,35):
        
        norm_comb = []
        
        for j in range(1,5):
            
            norm_comb.append(abatidores_page[columnas4[j]][i])
        
        norma.append(norm_comb)
        
    for i in range(0,len(norma)):
        
        norma_d= {'tecnologia': norma[i][0], 'MP': norma[i][1], 'SOx':norma[i][2], 'NOx':norma[i][3]}
        
        dic_norma.append(norma_d)
      
    
    return dic_norma
        

def DañoAmbiental():
    
    daño_sector = []
    
    dic_daño = []
    
    for i in range(4,17):
        
        daño =[]
        
        for j in range(1,6):
            
            daño.append(daño_ambiental_page[columnas5[j]][i])
        
        daño_sector.append(daño)
        
    for k in range(0,len(daño_sector)):
        
        daño_ciudad = {'ubicacion': daño_sector[k][0], 'MP': daño_sector[k][1], 'SOx': daño_sector[k][2], 'NOx': daño_sector[k][3], 'CO2': daño_sector[k][4]}
        
        dic_daño.append(daño_ciudad)
        
    
    return dic_daño
    

def CombAbatidores():
    
    comb = []
    dic_comb = []
    
    for i in range(1, 65):
        
        comb_p = []
        
        for j in range(12, 21):
            
            comb_p.append(abatidores_page[columnas4[j]][i])
        
        comb.append(comb_p)
    
    for k in range(0,len(comb)):
        
        filtros = {'id': comb[k][0], 'f1': comb[k][1], 'f2': comb[k][2], 'f3': comb[k][3], 
                   'eff-MP': comb[k][4], 'eff-NOx': comb[k][5], 'eff-SOx': comb[k][6],
                   'CVT': comb[k][7], 'A': comb[k][8]}
        
        dic_comb.append(filtros)
    
    return dic_comb
    