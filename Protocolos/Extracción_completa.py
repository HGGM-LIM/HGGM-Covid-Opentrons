from opentrons import protocol_api
from opentrons.drivers.rpi_drivers import gpio
from opentrons.types import Point

# Metadatos:
metadata = {
    'protocolName': 'A Station - Version 3 - E4',
    'source': 'Custom Protocol',
    'apiLevel': '2.2',
    'author': 'HULP'}

# Variables iniciales:
SAMPLE_NUMBER = 48  # 48 muestras o 96 muestras
if SAMPLE_NUMBER == 48:
    columnas_recorrido = [1, 3, 5, 7, 9, 11]


# PARA LAS PRUEBAS:
# columnas_recorrido = [1, 3, 5, 7, 9]

def run(protocol: protocol_api.ProtocolContext):
    # Material laboratorio
    ## Slots
    ### 1

    ### 2
    tiprack_3 = protocol.load_labware('opentrons_96_filtertiprack_200ul', '3')
    ### 3
    tiprack_1 = protocol.load_labware('opentrons_96_filtertiprack_200ul', '9')

    ### 4
    tiprack_4 = protocol.load_labware('opentrons_96_filtertiprack_200ul', '2')

    ### 5 --> RESERVORIO
    reservoir_5 = protocol.load_labware('nest_12_reservoir_15ml', '5')

    ### 6
    tiprack_6 = protocol.load_labware('opentrons_96_filtertiprack_1000ul', '11')

    ### 7
    tuberack_7 = protocol.load_labware('opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '7')

    ### 8
    tuberack_10 = protocol.load_labware('opentrons_24_tuberack_eppendorf_2ml_safelock_snapcap', '10')

	### 9
    tempdeck = protocol.load_module('tempdeck', '6')
    wellplate_2 = tempdeck.load_labware('gm_alum_96_wellplate_100ul', 'Placa thermo 96 eluidos')

    ### 4 --> IMAN Y MUESTRAS INICIO
 
    mag_mod = protocol.load_module('magnetic module', '4')
    plate = mag_mod.load_labware('usascientific_96_wellplate_2.4ml_deep')


    ### 10 --> POOL para tirar sobrenadantes PARA 48 MUESTRAS
    pool_10 = protocol.load_labware('usascientific_96_wellplate_2.4ml_deep', '1')


    ## Pipetas
    p1000 = protocol.load_instrument('p1000_single_gen2', 'left', tip_racks=[tiprack_6])
    p300multi = protocol.load_instrument('p300_multi_gen2', 'right', tip_racks=[tiprack_4, tiprack_3, tiprack_1])


    # Protocolo
    # Luz en rojo para indicar inicio de la carga del protocolo por parte del procesador del robot y se encienden luces interiores


    ## 1
    txt = '---1 PARA 48 MUESTRAS) Con la p300 multi cogemos 40 de reservoir_5 columna 2 (bolas mágnéticas) y lo pasamos a las 6 columnas impares de plate SIN CAMBIAR LA PUNTA'
    protocol.comment(txt)

    ## Variables
    p300multi.well_bottom_clearance.aspirate = 1
    p300multi.well_bottom_clearance.dispense = 30  # el pocillo de plate mide 41.30 de profundidad y queremos dispensar alto para no tocar con la punta el isopropanol y evitar arrastar gotas hasta el reservorio de las bolas magnéticas

    ## Movimientos
    p300multi.pick_up_tip()
    for j in columnas_recorrido:
        p300multi.transfer(40, reservoir_5.columns_by_name()['2'], plate.columns_by_name()[str(j)],
                           new_tip='never')
        p300multi.blow_out(plate.wells()[(j - 1) * 8].top(z=-15))
    p300multi.drop_tip()


    ## 2
    txt = '---2 PARA 48 MUESTRAS) Con la p300 multi cogemos 250 de reservoir_5 columnas 6 y 7 (ISOPROPANOL) y lo pasamos a las 6 columnas impares de plate SIN CAMBIAR LA PUNTA'
    protocol.comment(txt)

    ## Variables
    p300multi.well_bottom_clearance.aspirate = 1
    p300multi.well_bottom_clearance.dispense = 30  # el pocillo de plate mide 41.30 de profundidad y queremos dispensar alto para no tocar con la punta el líquido dispensado y evitar arrastrar gota
    isopropanol = reservoir_5.columns_by_name()['6']

    ## Movimientos
    p300multi.pick_up_tip()
    # Cada columna del reservoir (máx de 15.000) nos sirve para llenar 3 columnas de plate (501x8=4008 ul por columna x3 columnas = 12.024)
    for i in columnas_recorrido:  # Podemos dispensar en 3 columnas del plate por cada carril del reservoir
        if SAMPLE_NUMBER == 48 and i == 7:
            isopropanol = reservoir_5.columns_by_name()['7']
        # for _ in range(3): # para llegar a 501 ul repetimos 167 ul tres veces y para poder hacer blow out en cada movimiento si fuera necesario
        for _ in range(2):  # para llegar a 250 ul repetimos 125 ul dos veces y para poder hacer blow out en cada movimiento si fuera necesario
            p300multi.transfer(125, isopropanol, plate.columns_by_name()[str(i)], new_tip='never')
            p300multi.blow_out(plate.wells()[(i - 1) * 8].top(z=-15))
    p300multi.drop_tip()

    # # Si cada columna del reservoir (máx de 15.000) es para tres columnas de plate,
    # # conlleva llenado de unos 13.000 y el volumen total es 15.000 por lo que estaría muy lleno cada carril y
    # # para evitar esto al hacerlo a mano, haremos que cada carril sea para dos columnas de la plate
    # p300multi.pick_up_tip()
    # for i in columnas_recorrido: # Podemos dispensar en 2 columnas del plate por cada carril del reservoir
    #     if (SAMPLE_NUMBER == 48 and i == 5) or (SAMPLE_NUMBER == 96 and i == 3):
    #         isopropanol = reservoir_5.columns_by_name()['3']
    #     elif (SAMPLE_NUMBER == 48 and i == 9) or (SAMPLE_NUMBER == 96 and i == 5):
    #         isopropanol = reservoir_5.columns_by_name()['4']
    #     elif SAMPLE_NUMBER == 96 and i == 7:
    #         isopropanol = reservoir_5.columns_by_name()['5']
    #     elif SAMPLE_NUMBER == 96 and i == 9:
    #         isopropanol = reservoir_5.columns_by_name()['6']
    #     elif SAMPLE_NUMBER == 96 and i == 11:
    #         isopropanol = reservoir_5.columns_by_name()['7']
    #     for _ in range(3): # para llegar a 501 ul repetimos 167 ul tres veces y para poder hacer blow out en cada movimiento si fuera necesario
    #         p300multi.transfer(167, isopropanol, plate.columns_by_name()[str(i)], new_tip='never')
    #         p300multi.blow_out(plate.wells()[(i-1)*8].top(z=-15))
    # p300multi.drop_tip()

    ## 3
    txt = '---3 PARA 48 MUESTRAS) Con la p1000 cogemos 250 de cada muestra inactivada y lo pasamos a las 6 columnas impares de plate y hacemos mix 5 veces'
    protocol.comment(txt)

    ## Variables
    p1000.well_bottom_clearance.aspirate = 1  # aspiramos del eppendorf de las muestras a baja altura para evitar que se deje volumen sin aspirar
    p1000.well_bottom_clearance.dispense = 7  # el pocillo de plate mide 41.30 de profundidad y queremos dispensar a una altura intermedia para hacer bien el mix
    p1000.flow_rate.aspirate = 1000  # subimos la velocidad de aspiración por defecto (300 ul/s) para que se mezcle bien al hacer el mix
    p1000.flow_rate.dispense = 1000  # subimos la velocidad de dispensación por defecto (300 ul/s) para que se mezcle bien al hacer el mix
    
    #### Recorrido de la recogida de muestras entre los 4 tuberacks
    recorrido_origen_muestras = []
    for columnas_inicio in range(6):
        if columnas_inicio <= 5:
            recorrido_origen = tuberack_10.columns()[columnas_inicio] + tuberack_7.columns()[columnas_inicio]
            recorrido_origen_muestras += recorrido_origen

    #### Recorrido de la dispensación en columnas impares del wellplate para los casos de 48 muestras
    recorrido_destino_muestras = []
    for columnas_destino in range(12):
        if columnas_destino % 2 == 0 and SAMPLE_NUMBER == 48:
            recorrido_destino = plate.columns()[columnas_destino]
            recorrido_destino_muestras += recorrido_destino

    ## Movimientos
    for sample in range(SAMPLE_NUMBER):
        p1000.pick_up_tip()
        p1000.transfer(250, recorrido_origen_muestras[sample], recorrido_destino_muestras[sample], new_tip='never', mix_after=(5, 350))
        for _ in range(2):  # sopesar hacer más blow outs seguidos para dispensar completamente y que no quede nada al llegar al slot 12 que pueda salpicar a la placa 9
            p1000.blow_out(recorrido_destino_muestras[sample].top(z=-15))
            p1000.touch_tip(recorrido_destino_muestras[sample], v_offset=-15)
        p1000.drop_tip()

        ## FINAL
    txt_final = '---FINAL DEL PROTOCOLO'
    protocol.comment(txt_final)

    ## Variables
    # Luz en verde para indicar final del procesamiento del protocolo por parte del robot y puede empezar el protocolo


    protocol.pause('Vaciar cubeta de puntas')


#######################################################
#######################################################



    ## Variables de inicio de protocolo
    ### Imán desactivado: Nos aseguramos que el imán está en su posición más baja al iniciar el protocolo
    mag_mod.disengage()
    ### Cambio de velocidad de dispensación de 300 ul/s por defecto a 900
    p300multi.flow_rate.dispense = 900

    # ############################################
    # # PASO EXTRA SOLO PARA LAS PRUEBAS DONDE SE COGE EL VOLUMEN EN UL QUE SE OBTIENE AL ACABAR CON EL A PARA EMPEZAR EL PROTOCOLO
    # p300multi.well_bottom_clearance.aspirate = 1
    # p300multi.well_bottom_clearance.dispense = 10
    # p300multi.pick_up_tip()
    # for h in columnas_recorrido:
    #     for _ in range(2):
    #         p300multi.transfer(100, reservoir_5.columns_by_name()['2'], plate.columns_by_name()[str(h)], new_tip='never')
    #         p300multi.blow_out(plate.wells()[(h-1)*8].top(z=-5))
    # p300multi.drop_tip()
    # ############################################


    ## 2
    txt = '---2) Pausa de 5 min previo a la activación del imán'
    protocol.comment(txt)

    ### Movimientos
    protocol.delay(minutes=5)


    ## 3
    txt = '---3) Activar imán a la misma altura de la base de la placa'
    protocol.comment(txt)

    ### Movimientos
    mag_mod.engage(height_from_base=7) # modificar este parámetro para ajustar la altura del imán a partir del fondo de la placa ubicada en él


    ## 4
    txt = '---4) Pausa de 4 min tras activar el imán para que las bolas magnéticas se desplacen lo suficiente y se peguen'
    protocol.comment(txt)

    ### Movimientos
    protocol.delay(minutes=4)


    ## 5
    txt = '---5) Con la p300 multi cogemos 500 de todas las columnas del plate y lo tiramos a pool_10'
    protocol.comment(txt)

    ### Variables
    p300multi.well_bottom_clearance.aspirate = -1 # -1???????????
    p300multi.well_bottom_clearance.dispense = 20 # el pool mide 30 mm de alto

    ### Movimientos
    for j in columnas_recorrido:
        p300multi.pick_up_tip()
        for _ in range(3): # para llegar a 501 ul repetimos 167 ul tres veces pero cogemos un poco más para que quede vacío y para poder hacer blow out dos veces en cada movimiento si fuera necesario
            p300multi.transfer(175, plate.columns_by_name()[str(j)], pool_10.columns_by_name()[str(j)], new_tip='never')
            p300multi.blow_out(pool_10.wells()[(j-1)*8].top(z=-15))
            p300multi.touch_tip(pool_10.wells()[(j-1)*8], radius=0.60, v_offset=-15)
        p300multi.drop_tip()


    ## 6
    txt = '---6 PARA 48 MUESTRAS) Con la p300 multi cogemos 500 de reservoir_5 columna 9 y 10 (ETANOL) y lo pasamos a las 6 columnas impares de plate SIN CAMBIAR LA PUNTA'
    protocol.comment(txt)

    ### Variables
    p300multi.well_bottom_clearance.aspirate = 1
    p300multi.well_bottom_clearance.dispense = 30 # el pocillo de plate mide 41.30 de profundidad y queremos dispensar alto para no tocar los reactivos del interior
    p300multi.flow_rate.dispense = 200  ### Cambio de velocidad de dispensación a 200
    etanol_primero = reservoir_5.columns_by_name()['9']

    ### Movimientos
    p300multi.pick_up_tip()
    for k in columnas_recorrido: # Podemos dispensar en 3 columnas del plate por cada carril del reservoir
        if SAMPLE_NUMBER == 48 and k == 7:
            etanol_primero = reservoir_5.columns_by_name()['10']
        for _ in range(3): # para llegar a 501 ul repetimos 167 ul tres veces y para poder hacer blow out en cada movimiento si fuera necesario
            p300multi.transfer(167, etanol_primero, plate.columns_by_name()[str(k)], new_tip='never')
            #p300multi.blow_out(plate.wells()[(k-1)*8].top(z=-5)) # lo descartamos porque hacer el blow out genera muchas burbujas en la punta
    p300multi.drop_tip()


    ## 7
    txt = '---7) Con la p300 multi cogemos 500 de las columnas de plate y lo tiramos en el pool_10: ' \
          'Para 48 muestras: dispensamos al lado de la columna donde se dispensó el primer sobrenadante con la muestra; '
    protocol.comment(txt)

    ### Variables
    p300multi.well_bottom_clearance.aspirate = -1 # -1???????????
    p300multi.well_bottom_clearance.dispense = 20 # el pool mide 30 mm de alto
    p300multi.flow_rate.dispense = 900  ### Cambio de velocidad de dispensación a 900

    ### Movimientos
    for l in columnas_recorrido:
        pool_destino_columna = pool_10.columns_by_name()[str(l+1)]
        pool_destino_posicion = pool_10.wells()[(l-1)*8+8]
        p300multi.pick_up_tip()
        for _ in range(3): # para llegar a 501 ul repetimos 167 ul tres veces, pero cogemos un poco más para que quede vacío
            p300multi.transfer(175, plate.columns_by_name()[str(l)], pool_destino_columna, new_tip='never')
            p300multi.blow_out(pool_destino_posicion.top(z=-15))
            p300multi.touch_tip(pool_destino_posicion, radius=0.80, v_offset=-15)
        p300multi.drop_tip()


    ## 8
    txt = '---8 PARA 48 MUESTRAS) Con la p300 multi cogemos 500 de reservoir_5 columna 11 y 12 (ETANOL) y lo pasamos a las 6 columnas impares de plate SIN CAMBIAR LA PUNTA'
    protocol.comment(txt)

    ### Variables
    p300multi.well_bottom_clearance.aspirate = 1
    p300multi.well_bottom_clearance.dispense = 30 # el pocillo de plate mide 41.30 de profundidad y queremos dispensar alto para no tocar los reactivos del interior
    p300multi.flow_rate.dispense = 200  ### Cambio de velocidad de dispensación a 200
    etanol_segundo = reservoir_5.columns_by_name()['11']

    ### Movimientos
    p300multi.pick_up_tip()
    for m in columnas_recorrido:# Podemos dispensar en 3 columnas del plate por cada carril del reservoir
        if SAMPLE_NUMBER == 48 and m == 7:
            etanol_segundo = reservoir_5.columns_by_name()['12']
        for _ in range(3): # para llegar a 501 ul repetimos 167 ul tres veces y para poder hacer blow out dos veces en cada movimiento si fuera necesario
            p300multi.transfer(167, etanol_segundo, plate.columns_by_name()[str(m)], new_tip='never')
            #p300multi.blow_out(plate.wells()[(m-1)*8].top(z=-5)) # lo descartamos porque hacer el blow out genera muchas burbujas en la punta
    p300multi.drop_tip()


    ## 9
    txt = '---9) Con la p300 multi cogemos 500 de las columnas de plate y lo tirarmos en el pool_10: ' \
          'Para 48 muestras: dispensamos al lado de la columna donde se dispensó el primer sobrenadante con la muestra; '
    protocol.comment(txt)

    ### Variables
    p300multi.well_bottom_clearance.aspirate = -1 # -1???????????
    p300multi.well_bottom_clearance.dispense = 20 # el pool mide 30 mm de alto
    p300multi.flow_rate.dispense = 900  ### Cambio de velocidad de dispensación a 900

    ### Movimientos
    for n in columnas_recorrido:
        pool_destino_columna = pool_10.columns_by_name()[str(n+1)]
        pool_destino_posicion = pool_10.wells()[(n-1)*8+8]
        p300multi.pick_up_tip()
        for _ in range(3): # para llegar a 501 ul repetimos 167 ul tres veces, pero cogemos un poco más para que quede vacío
            p300multi.transfer(175, plate.columns_by_name()[str(n)], pool_destino_columna, new_tip='never')
            p300multi.blow_out(pool_destino_posicion.top(z=-15))
            p300multi.touch_tip(pool_destino_posicion, radius=0.80, v_offset=-15)
        p300multi.drop_tip()


    ## 10
    txt = '---10) Pausa de 5 min para secado partículas con el imán mantenido encendido'
    protocol.comment(txt)

    ### Variables
    if SAMPLE_NUMBER == 48:
        protocol.delay(minutes=4) # no necesitamos 5 min porque al ser 6 columnas al acabar de recorrerlas han pasado 4 min y el min que falta se lo damos en el siguiente paso
    elif SAMPLE_NUMBER == 96:
        protocol.delay(seconds=1) # no hacemos pausa porque recorrer las 12 columnas en el paso previo ha hecho que pasen más de 5 minutos


    ## 11
    txt = '---11) Apagamos el imán antes de hacer las eluciones'
    protocol.comment(txt)

    ### Movimientos
    mag_mod.disengage()


    ## 12
    txt = '---12 PARA 48 MUESTRAS) Con la p300 multi cogemos 100 del reservoir_5 en la columna 4 (ELUCIÓN) y movemos a la plate SIN CAMBIAR LA PUNTA'
    protocol.comment(txt)

    ### Variables
    p300multi.well_bottom_clearance.aspirate = 1
    p300multi.well_bottom_clearance.dispense = 30 # el pocillo de plate mide 41.30 de profundidad y queremos dispensar alto para no tocar los reactivos del interior
    p300multi.flow_rate.dispense = 900  ### Cambio de velocidad de dispensación a 900
    minutos_secado = 1 # para que el total acumulado de tiempo de espera sea de 5 minutos totales de secado de partículas

    ### Movimientos
    p300multi.pick_up_tip()
    for p in columnas_recorrido:
        protocol.delay(minutes=minutos_secado)
        p300multi.transfer(100, reservoir_5.columns_by_name()['4'], plate.columns_by_name()[str(p)], new_tip='never')
        p300multi.blow_out(plate.wells()[(p-1)*8].top(z=-15))
    p300multi.drop_tip()

    ## 13
    txt = '---13) Mix con Eluciones y dispensación en placa final'
    protocol.comment(txt)
    tempdeck.set_temperature(4)
    ### Movimientos
    for o in columnas_recorrido:
        mag_mod.disengage() #  Imán apagado antes de hacer los mix con el bufer de elución'

        ## 13.1
        txt = '---13.1 PARA 48 MUESTRAS) Con la p300 multi movemos a las 6 columnas impares de plate columna por columna y hacemos mix 5 veces'
        protocol.comment(txt)

        ### Variables
        p300multi.flow_rate.dispense = 1000 # subimos la velocidad de dispensación por defecto (300 ul/s) para que se resuspenda bien al hacer el mix
        p300multi.flow_rate.aspirate = 150 # dejamos por defecto la velocidad de aspiración

        ### Movimientos
        p300multi.pick_up_tip()
        p300multi.mix(20, 80, plate.wells()[(o-1)*8].bottom(z=-1)) # ALTURA SUFICIENTE PARA HACER BIEN EL MIX
        for _ in range(2):
            p300multi.blow_out(plate.wells()[(o-1)*8].top(z=-15))
            p300multi.touch_tip(plate.wells()[(o-1)*8], v_offset=-15)
            p300multi.blow_out(plate.wells()[(o-1)*8].top(z=-15)) # para volver a colocarse en una posición centrada tras el touch
        p300multi.flow_rate.dispense = 900 # dejamos la velocidad a 900 de nuevo (300 es por defecto)


        ## 13.2
        txt = '---13.2) Pausa de 30 segundos, después Imán activado y posterior pausa de 1 minuto y 30 segundos'
        protocol.comment(txt)

        ### Movimientos
        #protocol.delay(seconds=30) # sustituimos esta pausa por hacer mas veces el MIX anterior (antes era 5 veces)
        mag_mod.engage(height_from_base=7)
        protocol.delay(minutes=1, seconds=30)


        ## 13.3
        txt = '---13.3) Con la p300 multi cogemos 80 del plate y lo llevamos al destino final (wellplate_2) con la misma punta del paso anterior'
        protocol.comment(txt)

        ### Variables
        p300multi.well_bottom_clearance.aspirate = -1 # -1?????
        p300multi.well_bottom_clearance.dispense = 5 # el pocillo de plate mide aprox 10 de profundidad
        p300multi.flow_rate.aspirate = 50 # cambiamos la velocidad de aspirado (por defecto es 150 ul/s)
        lateralidad = -2 # desplazamiento a la izquierda cuando aspiramos en columnas impares puesto que bolas están a la derecha

        ### Movimientos
        p300multi.transfer(80, plate.wells_by_name()['A' + str(o)].bottom(z=-1).move(Point(x=lateralidad, y=0, z=0)), wellplate_2.columns_by_name()[str(o)], new_tip='never')
        for _ in range(2):
            p300multi.blow_out(wellplate_2.wells()[(o-1)*8].top(z=-5))
            p300multi.touch_tip(wellplate_2.wells()[(o-1)*8], v_offset=-5)
            p300multi.blow_out(wellplate_2.wells()[(o-1)*8].top(z=-5))
        p300multi.drop_tip()


    ## 14 y final
    txt_final = '---14 Y FINAL) Apagamos Imán y termina protocolo'
    protocol.comment(txt_final)

    ## Variables
    # Luz en verde para indicar final del procesamiento del protocolo por parte del robot y puede empezar el protocolo
 

    ## Movimientos
    mag_mod.disengage()


