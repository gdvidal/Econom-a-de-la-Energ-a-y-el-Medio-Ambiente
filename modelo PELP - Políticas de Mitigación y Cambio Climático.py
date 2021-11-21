import numpy as np
from gurobipy import *
import datos

################ CAMBIAR VARIABLES PARA ANALIZAR LOS DIFERENTES CASOS #############

BAU = False                     #Caso Base: incluye Norma Termoeléctricas y Meta mitigación de CO2
Politica_Eficiente = True     #Fija un Costo por Daño Social en Cada Barra del Sistema: Eficiente Ambiental y Cambio Climático


if BAU == True:
    Norma_Termoelectrica = True    #Norma Command and Control: Fija un cierto % de abatimiento según sustancia (MP, SOx, NOx)
    Meta_CO2 = True                #Fija meta de reducción de un % de CO2 al 2030

    Politica_CO2 = 25/100;         #0%, 5%, 10%, 15%, 20% y 25%

else:
    Norma_Termoelectrica = False
    Meta_CO2 = False
    
################ ----------------------------------------------------###############


#PARÁMETROS 
Abatidores_NOx = ['NOx-1', 'NOx-2', 'NOx-3']
Abatidores_MP = ['MP-1', 'MP-2', 'MP-3']
Abatidores_SOx = ['SOx-1', 'SOx-2', 'SOx-3']

EmisionesBAU_CO2 = 20505.02*1000                #Emisiones de CO2 caso BAU

###### MODELO DE OPTIMIZACIÓN ######

bloque= ['bloque1','bloque2','bloque3']
año = ['2016','2030']                                                                                               #Para efectos de esta tarea, sólo se considera el año 2030.
renovable = ['Eolica 1','Eolica 2', 'Eolica 3', 'Solar FV 1','Solar FV 2', 'Solar FV 3','Geotermia','minihidro']
combustibles_set = ['Carbón', 'CC-GNL', 'Petróleo Diesel']

#INDICES
I = range(len(datos.Centrales()))       #centrales existentes
J = range(len(datos.CentralesNuevas())) #centrales nuevas
B = range(len(datos.DemandaGWh())-1)    #bloques demanda
F = range(len(datos.CombAbatidores()))  #64 combinaciones de abatidores

model = Model()

#VARIABLES
E_ce= model.addVars(I, B, F)    #energía centrales existentes (MWh)
E_cn= model.addVars(J, B, F)    #energía centrales nuevas     (MWh)

Cap_ins = model.addVars(J,F)    # capacidad instalada nuevas centrales (MW)
P_ce = model.addVars(I, B ,F)   #potencia despachada de centrales existentes (MW)
P_max_ce = model.addVars(I, F)  #maxima potencia despachada centrales existentes (MW)

##### RESTRICCIONES ######

#máxima potencia despachada de las centrales existentes(MW)
model.addConstrs(sum(P_ce[i,b,f] for f in F) <= datos.Centrales()[i]['P_neta']*datos.Centrales()[i]['disp'] for i in I for b in B)


#mayor potencia despachada en todos los bloques para una central existente
model.addConstrs(P_max_ce[i,f] >= P_ce[i,b,f] for i in I for f in F for b in B)


# -- CENTRALES NUEVAS -- #

# 2.- [Restricción de máxima capacidad instalada centrales nuevas]
model.addConstrs(sum(Cap_ins[j,f] for f in F) <= datos.CentralesNuevas()[j]['RI_max'] for j in J if datos.CentralesNuevas()[j]['RI_max'] != 1000_000_000)


# -- MÁXIMA ENERGÍA POR CENTRAL -- #

# 3.- [Centrales Existentes]
model.addConstrs(E_ce[i,b,f]
                  <= P_ce[i,b,f]*datos.Duracion()[bloque[b]] for i in I for b in B for f in F)


# 4.- [Centrales Nuevas]
model.addConstrs(E_cn[j,b,f]
                    <= datos.CentralesNuevas()[j]['disp']*Cap_ins[j,f]*datos.Duracion()[bloque[b]] for j in J for b in B for f in F)


