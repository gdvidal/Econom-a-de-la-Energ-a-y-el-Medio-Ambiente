import numpy as np
from gurobipy import *
import datos

################ CAMBIAR VARIABLES PARA ANALIZAR LOS DIFERENTES CASOS #############

porcentaje_ernc = 30/100        #% de generación ERNC 2030  

Meta_ERNC = False               #Meta que fija un % de generación ERNC para el año 2030
Incentivo_ERNC = False          #Mejora tecnológica: disminución costos de inversión solar

################ ----------------------------------------------------###############

 
###### MODELO DE OPTIMIZACIÓN T1 ######

bloque= ['bloque1','bloque2','bloque3']
año = ['2016','2030']
renovable = ['Eolica 1','Eolica 2', 'Eolica 3', 'Solar FV 1','Solar FV 2', 'Solar FV 3','Geotermia','minihidro']
combustibles_set = ['Carbón', 'CC-GNL', 'Petróleo Diesel']

#INDICES
I = range(len(datos.Centrales()))       #centrales existentes
J = range(len(datos.CentralesNuevas())) #centrales nuevas
B = range(len(datos.DemandaGWh())-1)    #bloques demanda
T= range(2)                             #años: 2016 y 2030

model = Model()

#VARIABLES
E_ce= model.addVars(I, B, T)    #energía centrales existentes (MWh)
E_cn= model.addVars(J, B, T)    #energía centrales nuevas     (MWh)

Cap_ins = model.addVars(J,T)    # capacidad instalada nuevas centrales (MW)


##### RESTRICCIONES ######

# -- CENTRALES NUEVAS -- #

# 1.- [capacidad instalda de nuevas centrales es 0 en 2016]
model.addConstrs(Cap_ins[j,0] == 0 for j in J)

# 2.- [Restricción de máxima capacidad instalada centrales nuevas]
model.addConstrs(Cap_ins[j,1] <= datos.CentralesNuevas()[j]['RI_max'] for j in J if datos.CentralesNuevas()[j]['RI_max'] != 1000_000_000)


# -- MÁXIMA ENERGÍA POR CENTRAL -- #

# 3.- [Centrales Existentes]
model.addConstrs(E_ce[i,b,t]
                  <= datos.Centrales()[i]['disp']*datos.Centrales()[i]['P_neta']*datos.Duracion()[bloque[b]] for i in I for b in B for t in T)


# 4.- [Centrales Nuevas]
model.addConstrs(E_cn[j,b,1]
                   <= datos.CentralesNuevas()[j]['disp']*Cap_ins[j,1]*datos.Duracion()[bloque[b]] for j in J for b in B)


# -- DEMANDA GWh -- #

# 5.- [Demanda año 2016]
model.addConstrs(sum(E_ce[i,b,0] for i in I) 
                 >= datos.DemandaGWh()[bloque[b]][año[0]]*1000 for b in B)

# 6.- [Demanda año 2030]
model.addConstrs(sum(E_ce[i,b,1] for i in I) + sum(E_cn[j,b,1] for j in J) 
                 >= datos.DemandaGWh()[bloque[b]][año[1]]*1000 for b in B)


# 6.1 (*).- [Política Meta ERNC que fija un % tipo renovable respecto a la generación]
if Meta_ERNC == True: #2030
    
    model.addConstr( sum(sum(E_ce[i,b,1] for i in I if datos.Centrales()[i]['tecnologia'] in renovable) for b in B)
                    + sum(sum(E_cn[j,b,1] for j in J if datos.CentralesNuevas()[j]['tecnologia'] in renovable) for b in B)
                    >=  (porcentaje_ernc)* ( sum(sum(E_ce[i,b,1] for i in I) for b in B) + sum(sum(E_cn[j,b,1] for j in J) for b in B) ) )

                                    
#naturaleza variables
model.addConstrs(E_ce[i,b,t] >= 0 for i in I for b in B for t in T)
model.addConstrs(E_cn[j,b,t] >= 0 for j in J for b in B for t in T)
model.addConstrs(Cap_ins[j,t] >= 0 for j in J for t in T)


### FUNCION OBJETIVO ###