# -- DEMANDA GWh -- #

# 6.- [Demanda año 2030]
model.addConstrs(sum(sum(E_ce[i,b,f] for f in F) for i in I) + sum(sum(E_cn[j,b,f] for f in F) for j in J) 
                  >= datos.DemandaGWh()[bloque[b]][año[1]]*1000 for b in B)

  
if Norma_Termoelectrica == True:
    
    # Centrales Antiguas
    
    #7.1.- MP
    model.addConstrs( (E_ce[i,b,f]*datos.Centrales()[i]['FEMI_MP']/1000)*(1-datos.CombAbatidores()[f]['eff-MP'])
                      <= E_ce[i,b,f]*datos.Centrales()[i]['FEMI_MP']/1000*(1 - datos.Centrales()[i]['Norma_MP'])
                    for i in I for b in B for f in F)
     
    #7.2.- SOx
    model.addConstrs( (E_ce[i,b,f]*datos.Centrales()[i]['FEMI_SOx']/1000)*(1-datos.CombAbatidores()[f]['eff-SOx'])
                      <= E_ce[i,b,f]*datos.Centrales()[i]['FEMI_SOx']/1000*(1 - datos.Centrales()[i]['Norma_SOx'])
                    for i in I for b in B for f in F)
    
    #7.3.-NOx
    model.addConstrs( (E_ce[i,b,f]*datos.Centrales()[i]['FEMI_NOx']/1000)*(1-datos.CombAbatidores()[f]['eff-NOx'])
                      <= E_ce[i,b,f]*datos.Centrales()[i]['FEMI_NOx']/1000*(1 - datos.Centrales()[i]['Norma_NOx'])
                    for i in I for b in B for f in F)
    
    
    #### Centrales Nuevas ####
    
    #8.1.- MP
    model.addConstrs( (E_cn[j,b,f]*datos.CentralesNuevas()[j]['FEMI_MP']/1000)*(1-datos.CombAbatidores()[f]['eff-MP'])
                      <= E_cn[j,b,f]*datos.CentralesNuevas()[j]['FEMI_MP']/1000*(1 - datos.CentralesNuevas()[j]['Norma_MP'])
                    for j in J for b in B for f in F)

    #8.1.- SOx
    model.addConstrs( (E_cn[j,b,f]*datos.CentralesNuevas()[j]['FEMI_SOx']/1000)*(1-datos.CombAbatidores()[f]['eff-SOx'])
                      <= E_cn[j,b,f]*datos.CentralesNuevas()[j]['FEMI_SOx']/1000*(1 - datos.CentralesNuevas()[j]['Norma_SOx'])
                    for j in J for b in B for f in F)
    
    #8.1.- NOx
    model.addConstrs( (E_cn[j,b,f]*datos.CentralesNuevas()[j]['FEMI_NOx']/1000)*(1-datos.CombAbatidores()[f]['eff-NOx'])
                      <= E_cn[j,b,f]*datos.CentralesNuevas()[j]['FEMI_NOx']/1000*(1 - datos.CentralesNuevas()[j]['Norma_NOx'])
                    for j in J for b in B for f in F)

    # --------    

if Meta_CO2 == True:
    
    #9.1 REDUCCIÓN DE EMISIONES de CO2:
    model.addConstr( sum(E_ce[i,b,f]*datos.Centrales()[i]['FEMI_CO2']/1000 for i in I for b in B for f in F) 
                     + sum(E_cn[j,b,f]*datos.CentralesNuevas()[j]['FEMI_CO2']/1000 for j in J for b in B for f in F)                   
                    <= EmisionesBAU_CO2*(1 - Politica_CO2))
    
 
# #naturaleza variables
# model.addConstrs(E_ce[i,b,f] >= 0 for i in I for b in B for f in F)
# model.addConstrs(E_cn[j,b,f] >= 0 for j in J for b in B for f in F)
# model.addConstrs(Cap_ins[j,f] >= 0 for j in J for f in F)
# model.addConstrs(P_ce[i,b,f] >= 0 for i in I for b in B for f in F)
# model.addConstrs(P_max_ce[i,f] >= 0 for i in I for f in F)

######## FUNCION OBJETIVO #########

if True:                    
    
    C_var1 = sum(datos.Centrales()[i]['CVT']* sum(sum(E_ce[i,b,f] for b in B) for f in F) for i in I)        #costo variable centrales antiguas
    C_var2 = sum(datos.CentralesNuevas()[j]['CVT']* sum(sum(E_cn[j,b,f] for b in B) for f in F) for j in J)  #costo variable centrales nuevas
    
    C_var3 = sum(datos.CombAbatidores()[f]['CVT']* sum(sum(E_ce[i,b,f] for b in B) for i in I) for f in F)   #costo variable abatidores centrales antiguas
    C_var4 = sum(datos.CombAbatidores()[f]['CVT']* sum(sum(E_cn[j,b,f] for b in B) for j in J) for f in F)   #costo variable abatidores centrales nuevas
    
    C_var = C_var1 + C_var2 + C_var3 + C_var4                                                                #costos variables totales
    #C_peaje = sum(datos.CentralesNuevas()[j]['LP']* sum(E_cn[j,b,1] for b in B) for j in J)                 #costo de linea centrales nuevas
    C_peaje = 0 #incluida en CVT
    
    CET = C_var + C_peaje                                                                                   #costo varible + costo linea
    
    CI_1 = sum(sum(Cap_ins[j,f] for f in F)*1000 * datos.CentralesNuevas()[j]['A'] for j in J)              #costos de inversión centrales nuevas anualizados
    CI_2 = sum(P_max_ce[i,f]*1000*datos.CombAbatidores()[f]['A'] for f in F for i in I)                     #costo de inversion abatidores centrales existentes
    CI_3= sum(Cap_ins[j,f]*1000*datos.CombAbatidores()[f]['A'] for f in F for j in J)                       #costo de inversion abatidores centrales nuevas
    
    CI = CI_1 + CI_2 + CI_3                                                                                 #costos de inversiones totales (centrales + abatidores)
    
    if Politica_Eficiente == True: 
        
        #Costo por Daño Social: CENTRALES ANTIGUAS
        C_sociales_1 =  sum(sum(sum(E_ce[i,b,f]*datos.Centrales()[i]['FEMI_MP']/1000*(1- datos.CombAbatidores()[f]['eff-MP'])*datos.Centrales()[i]['C_social_MP'] for b in B) for f in F) for i in I) 
        C_sociales_2 =  sum(sum(sum(E_ce[i,b,f]*datos.Centrales()[i]['FEMI_SOx']/1000*(1- datos.CombAbatidores()[f]['eff-SOx'])*datos.Centrales()[i]['C_social_SOx'] for b in B) for f in F) for i in I)  
        C_sociales_3 =  sum(sum(sum(E_ce[i,b,f]*datos.Centrales()[i]['FEMI_NOx']/1000*(1- datos.CombAbatidores()[f]['eff-NOx'])*datos.Centrales()[i]['C_social_NOx'] for b in B) for f in F) for i in I)   
        C_sociales_4 =  sum(sum(sum(E_ce[i,b,f]*datos.Centrales()[i]['FEMI_CO2']/1000*datos.Centrales()[i]['C_social_CO2'] for b in B) for f in F) for i in I)
    
        #Costos por Daño Social: CENTRALES Nuevas
        C_sociales_5 =  sum(sum(sum(E_cn[i,b,f]*datos.CentralesNuevas()[i]['FEMI_MP']/1000*(1- datos.CombAbatidores()[f]['eff-MP'])*datos.CentralesNuevas()[i]['C_social_MP'] for b in B) for f in F) for i in J) 
        C_sociales_6 =  sum(sum(sum(E_cn[i,b,f]*datos.CentralesNuevas()[i]['FEMI_SOx']/1000*(1- datos.CombAbatidores()[f]['eff-SOx'])*datos.CentralesNuevas()[i]['C_social_SOx'] for b in B) for f in F) for i in J)   
        C_sociales_7 =  sum(sum(sum(E_cn[i,b,f]*datos.CentralesNuevas()[i]['FEMI_NOx']/1000*(1- datos.CombAbatidores()[f]['eff-NOx'])*datos.CentralesNuevas()[i]['C_social_NOx'] for b in B) for f in F) for i in J)                                                                 #costos de inversiones totales (centrales + abatidores)
        C_sociales_8 =  sum(sum(sum(E_cn[i,b,f]*datos.CentralesNuevas()[i]['FEMI_CO2']/1000*datos.CentralesNuevas()[i]['C_social_CO2'] for b in B) for f in F) for i in J)
        
        C_sociales = C_sociales_1 + C_sociales_2 + C_sociales_3 + C_sociales_4 + C_sociales_5 + C_sociales_6 + C_sociales_7 + C_sociales_8
    
        model.setObjective(CET + CI + C_sociales, GRB.MINIMIZE)                                              #minimizar costos considerando daño social
        
    else:
    
        model.setObjective(CET + CI , GRB.MINIMIZE)                                                          #función objetivo: min. costos sin daño social

    