#caso base
if Incentivo_ERNC == False:                                                         
    C_var1 = sum(sum(datos.Centrales()[i]['CVT']* sum(E_ce[i,b,t] for b in B) for i in I) for t in T)       #costo variable centrales antiguas
    C_var2 = sum(sum(datos.CentralesNuevas()[j]['CVT']* sum(E_cn[j,b,t] for b in B) for j in J) for t in T) #costo variable centrales nuevas
    
    C_var = C_var1 + C_var2                                                                                 #costos variables totales
    #C_peaje = sum(datos.CentralesNuevas()[j]['LP']* sum(E_cn[j,b,1] for b in B) for j in J)                 #costo de linea centrales nuevas
    C_peaje = 0 #incluida en CVT
    
    CET = C_var + C_peaje                                                                                   #costo varible + costo linea
    CI = sum( Cap_ins[j,1]*1000 * datos.CentralesNuevas()[j]['A'] for j in J)                               #costos de inversión anualizados
    
    model.setObjective(CET + CI , GRB.MINIMIZE)                                                             #función objetivo: min. costos


#caso con incentivo tecnológico
elif Incentivo_ERNC == True:
    
    centrales_nuevas_ernc = datos.CentralesIncentivoERNC(True, datos.CentralesNuevas())                     #cambiar valor de anualidad (mejora tecnológica)
    
    
    C_var1 = sum(sum(datos.Centrales()[i]['CVT']* sum(E_ce[i,b,t] for b in B) for i in I) for t in T)       #costo variable centrales antiguas
    C_var2 = sum(sum(centrales_nuevas_ernc[j]['CVT']* sum(E_cn[j,b,t]for b in B) for j in J) for t in T)    #costo variable centrales nuevas
    
    C_var = C_var1 + C_var2                                                                                 #costos variables totales
    #C_peaje = sum(centrales_nuevas_ernc[j]['LP']* sum(E_cn[j,b,1] for b in B) for j in J)                   #costo de linea centrales nuevas
    C_peaje = 0 #incluida en CVT
    
    CET = C_var + C_peaje                                                                                   #costo varible + costo linea
    CI = sum( Cap_ins[j,1]*1000 * centrales_nuevas_ernc[j]['A'] for j in J)                                 #costos de inversión anualizados
    
    model.setObjective(CET + CI , GRB.MINIMIZE)                                                             #función objetivo: min. costos


model.optimize();



########################### MAIN #######################

# print("\n")

# print("Función Objetivo:",model.objVal/1000000, "MM USD")


gen16_biomasa=0
gen16_carbon=0
gen16_diesel=0
gen16_gnl=0
gen16_minihidro=0
gen16_hidro=0
gen16_wind=0
gen16_solar=0
gen16_falla=0
gen16_geotermica=0

gen30_biomasa=0
gen30_carbon=0
gen30_diesel=0
gen30_gnl=0
gen30_minihidro=0
gen30_hidro=0
gen30_wind=0
gen30_solar=0
gen30_falla=0
gen30_geotermica=0

gen30_biomasa2=0
gen30_carbon2=0
gen30_diesel2=0
gen30_gnl2=0
gen30_minihidro2=0
gen30_hidro2=0
gen30_wind2=0
gen30_solar2=0
gen30_falla2=0
gen30_geotermica2=0


#capacidad instalada 2016:
mw16_biomasa= 0
mw16_carbon=0
mw16_diesel=0
mw16_gnl=0
mw16_minihidro=0
mw16_hidro=0
mw16_wind=0
mw16_solar=0
mw16_falla=0
mw16_geotermica=0

#capacidad instalada ADICIONAL en 2030
mw30_biomasa=0
mw30_carbon=0
mw30_diesel=0
mw30_gnl=0
mw30_minihidro=0
mw30_hidro=0
mw30_wind=0
mw30_solar=0
mw30_falla=0
mw30_geotermica=0