model.optimize();

########################### MAIN #######################

print("\n")
print("Función Objetivo:",model.objVal/1000000, "MM USD")


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


print("\n Filtro según tecnología y ubicación \n")
print("\n Centrales Antiguas\n")
for i in I:
    if datos.Centrales()[i]['tecnologia'] in combustibles_set:
        for b in B:
            for f in F:
                if (E_ce[i,b,f].x != 0): 
                    print ("Central: ", datos.Centrales()[i]['tecnologia'], "Ubicación: ", datos.Centrales()[i]['ubicacion'], "Filtro Nro.", datos.CombAbatidores()[f]['id'], 
                           ": ", datos.CombAbatidores()[f]['f1'], ", ", datos.CombAbatidores()[f]['f2'], ", ", datos.CombAbatidores()[f]['f3'])
            

print("\n Filtro según tecnología y ubicación \n")
print("\n Centrales Nuevas\n")
for i in J:
    if datos.CentralesNuevas()[i]['tecnologia'] in combustibles_set:
        for b in B:
            for f in F:
                if (E_cn[i,b,f].x != 0): 
                    print ("Central: ", datos.CentralesNuevas()[i]['tecnologia'], "Ubicación: ", datos.CentralesNuevas()[i]['ubicacion'], "Filtro Nro.", datos.CombAbatidores()[f]['id'], 
                           ": ", datos.CombAbatidores()[f]['f1'], ", ", datos.CombAbatidores()[f]['f2'], ", ", datos.CombAbatidores()[f]['f3'])


#resultados potencia base
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
        
        