#resultados 2016
for i in I:
    
    if datos.Centrales()[i]['tecnologia'] == 'Biomasa':
           
           mw16_biomasa+= datos.Centrales()[i]['P_neta']
           
           
    if datos.Centrales()[i]['tecnologia'] == 'Carbón':

       mw16_carbon+= datos.Centrales()[i]['P_neta']
       
  
    if datos.Centrales()[i]['tecnologia'] == 'CC-GNL':
        
        mw16_gnl+= datos.Centrales()[i]['P_neta']
           
        
    if datos.Centrales()[i]['tecnologia'] == 'Petróleo Diesel':
       
       mw16_diesel+= datos.Centrales()[i]['P_neta']

    if datos.Centrales()[i]['tecnologia'] == 'Hidro':
        
        mw16_hidro+= datos.Centrales()[i]['P_neta']
        
    if datos.Centrales()[i]['tecnologia'] == 'Eolica 1':
        
        mw16_wind+= datos.Centrales()[i]['P_neta']


    if datos.Centrales()[i]['tecnologia'] == 'Solar FV 1':
        
        mw16_solar+= datos.Centrales()[i]['P_neta']
        

    if datos.Centrales()[i]['tecnologia'] == 'Central de falla':
        
        mw16_falla+= datos.Centrales()[i]['P_neta']

    
    if datos.Centrales()[i]['tecnologia'] == 'Geotermia':
        
        mw16_geotermica+= datos.Centrales()[i]['P_neta']
        
        
    if datos.Centrales()[i]['tecnologia'] == 'minihidro':
        
        mw16_minihidro+= datos.Centrales()[i]['P_neta']
        


    for b in B:
         
        if datos.Centrales()[i]['tecnologia'] == 'Biomasa':
           
           gen16_biomasa+= E_ce[i,b,0].x/1000
           
           #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
           
        if datos.Centrales()[i]['tecnologia'] == 'Carbón':
           
           gen16_carbon+= E_ce[i,b,0].x/1000
           
           #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
           
        if datos.Centrales()[i]['tecnologia'] == 'CC-GNL':
            
            gen16_gnl+= E_ce[i,b,0].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
            
            
        if datos.Centrales()[i]['tecnologia'] == 'Petróleo Diesel':
           
           gen16_diesel+= E_ce[i,b,0].x/1000
           
           #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
                
        if datos.Centrales()[i]['tecnologia'] == 'Hidro':
            
            gen16_hidro+= E_ce[i,b,0].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")   
    

        if datos.Centrales()[i]['tecnologia'] == 'Eolica 1':
            
            gen16_wind+= E_ce[i,b,0].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh") 


        if datos.Centrales()[i]['tecnologia'] == 'Solar FV 1':
            
            gen16_solar+= E_ce[i,b,0].x/1000

            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")

    
        if datos.Centrales()[i]['tecnologia'] == 'Central de falla':
            
            gen16_falla+= E_ce[i,b,0].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
            
        if datos.Centrales()[i]['tecnologia'] == 'Geotermia':
            
            gen16_geotermica+= E_ce[i,b,0].x/1000

            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")

        if datos.Centrales()[i]['tecnologia'] == 'minihidro':
            
            gen16_minihidro+= E_ce[i,b,0].x/1000
        

#resultados 2030: centrales antiguas
for i in I:
    for b in B:
         
        if datos.Centrales()[i]['tecnologia'] == 'Biomasa':
           
           gen30_biomasa+= E_ce[i,b,1].x/1000
           
           #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
           
        if datos.Centrales()[i]['tecnologia'] == 'Carbón':
           
           gen30_carbon+= E_ce[i,b,1].x/1000
           
           #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
           
        if datos.Centrales()[i]['tecnologia'] == 'CC-GNL':
            
            gen30_gnl+= E_ce[i,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
            
            
        if datos.Centrales()[i]['tecnologia'] == 'Petróleo Diesel':
           
           gen30_diesel+= E_ce[i,b,1].x/1000
           
           #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
                
        if datos.Centrales()[i]['tecnologia'] == 'Hidro':
            
            gen30_hidro+= E_ce[i,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")   
    

        if datos.Centrales()[i]['tecnologia'] == 'Eolica 1':
            
            gen30_wind+= E_ce[i,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh") 


        if datos.Centrales()[i]['tecnologia'] == 'Solar FV 1':
            
            gen30_solar+= E_ce[i,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")

    
        if datos.Centrales()[i]['tecnologia'] == 'Central de falla':
            
            gen30_falla+= E_ce[i,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
            
            
        if datos.Centrales()[i]['tecnologia'] == 'Geotermia':
            
            gen30_geotermica+= E_ce[i,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")

        if datos.Centrales()[i]['tecnologia'] == 'minihidro':
            
            gen30_minihidro+= E_ce[i,b,1].x/1000
            
            
#resultados 2030: centrales nuevas
for j in J:
    
    if datos.CentralesNuevas()[j]['tecnologia'] == 'Biomasa':
           
           mw30_biomasa+= Cap_ins[j,1].x
           

    if datos.CentralesNuevas()[j]['tecnologia'] == 'Carbón':
       
       mw30_carbon+= Cap_ins[j,1].x


    if datos.CentralesNuevas()[j]['tecnologia'] == 'CC-GNL':
        
        mw30_gnl+= Cap_ins[j,1].x
        

    if datos.CentralesNuevas()[j]['tecnologia'] == 'Petróleo Diesel':
       
       mw30_diesel+= Cap_ins[j,1].x


    if datos.CentralesNuevas()[j]['tecnologia'] == 'minihidro':
        mw30_minihidro+= Cap_ins[j,1].x
        

    if datos.CentralesNuevas()[j]['tecnologia'] == 'Hidro' or datos.CentralesNuevas()[j]['tecnologia'] == 'Hidroelectricidad convencional':
        
        mw30_hidro+= Cap_ins[j,1].x
        

    if datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 1' or datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 2' or datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 3':
        
        mw30_wind+= Cap_ins[j,1].x
        

    if datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 1' or datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 2' or datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 3':
        
        mw30_solar+= Cap_ins[j,1].x
        

    if datos.CentralesNuevas()[j]['tecnologia'] == 'Central de falla':
        
        mw30_falla+= Cap_ins[j,1].x
        

    if datos.CentralesNuevas()[j]['tecnologia'] == 'Geotermia':
        
        mw30_geotermica+= Cap_ins[j,1].x
    
    
    for b in B:
         
        if datos.CentralesNuevas()[j]['tecnologia'] == 'Biomasa':
           
           gen30_biomasa2+= E_cn[j,b,1].x/1000
           
           #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
           
        if datos.CentralesNuevas()[j]['tecnologia'] == 'Carbón':
           
           gen30_carbon2+= E_cn[j,b,1].x/1000
           
           #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
           
        if datos.CentralesNuevas()[j]['tecnologia'] == 'CC-GNL':
            
            gen30_gnl2+= E_cn[j,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
            
            
        if datos.CentralesNuevas()[j]['tecnologia'] == 'Petróleo Diesel':
           
           gen30_diesel2+= E_cn[j,b,1].x/1000
           
           #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
           
        
        if datos.CentralesNuevas()[j]['tecnologia'] == 'minihidro':
            
            gen30_minihidro2 += E_cn[j,b,1].x/1000
        
        
        if datos.CentralesNuevas()[j]['tecnologia'] == 'Hidro' or datos.CentralesNuevas()[j]['tecnologia'] == 'Hidroelectricidad convencional':
            
            gen30_hidro2+= E_cn[j,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")   
    

        if datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 1' or datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 2' or datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 3':
            
            gen30_wind2+= E_cn[j,b,1].x/1000

            #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh") 


        if datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 1' or datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 2' or datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 3':
            
            gen30_solar2+= E_cn[j,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")

    
        if datos.CentralesNuevas()[j]['tecnologia'] == 'Central de falla':
            
            gen30_falla2+= E_cn[j,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")

        if datos.CentralesNuevas()[j]['tecnologia'] == 'Geotermia':
            
            gen30_geotermica2+= E_cn[j,b,1].x/1000
            
            #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")

gen30_biomasa_f= gen30_biomasa + gen30_biomasa2
gen30_carbon_f= gen30_carbon + gen30_carbon2
gen30_diesel_f= gen30_diesel + gen30_diesel2
gen30_gnl_f= gen30_gnl + gen30_gnl2
gen30_hidro_f= gen30_hidro + gen30_hidro2
gen30_wind_f= gen30_wind + gen30_wind2
gen30_solar_f= gen30_solar + gen30_solar2
gen30_falla_f= gen30_falla + gen30_falla2
gen30_geotermica_f= gen30_geotermica + gen30_geotermica2
gen30_minihidro_f = gen30_minihidro + gen30_minihidro2

totalmw30_biomasa= mw16_biomasa + mw30_biomasa
totalmw30_carbon= mw16_carbon + mw30_carbon
totalmw30_diesel= mw16_diesel + mw30_diesel
totalmw30_gnl= mw16_gnl + mw30_gnl
totalmw30_hidro= mw16_hidro + mw30_hidro
totalmw30_wind= mw16_wind + mw30_wind
totalmw30_solar= mw16_solar + mw30_solar
totalmw30_falla= mw16_falla + mw30_falla
totalmw30_geotermica= mw16_geotermica + mw30_geotermica
totalmw30_minihidro= mw16_minihidro + mw30_minihidro


#calculo emisiones descontroladas:
    
emisiones_MP = 0
emisiones_SOx = 0
emisiones_NOx = 0
emisiones_CO2 = 0

emisiones2030_MP = 0
emisiones2030_SOx = 0
emisiones2030_NOx = 0
emisiones2030_CO2 = 0

#diccionario con las emisiones descontroladas
emisiones2030_descontroladas_ce =[]
emisiones2030_descontroladas_cn =[]

#centrales antiguas 2016
for i in I:
    for b in B:
        
        if datos.Centrales()[i]['tecnologia'] in combustibles_set:
            
            if datos.Centrales()[i]['tecnologia'] == 'Carbón':
                emisiones_MP+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['MP']/(1000*1000000)
                emisiones_SOx+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['SOx']/(1000*1000000)
                emisiones_NOx+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['NOx']/(1000*1000000)
                emisiones_CO2+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['CO2']/(1000*1000000)
            
            if datos.Centrales()[i]['tecnologia'] == 'Petróleo Diesel':
                emisiones_MP+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['MP']/(1000*1000000)
                emisiones_SOx+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['SOx']/(1000*1000000)
                emisiones_NOx+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['NOx']/(1000*1000000)
                emisiones_CO2+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['CO2']/(1000*1000000)


            if datos.Centrales()[i]['tecnologia'] == 'CC-GNL':
                emisiones_MP+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['MP']/(1000*1000000)
                emisiones_SOx+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['SOx']/(1000*1000000)
                emisiones_NOx+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['NOx']/(1000*1000000)
                emisiones_CO2+= ((E_ce[i,b,0].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['CO2']/(1000*1000000)
    
    
#centrales antiguas 2030
for i in I:
    
    e_MP_carbon = 0
    e_SOx_carbon = 0
    e_NOx_carbon = 0
    e_CO2_carbon = 0
    
    e_MP_gnl = 0
    e_SOx_gnl = 0
    e_NOx_gnl = 0
    e_CO2_gnl = 0
    
    e_MP_diesel = 0
    e_SOx_diesel = 0
    e_NOx_diesel = 0
    e_CO2_diesel = 0
    
    
    for b in B:
        
        if datos.Centrales()[i]['tecnologia'] in combustibles_set:
            
            if datos.Centrales()[i]['tecnologia'] == 'Carbón':
                emisiones2030_MP+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['MP']/(1000*1000000)
                emisiones2030_SOx+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['SOx']/(1000*1000000)
                emisiones2030_NOx+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['NOx']/(1000*1000000)
                emisiones2030_CO2+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['CO2']/(1000*1000000)
                
                e_MP_carbon+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['MP']/(1000*1000000)
                e_SOx_carbon+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['SOx']/(1000*1000000)
                e_NOx_carbon+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['NOx']/(1000*1000000)
                e_CO2_carbon+=  ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['CO2']/(1000*1000000)
                
            
            if datos.Centrales()[i]['tecnologia'] == 'Petróleo Diesel':
                emisiones2030_MP+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['MP']/(1000*1000000)
                emisiones2030_SOx+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['SOx']/(1000*1000000)
                emisiones2030_NOx+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['NOx']/(1000*1000000)
                emisiones2030_CO2+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['CO2']/(1000*1000000)
                
                e_MP_diesel+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['MP']/(1000*1000000)
                e_SOx_diesel+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['SOx']/(1000*1000000)
                e_NOx_diesel+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['NOx']/(1000*1000000)
                e_CO2_diesel+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['CO2']/(1000*1000000)


            if datos.Centrales()[i]['tecnologia'] == 'CC-GNL':
                emisiones2030_MP+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['MP']/(1000*1000000)
                emisiones2030_SOx+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['SOx']/(1000*1000000)
                emisiones2030_NOx+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['NOx']/(1000*1000000)
                emisiones2030_CO2+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['CO2']/(1000*1000000)
                
                e_MP_gnl+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['MP']/(1000*1000000)
                e_SOx_gnl+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['SOx']/(1000*1000000)
                e_NOx_gnl+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['NOx']/(1000*1000000)
                e_CO2_gnl+= ((E_ce[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['CO2']/(1000*1000000)
                

    if datos.Centrales()[i]['tecnologia'] == 'Carbón':
        dic_emisiones_carbon = {'tecnologia': datos.Centrales()[i]['tecnologia'], 'ubicacion': datos.Centrales()[i]['ubicacion']
                                , 'emisiones_MP': e_MP_carbon , 'emisiones_SOx': e_SOx_carbon , 'emisiones_NOx': e_NOx_carbon , 'emisiones_CO2': e_CO2_carbon}
        
        emisiones2030_descontroladas_ce.append(dic_emisiones_carbon)


    if datos.Centrales()[i]['tecnologia'] == 'Petróleo Diesel':
        dic_emisiones_diesel = {'tecnologia': datos.Centrales()[i]['tecnologia'], 'ubicacion': datos.Centrales()[i]['ubicacion']
                                , 'emisiones_MP': e_MP_diesel , 'emisiones_SOx': e_SOx_diesel , 'emisiones_NOx': e_NOx_diesel , 'emisiones_CO2': e_CO2_diesel}
        
        emisiones2030_descontroladas_ce.append(dic_emisiones_diesel
                                            )
        
    if datos.Centrales()[i]['tecnologia'] == 'CC-GNL':
        dic_emisiones_gnl = {'tecnologia': datos.Centrales()[i]['tecnologia'], 'ubicacion': datos.Centrales()[i]['ubicacion']
                                , 'emisiones_MP': e_MP_gnl , 'emisiones_SOx': e_SOx_gnl , 'emisiones_NOx': e_NOx_gnl , 'emisiones_CO2': e_CO2_gnl}
        
               
        emisiones2030_descontroladas_ce.append(dic_emisiones_gnl)
    
    else:
        dic_no_contaminante = {'tecnologia': datos.Centrales()[i]['tecnologia'], 'ubicacion': datos.Centrales()[i]['ubicacion']
                                , 'emisiones_MP': 0 , 'emisiones_SOx': 0 , 'emisiones_NOx': 0 , 'emisiones_CO2': 0}
        
        emisiones2030_descontroladas_ce.append(dic_no_contaminante)
        
        

#centrales nuevas 2030
for i in J:
    
    e_MP_carbon_cn = 0
    e_SOx_carbon_cn = 0
    e_NOx_carbon_cn = 0
    e_CO2_carbon_cn = 0
    
    e_MP_gnl_cn = 0
    e_SOx_gnl_cn = 0
    e_NOx_gnl_cn = 0
    e_CO2_gnl_cn = 0
    
    e_MP_diesel_cn = 0
    e_SOx_diesel_cn = 0
    e_NOx_diesel_cn = 0
    e_CO2_diesel_cn = 0
    
    
    for b in B:
        
        if datos.CentralesNuevas()[i]['tecnologia'] in combustibles_set:
            
            if datos.CentralesNuevas()[i]['tecnologia'] == 'Carbón':
                emisiones2030_MP+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['MP']/(1000*1000000)
                emisiones2030_SOx+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['SOx']/(1000*1000000)
                emisiones2030_NOx+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['NOx']/(1000*1000000)
                emisiones2030_CO2+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['CO2']/(1000*1000000)
                
                e_MP_carbon_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['MP']/(1000*1000000)
                e_SOx_carbon_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['SOx']/(1000*1000000)
                e_NOx_carbon_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['NOx']/(1000*1000000)
                e_CO2_carbon_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Carbón']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['CO2']/(1000*1000000)
            
            if datos.CentralesNuevas()[i]['tecnologia'] == 'Petróleo Diesel':
                emisiones2030_MP+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['MP']/(1000*1000000)
                emisiones2030_SOx+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['SOx']/(1000*1000000)
                emisiones2030_NOx+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['NOx']/(1000*1000000)
                emisiones2030_CO2+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['CO2']/(1000*1000000)
                
                e_MP_diesel_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['MP']/(1000*1000000)
                e_SOx_diesel_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['SOx']/(1000*1000000)
                e_NOx_diesel_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['NOx']/(1000*1000000)
                e_CO2_diesel_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['Diesel']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['CO2']/(1000*1000000)


            if datos.CentralesNuevas()[i]['tecnologia'] == 'CC-GNL':
                emisiones2030_MP+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['MP']/(1000*1000000)
                emisiones2030_SOx+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['SOx']/(1000*1000000)
                emisiones2030_NOx+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['NOx']/(1000*1000000)
                emisiones2030_CO2+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['CO2']/(1000*1000000)
                
                e_MP_gnl_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['MP']/(1000*1000000)
                e_SOx_gnl_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['SOx']/(1000*1000000)
                e_NOx_gnl_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['NOx']/(1000*1000000)
                e_CO2_gnl_cn+= ((E_cn[i,b,1].x)*datos.PoderCalorifico()['GNL']/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['CO2']/(1000*1000000)


    if datos.CentralesNuevas()[i]['tecnologia'] == 'Carbón':
        dic_emisiones_carbon_cn = {'tecnologia': datos.CentralesNuevas()[i]['tecnologia'], 'ubicacion': datos.CentralesNuevas()[i]['ubicacion']
                                , 'emisiones_MP': e_MP_carbon_cn , 'emisiones_SOx': e_SOx_carbon_cn , 'emisiones_NOx': e_NOx_carbon_cn , 'emisiones_CO2': e_CO2_carbon_cn}
        
        emisiones2030_descontroladas_cn.append(dic_emisiones_carbon_cn)


    if datos.CentralesNuevas()[i]['tecnologia'] == 'Petróleo Diesel':
        dic_emisiones_diesel_cn = {'tecnologia': datos.CentralesNuevas()[i]['tecnologia'], 'ubicacion': datos.CentralesNuevas()[i]['ubicacion']
                                , 'emisiones_MP': e_MP_diesel_cn , 'emisiones_SOx': e_SOx_diesel_cn , 'emisiones_NOx': e_NOx_diesel_cn , 'emisiones_CO2': e_CO2_diesel_cn}
        
        emisiones2030_descontroladas_cn.append(dic_emisiones_diesel_cn)
        
    if datos.CentralesNuevas()[i]['tecnologia'] == 'CC-GNL':
        dic_emisiones_gnl_cn = {'tecnologia': datos.CentralesNuevas()[i]['tecnologia'], 'ubicacion': datos.CentralesNuevas()[i]['ubicacion']
                                , 'emisiones_MP': e_MP_gnl_cn , 'emisiones_SOx': e_SOx_gnl_cn , 'emisiones_NOx': e_NOx_gnl_cn , 'emisiones_CO2': e_CO2_gnl_cn}
        
        emisiones2030_descontroladas_cn.append(dic_emisiones_gnl_cn)

    else:
        dic_no_contaminante_cn = {'tecnologia': datos.CentralesNuevas()[i]['tecnologia'], 'ubicacion': datos.CentralesNuevas()[i]['ubicacion']
                                , 'emisiones_MP': 0 , 'emisiones_SOx': 0 , 'emisiones_NOx': 0 , 'emisiones_CO2': 0}
        
        emisiones2030_descontroladas_cn.append(dic_no_contaminante_cn)
        
print("\n EMISIONES DESCONTROLADAS año 2016\n")
print('MP: {} Mton'.format(emisiones_MP))
print('SOx: {} Mton'.format(emisiones_SOx))
print('NOx: {} Mton'.format(emisiones_NOx))
print('CO2: {} Mton'.format(emisiones_CO2))

print("\n EMISIONES DESCONTROLADAS año 2030\n")
print('MP: {} Mton'.format(emisiones2030_MP))
print('SOx: {} Mton'.format(emisiones2030_SOx))
print('NOx: {} Mton'.format(emisiones2030_NOx))
print('CO2: {} Mton'.format(emisiones2030_CO2))


#MOSTRAR DATOS ---------------------------------------------------------------------------------------

print('\nGeneración de Combustibles Año 2016\n')
print("Gen 2016 Carbon Existente: {} GWh".format(gen16_carbon))
print("Gen 2016 Carbon Nuevo: {} GWh".format(0))
print("Gen 2016 Diesel Existente: {} GWh".format(gen16_diesel))
print("Gen 2016 Diesel Nuevo: {} GWh".format(0))
print("Gen 2016 CC-GNL Existente: {} GWh".format(gen16_gnl))
print("Gen 2016 CC-GNL Nuevo: {} GWh".format(0))


print('\nGeneración de Combustibles Año 2030\n')
print("Gen 2030 Carbon Existente: {} GWh".format(gen30_carbon))
print("Gen 2030 Carbon Nuevo: {} GWh".format(gen30_carbon2))
print("Gen 2030 Diesel Existente: {} GWh".format(gen30_diesel))
print("Gen 2030 Diesel Nuevo: {} GWh".format(gen30_diesel2))
print("Gen 2030 CC-GNL Existente: {} GWh".format(gen30_gnl))
print("Gen 2030 CC-GNL Nuevo: {} GWh".format(gen30_gnl2))


print("\nGeneración 2016\n");
print("Gen Biomasa {} GWh".format(gen16_biomasa));
print("Gen Carbón {} GWh".format(gen16_carbon)); 
print("Gen CC-GNL {} GWh".format(gen16_gnl));
print("Gen Petroleo Diesel {} GWh".format(gen16_diesel)); 
print("Gen Hidro {} GWh".format(gen16_hidro)); 
print("Gen Solar {} GWh".format(gen16_solar));
print("Gen Eolica {} GWh".format(gen16_wind)); 
print("Gen Falla {} GWh".format(gen16_falla));
print("Gen Geotermia {} GWh".format(gen16_geotermica));
print("Gen Minihidro {} GWh".format(gen16_minihidro));

print("\nGeneración 2030\n");
print("Gen Biomasa {} GWh".format(gen30_biomasa_f));
print("Gen Carbón {} GWh".format(gen30_carbon_f)); 
print("Gen CC-GNL {} GWh".format(gen30_gnl_f));
print("Gen Petroleo Diesel {} GWh".format(gen30_diesel_f)); 
print("Gen Hidro {} GWh".format(gen30_hidro_f)); 
print("Gen Solar {} GWh".format(gen30_solar_f));
print("Gen Eolica {} GWh".format(gen30_wind_f)); 
print("Gen Falla {} GWh".format(gen30_falla_f));
print("Gen Geotermia {} GWh".format(gen30_geotermica_f));
print("Gen Minihidro {} GWh".format(gen30_minihidro_f));

print("\nCapacidad Instalada 2016\n");
print("Pot Biomasa {} MW".format(mw16_biomasa));
print("Pot Carbón {} MW".format(mw16_carbon)); 
print("Pot CC-GNL {} MW".format(mw16_gnl));
print("Pot Petroleo Diesel {} MW".format(mw16_diesel)); 
print("Pot Hidro {} MW".format(mw16_hidro)); 
print("Pot Solar {} MW".format(mw16_solar));
print("Pot Eolica {} MW".format(mw16_wind)); 
print("Pot Falla {} MW".format(mw16_falla));
print("Pot Geotermia {} MW".format(mw16_geotermica));
print("Pot Minihidro {} MW".format(mw16_minihidro));


print("\nCapacidad Instalada AGREGADA 2030\n");
print("Pot Biomasa {} MW".format(mw30_biomasa));
print("Pot Carbón {} MW".format(mw30_carbon)); 
print("Pot CC-GNL {} MW".format(mw30_gnl));
print("Pot Petroleo Diesel {} MW".format(mw30_diesel)); 
print("Pot Hidro {} MW".format(mw30_hidro)); 
print("Pot Solar {} MW".format(mw30_solar));
print("Pot Eolica {} MW".format(mw30_wind)); 
print("Pot Falla {} MW".format(mw30_falla));
print("Pot Geotermia {} MW".format(mw30_geotermica));
print("Pot Minihidro {} MW".format(mw30_minihidro));


print("\nCapacidad Instalada 2030\n");
print("Pot Biomasa {} MW".format(totalmw30_biomasa));
print("Pot Carbón {} MW".format(totalmw30_carbon)); 
print("Pot CC-GNL {} MW".format(totalmw30_gnl));
print("Pot Petroleo Diesel {} MW".format(totalmw30_diesel)); 
print("Pot Hidro {} MW".format(totalmw30_hidro)); 
print("Pot Solar {} MW".format(totalmw30_solar));
print("Pot Eolica {} MW".format(totalmw30_wind)); 
print("Pot Falla {} MW".format(totalmw30_falla));
print("Gen Geotermia {} MW".format(totalmw30_geotermica));
print("Gen Minihidro {} MW".format(totalmw30_minihidro));

print("\n")
for j in J:
    print("Tipo: {}".format(datos.CentralesNuevas()[j]['tecnologia']), ", Ubicación: {}".format(datos.CentralesNuevas()[j]['ubicacion']), 
          " , Capacidad Instalada Ad: {}".format(Cap_ins[j,1].x))
        

#generacion del tipo ERNC por año
gen_ernc_16 = gen16_geotermica + gen16_wind + gen16_solar + gen16_minihidro
gen_ernc_30= gen30_geotermica_f + gen30_wind_f + gen30_solar_f + gen30_minihidro_f

gen_total_16= gen16_biomasa + gen16_carbon + gen16_gnl + gen16_diesel + gen16_hidro + gen16_solar + gen16_wind + gen16_geotermica + gen16_falla + gen16_minihidro
gen_total_30= gen30_biomasa_f + gen30_carbon_f + gen30_gnl_f + gen30_diesel_f + gen30_hidro_f + gen30_solar_f + gen30_wind_f + gen30_geotermica_f + gen30_falla_f + gen30_minihidro_f

print("\n")
print("Generación ERNC 2016 = {}".format(gen_ernc_16))
print("Generación ERNC 2030 = {}".format(gen_ernc_30))
print("\n")
print("Generación total 2016: {}".format(gen_total_16))
print("Generación total 2030: {}".format(gen_total_30))
print("\n")
print("% ERNC 2030: {} %".format((gen_ernc_30/gen_total_30)*100))



# -----------------------------------------------------------------------------------------------------------#