#resultados 2030: centrales antiguas
for i in I:
    for b in B:
        
        for f in F:
            
            if (E_ce[i,b,f].x != 0): 
         
                if datos.Centrales()[i]['tecnologia'] == 'Biomasa':
                   
                   gen30_biomasa+= E_ce[i,b,f].x/1000
                   
                   #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
                   
                if datos.Centrales()[i]['tecnologia'] == 'Carbón':
                   
                   gen30_carbon+= E_ce[i,b,f].x/1000
                   
                   #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
                   
                if datos.Centrales()[i]['tecnologia'] == 'CC-GNL':
                    
                    gen30_gnl+= E_ce[i,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
                    
                    
                if datos.Centrales()[i]['tecnologia'] == 'Petróleo Diesel':
                   
                   gen30_diesel+= E_ce[i,b,f].x/1000
                   
                   #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
                        
                if datos.Centrales()[i]['tecnologia'] == 'Hidro':
                    
                    gen30_hidro+= E_ce[i,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")   
            
        
                if datos.Centrales()[i]['tecnologia'] == 'Eolica 1':
                    
                    gen30_wind+= E_ce[i,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh") 
        
        
                if datos.Centrales()[i]['tecnologia'] == 'Solar FV 1':
                    
                    gen30_solar+= E_ce[i,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
        
            
                if datos.Centrales()[i]['tecnologia'] == 'Central de falla':
                    
                    gen30_falla+= E_ce[i,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
                    
                    
                if datos.Centrales()[i]['tecnologia'] == 'Geotermia':
                    
                    gen30_geotermica+= E_ce[i,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.Centrales()[i]['tecnologia'] , ", " , datos.Centrales()[i]['ubicacion'] ,"= ",E_ce[i,b,0].x/1000, "GWh")
        
                if datos.Centrales()[i]['tecnologia'] == 'minihidro':
                    
                    gen30_minihidro+= E_ce[i,b,f].x/1000
            
            
#resultados 2030: centrales nuevas
for j in J:
    
    for f in F:
        
        if (Cap_ins[j,f].x != 0):
    
            if datos.CentralesNuevas()[j]['tecnologia'] == 'Biomasa':
                   
                    mw30_biomasa+= Cap_ins[j,f].x
                   
        
            if datos.CentralesNuevas()[j]['tecnologia'] == 'Carbón':
               
                mw30_carbon+= Cap_ins[j,f].x
        
        
            if datos.CentralesNuevas()[j]['tecnologia'] == 'CC-GNL':
                
                mw30_gnl+= Cap_ins[j,f].x
                
        
            if datos.CentralesNuevas()[j]['tecnologia'] == 'Petróleo Diesel':
               
                mw30_diesel+= Cap_ins[j,f].x
        
        
            if datos.CentralesNuevas()[j]['tecnologia'] == 'minihidro':
                mw30_minihidro+= Cap_ins[j,f].x
                
        
            if datos.CentralesNuevas()[j]['tecnologia'] == 'Hidro' or datos.CentralesNuevas()[j]['tecnologia'] == 'Hidroelectricidad convencional':
                
                mw30_hidro+= Cap_ins[j,f].x
                
        
            if datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 1' or datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 2' or datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 3':
                
                mw30_wind+= Cap_ins[j,f].x
                
        
            if datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 1' or datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 2' or datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 3':
                
                mw30_solar+= Cap_ins[j,f].x
                
        
            if datos.CentralesNuevas()[j]['tecnologia'] == 'Central de falla':
                
                mw30_falla+= Cap_ins[j,f].x
                
        
            if datos.CentralesNuevas()[j]['tecnologia'] == 'Geotermia':
                
                mw30_geotermica+= Cap_ins[j,f].x
    
    
    for b in B:
        
        for f in F:
            
            if (E_cn[j,b,f].x != 0):
         
                if datos.CentralesNuevas()[j]['tecnologia'] == 'Biomasa':
                   
                    gen30_biomasa2+= E_cn[j,b,f].x/1000
                   
                    #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
                   
                if datos.CentralesNuevas()[j]['tecnologia'] == 'Carbón':
                   
                    gen30_carbon2+= E_cn[j,b,f].x/1000
                   
                    #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
                   
                if datos.CentralesNuevas()[j]['tecnologia'] == 'CC-GNL':
                    
                    gen30_gnl2+= E_cn[j,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
                    
                    
                if datos.CentralesNuevas()[j]['tecnologia'] == 'Petróleo Diesel':
                   
                    gen30_diesel2+= E_cn[j,b,f].x/1000
                   
                    #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
                   
                
                if datos.CentralesNuevas()[j]['tecnologia'] == 'minihidro':
                    
                    gen30_minihidro2 += E_cn[j,b,f].x/1000
                
                
                if datos.CentralesNuevas()[j]['tecnologia'] == 'Hidro' or datos.CentralesNuevas()[j]['tecnologia'] == 'Hidroelectricidad convencional':
                    
                    gen30_hidro2+= E_cn[j,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")   
            
        
                if datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 1' or datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 2' or datos.CentralesNuevas()[j]['tecnologia'] == 'Eolica 3':
                    
                    gen30_wind2+= E_cn[j,b,f].x/1000
        
                    #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh") 
        
        
                if datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 1' or datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 2' or datos.CentralesNuevas()[j]['tecnologia'] == 'Solar FV 3':
                    
                    gen30_solar2+= E_cn[j,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
        
            
                if datos.CentralesNuevas()[j]['tecnologia'] == 'Central de falla':
                    
                    gen30_falla2+= E_cn[j,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
        
                if datos.CentralesNuevas()[j]['tecnologia'] == 'Geotermia':
                    
                    gen30_geotermica2+= E_cn[j,b,f].x/1000
                    
                    #print("Gen: ", "Bloque",b ,", ", datos.CentralesNuevas()[j]['tecnologia'] , ", " , datos.CentralesNuevas()[j]['ubicacion'] ,"= ",E_cn[j,b,0].x/1000, "GWh")
        
        #---


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


# totalmw30_biomasa= mw30_biomasa
# totalmw30_carbon= mw30_carbon
# totalmw30_diesel= mw30_diesel
# totalmw30_gnl=mw30_gnl
# totalmw30_hidro= mw30_hidro
# totalmw30_wind= mw30_wind
# totalmw30_solar= mw30_solar
# totalmw30_falla= mw30_falla
# totalmw30_geotermica= mw30_geotermica
# totalmw30_minihidro= mw30_minihidro

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

gen_total_30= gen30_biomasa_f + gen30_carbon_f + gen30_gnl_f + gen30_diesel_f + gen30_hidro_f + gen30_solar_f + gen30_wind_f + gen30_geotermica_f + gen30_falla_f + gen30_minihidro_f

print("\nGeneración total 2030: {}".format(gen_total_30))


#calculo emisiones descontroladas:

emisiones2030_MP = 0
emisiones2030_SOx = 0
emisiones2030_NOx = 0
emisiones2030_CO2 = 0

#centrales antiguas 2030
for i in I:
            
    for b in B:
        
        for f in F:
            
            if (E_ce[i,b,f].x != 0):
        
                if datos.Centrales()[i]['tecnologia'] in combustibles_set:
                    
                        
                    if datos.Centrales()[i]['tecnologia'] == 'Carbón':
                        emisiones2030_MP+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['Carbón']*(1-datos.CombAbatidores()[f]['eff-MP'])/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['MP']/(1000*1000000)
                        emisiones2030_SOx+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['Carbón']*(1-datos.CombAbatidores()[f]['eff-SOx'])/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['SOx']/(1000*1000000)
                        emisiones2030_NOx+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['Carbón']*(1-datos.CombAbatidores()[f]['eff-NOx'])/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['NOx']/(1000*1000000)
                        emisiones2030_CO2+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['Carbón']*(1-0)/datos.Centrales()[i]['eff'])*datos.Emisiones()[0]['CO2']/(1000*1000000)
    
                    
                    if datos.Centrales()[i]['tecnologia'] == 'Petróleo Diesel':
                        emisiones2030_MP+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['Diesel']*(1-datos.CombAbatidores()[f]['eff-MP'])/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['MP']/(1000*1000000)
                        emisiones2030_SOx+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['Diesel']*(1-datos.CombAbatidores()[f]['eff-SOx'])/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['SOx']/(1000*1000000)
                        emisiones2030_NOx+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['Diesel']*(1-datos.CombAbatidores()[f]['eff-NOx'])/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['NOx']/(1000*1000000)
                        emisiones2030_CO2+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['Diesel']*(1-0)/datos.Centrales()[i]['eff'])*datos.Emisiones()[2]['CO2']/(1000*1000000)
                    
        
                    if datos.Centrales()[i]['tecnologia'] == 'CC-GNL':
                        emisiones2030_MP+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['GNL']*(1-datos.CombAbatidores()[f]['eff-MP'])/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['MP']/(1000*1000000)
                        emisiones2030_SOx+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['GNL']*(1-datos.CombAbatidores()[f]['eff-SOx'])/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['SOx']/(1000*1000000)
                        emisiones2030_NOx+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['GNL']*(1-datos.CombAbatidores()[f]['eff-NOx'])/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['NOx']/(1000*1000000)
                        emisiones2030_CO2+= ((E_ce[i,b,f].x)*datos.PoderCalorifico()['GNL']*(1-0)/datos.Centrales()[i]['eff'])*datos.Emisiones()[4]['CO2']/(1000*1000000)
                        

#centrales nuevas 2030
for i in J:
        
    for b in B:
        
        for f in F:
            
            if (E_cn[i,b,f].x != 0):
        
                if datos.CentralesNuevas()[i]['tecnologia'] in combustibles_set:
                    
                    if datos.CentralesNuevas()[i]['tecnologia'] == 'Carbón':
                        emisiones2030_MP+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['Carbón']*(1-datos.CombAbatidores()[f]['eff-MP'])/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['MP']/(1000*1000000)
                        emisiones2030_SOx+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['Carbón']*(1-datos.CombAbatidores()[f]['eff-SOx'])/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['SOx']/(1000*1000000)
                        emisiones2030_NOx+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['Carbón']*(1-datos.CombAbatidores()[f]['eff-NOx'])/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['NOx']/(1000*1000000)
                        emisiones2030_CO2+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['Carbón']*(1-0)/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[1]['CO2']/(1000*1000000)
                        
                    
                    if datos.CentralesNuevas()[i]['tecnologia'] == 'Petróleo Diesel':
                        emisiones2030_MP+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['Diesel']*(1-datos.CombAbatidores()[f]['eff-MP'])/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['MP']/(1000*1000000)
                        emisiones2030_SOx+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['Diesel']*(1-datos.CombAbatidores()[f]['eff-SOx'])/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['SOx']/(1000*1000000)
                        emisiones2030_NOx+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['Diesel']*(1-datos.CombAbatidores()[f]['eff-NOx'])/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['NOx']/(1000*1000000)
                        emisiones2030_CO2+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['Diesel']*(1-0)/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[3]['CO2']/(1000*1000000)
                        
        
                    if datos.CentralesNuevas()[i]['tecnologia'] == 'CC-GNL':
                        emisiones2030_MP+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['GNL']*(1-datos.CombAbatidores()[f]['eff-MP'])/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['MP']/(1000*1000000)
                        emisiones2030_SOx+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['GNL']*(1-datos.CombAbatidores()[f]['eff-SOx'])/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['SOx']/(1000*1000000)
                        emisiones2030_NOx+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['GNL']*(1-datos.CombAbatidores()[f]['eff-NOx'])/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['NOx']/(1000*1000000)
                        emisiones2030_CO2+= ((E_cn[i,b,f].x)*datos.PoderCalorifico()['GNL']*(1-0)/datos.CentralesNuevas()[i]['eff'])*datos.Emisiones()[5]['CO2']/(1000*1000000)


print("\n EMISIONES DESCONTROLADAS año 2030\n")
print('MP: {} Mton'.format(emisiones2030_MP))
print('SOx: {} Mton'.format(emisiones2030_SOx))
print('NOx: {} Mton'.format(emisiones2030_NOx))
print('CO2: {} Mton'.format(emisiones2030_CO2))

# e_nox = 0

# for i in I:
#     for b in B:
#         for f in F:
#             if (E_ce[i,b,f].x != 0):
                
#                 e_nox+= (E_ce[i,b,f].x)*datos.Centrales()[i]['FEMI_NOx']*(1 - datos.CombAbatidores()[f]['eff-NOx'])/(1000000)
                
# for i in J:
#     for b in B:
#         for f in F:
#             if (E_cn[i,b,f].x != 0):
                
#                 e_nox+= (E_cn[i,b,f].x)*datos.CentralesNuevas()[i]['FEMI_NOx']*(1 - datos.CombAbatidores()[f]['eff-NOx'])/(1000000)
                

# print("e nox: ", e_nox)     

print("\n Centrales Antiguas\n")
for i in I:
    for b in B:
        for f in F:
            
            if (E_ce[i,b,f].x != 0):
                print("Central:", datos.Centrales()[i]['tecnologia'], "Ubicacion: ", datos.Centrales()[i]['ubicacion'], "Potencia MW", datos.Centrales()[i]['P_neta'])
                

print("\n Centrales Nuevas\n")
for i in J:
    for b in B:
        for f in F:
            
            if (E_cn[i,b,f].x != 0):
                print("Central:", datos.CentralesNuevas()[i]['tecnologia'], "Ubicacion: ", datos.CentralesNuevas()[i]['ubicacion'], "Potencia MW:", Cap_ins[i,f].x )
                

#CALCULO DE COSTO POR DAÑO SOCIAL:    
   
C_sociales_1=0
C_sociales_2=0
C_sociales_3=0
C_sociales_4=0    
   
for i in I:
    for b in B:
        for f in F:
            
            if (E_ce[i,b,f].x != 0):
                #Costo por Daño Social: CENTRALES ANTIGUAS
                C_sociales_1+=  E_ce[i,b,f].x*datos.Centrales()[i]['FEMI_MP']/1000*(1- datos.CombAbatidores()[f]['eff-MP'])*datos.Centrales()[i]['C_social_MP'] 
                C_sociales_2+=  E_ce[i,b,f].x*datos.Centrales()[i]['FEMI_SOx']/1000*(1- datos.CombAbatidores()[f]['eff-SOx'])*datos.Centrales()[i]['C_social_SOx'] 
                C_sociales_3+=  E_ce[i,b,f].x*datos.Centrales()[i]['FEMI_NOx']/1000*(1- datos.CombAbatidores()[f]['eff-NOx'])*datos.Centrales()[i]['C_social_NOx'] 
                C_sociales_4+=  E_ce[i,b,f].x*datos.Centrales()[i]['FEMI_CO2']/1000*datos.Centrales()[i]['C_social_CO2']
                
C_sociales_5=0
C_sociales_6=0
C_sociales_7=0
C_sociales_8=0
              
for i in J:
    for b in B:
        for f in F:
            
            if (E_cn[i,b,f].x != 0):
                #Costos por Daño Social: CENTRALES Nuevas
                C_sociales_5+=  E_cn[i,b,f].x*datos.CentralesNuevas()[i]['FEMI_MP']/1000*(1- datos.CombAbatidores()[f]['eff-MP'])*datos.CentralesNuevas()[i]['C_social_MP']
                C_sociales_6+=  E_cn[i,b,f].x*datos.CentralesNuevas()[i]['FEMI_SOx']/1000*(1- datos.CombAbatidores()[f]['eff-SOx'])*datos.CentralesNuevas()[i]['C_social_SOx'] 
                C_sociales_7+=  E_cn[i,b,f].x*datos.CentralesNuevas()[i]['FEMI_NOx']/1000*(1- datos.CombAbatidores()[f]['eff-NOx'])*datos.CentralesNuevas()[i]['C_social_NOx']                                                                #costos de inversiones totales (centrales + abatidores)
                C_sociales_8+=  E_cn[i,b,f].x*datos.CentralesNuevas()[i]['FEMI_CO2']/1000*datos.CentralesNuevas()[i]['C_social_CO2']


C_MP = C_sociales_1 + C_sociales_5
C_SOx = C_sociales_2 + C_sociales_6
C_NOx = C_sociales_3 + C_sociales_7
C_CO2 = C_sociales_4 + C_sociales_8

print("\n Costo por Daño Social\n")
print("Costo MP: {}".format(C_MP))
print("Costo SOx: {}".format(C_SOx))
print("Costo NOx: {}".format(C_NOx))
print("Costo CO2: {}".format(C_CO2))

C_daño = C_MP + C_SOx + C_NOx + C_CO2

print("\nCosto del Daño = {}\n".format(C_daño))

#Calculo del Costo Marginal
l= len(model.Pi) -1
shadow_price = -model.Pi[l]

print("Precio Sombra (CMg) = {}".format(shadow_price))
