# Importar módulos

# Módulo para manejar el tiempo
import time

# Módulo para la conexión a la base de datos MySQL
import mysql.connector

# Módulo para cargar variables de entorno desde un archivo .env
from dotenv import load_dotenv

# Módulo para acceder a funciones del sistema operativo
import os

import sys
sys.path.append("..")
import cielConceptToGesApi

import uuid # nuevo 

load_dotenv()


# Conexión a la base de datos MySQL
openmrsdb_name = os.getenv('openmrsbd_var')
notificacionesdb_name = os.getenv("notificacionesbd_var")

# Establecer la conexión con la base de datos MySQL utilizando los valores de las variables de entorno
openmrsdb = mysql.connector.connect(
    host=os.getenv("openmrshost_var"),  # Obtener la dirección IP del host desde una variable de entorno
    user=os.getenv("user_var"),  # Obtener el nombre de usuario desde una variable de entorno
    password=os.getenv("password_var"),  # Obtener la contraseña desde una variable de entorno
    database=openmrsdb_name   # Obtener el nombre de la base de datos de openmrs desde una variable de entorno
)

obs_id_inicio = 0
condition_id_inicio = 0

# UUID del concepto que deseas buscar
concept_uuid = os.getenv("concept_uuid_var")

# Crear un cursor para ejecutar la consulta
openmrscursor = openmrsdb.cursor()

try:
    # Consulta para obtener directamente el concept_id basado en el UUID
    openmrscursor.execute(f"SELECT concept_id FROM {openmrsdb_name}.concept WHERE uuid = '{concept_uuid}';")
    print("*** concept uuid ***")
    print(concept_uuid)

    # Obtener el resultado de la consulta
    concept_id_result = openmrscursor.fetchone()

    # Verificar si se encontró un concepto con el UUID proporcionado
    if concept_id_result:
        concept_id = concept_id_result[0]

        # Imprimir el concept_id encontrado
        print(f"Concept ID encontrado: {concept_id}")

    else:
        print(f"No se encontró un concepto con el UUID {concept_uuid}")

except Exception as err:
    print(f"Error al ejecutar la consulta para obtener el concept_id: {err}")

finally:
    # Cerrar el cursor 
    openmrscursor.close()

while True:
    # Crear un cursor para ejecutar consultas en la base de datos
    openmrscursor = openmrsdb.cursor()

    # Ejecutar una consulta SQL para obtener los valores de order_id de la tabla orders
    # Filtrar por order type id=2 y excluir los order_id que ya existen en la tabla de notificaciones con un estado 'E'
    query ="""select o.obs_id as obs_id,
       null as condition_id,
       pr_pn.person_id as id_notificador,
       concat(pr_pn.given_name, ' ', pr_pn.family_name) as nombre_notificador,
       concat(pn.given_name,' ',pn.family_name) as nombre_paciente,
       pi.identifier as rut_paciente,
       pa.address1 as direccion_paciente,
       pa.city_village as comuna_paciente,
       pat_n.value as celular_paciente,
       pat_e.value as email_paciente,
       o.value_coded as diag_cod,
       o.creator as usuario_registro
        from """+openmrsdb_name+""".obs o
        inner join """+openmrsdb_name+""".users pr_u on o.creator = pr_u.user_id
        inner join """+openmrsdb_name+""".person pr_p on pr_u.person_id = pr_p.person_id
        inner join """+openmrsdb_name+""".person_name pr_pn on pr_u.person_id = pr_pn.person_id
        inner join """+openmrsdb_name+""".person_name pn on o.person_id = pn.person_id
        inner join """+openmrsdb_name+""".patient_identifier pi on o.person_id = pi.patient_id AND pi.identifier_type = 4
        left join """+openmrsdb_name+""".person_address pa on o.person_id = pa.person_id
        left join """+openmrsdb_name+""".person_attribute pat_n on o.person_id = pat_n.person_id and pat_n.person_attribute_type_id = 14
        left join """+openmrsdb_name+""".person_attribute pat_e on o.person_id = pat_e.person_id and pat_e.person_attribute_type_id = 13
        where o.concept_id= """+str(concept_id)+"""
        and o.obs_id > """+str(obs_id_inicio)+"""
        and o.obs_id not in (select IFNULL(n.obs_id,0) from """+notificacionesdb_name+""".notificacion_ges n)
      UNION

      select null as obs_id,
       c.condition_id as condition_id,
       pr_pn.person_id as id_notificador,
       concat(pr_pn.given_name, ' ', pr_pn.family_name) as nombre_notificador,
       concat(pn.given_name,' ',pn.family_name) as nombre_paciente,
       pi.identifier as rut_paciente,
       pa.address1 as direccion_paciente,
       pa.city_village as comuna_paciente,
       pat_n.value as celular_paciente,
       pat_e.value as email_paciente,
       c.condition_coded as diag_cod,
       -- crt.code as icd10,
       c.creator as usuario_registro
       from """+openmrsdb_name+""".conditions c
       -- inner join """+openmrsdb_name+""".concept_reference_map crm on c.condition_coded = crm.concept_id
       -- inner join """+openmrsdb_name+""".concept_reference_term crt on crt.concept_reference_term_id = crm.concept_reference_term_id
       inner join """+openmrsdb_name+""".users pr_u on c.creator = pr_u.user_id
       inner join """+openmrsdb_name+""".person_name pr_pn on pr_u.person_id = pr_pn.person_id
       inner join """+openmrsdb_name+""".person_name pn on c.patient_id = pn.person_id
       inner join """+openmrsdb_name+""".patient_identifier pi on c.patient_id = pi.patient_id AND pi.identifier_type = 4
       left join """+openmrsdb_name+""".person_address pa on c.patient_id = pa.person_id
       left join """+openmrsdb_name+""".person_attribute pat_n on c.patient_id = pat_n.person_id and pat_n.person_attribute_type_id = 14
       left join """+openmrsdb_name+""".person_attribute pat_e on c.patient_id = pat_e.person_id and pat_e.person_attribute_type_id = 13
       where c.condition_id > """+str(condition_id_inicio)+"""
       and c.condition_id not in (select IFNULL(n.condition_id,0) from """+notificacionesdb_name+""".notificacion_ges n);"""
    print(query)
    openmrscursor.execute(query)
   
    #///revisar en query el estado de la tabla odp
    #///modificar query para agregar la busqueda en condition (condition.code), asegurar no repetir si son del paciente.
    #///revisar si existe el ges en condition

    # Obtener todos los resultados de la consulta
    openmrsResult = openmrscursor.fetchall()


    # Confirmar los cambios en la base de datos
    openmrsdb.commit()
    openmrscursor.close()
    # Iterar sobre cada resultado obtenido
    for (obs_id,condition_id,id_notificador,nombre_notificador,nombre_paciente,rut_paciente,direccion_paciente,comuna_paciente,celular_paciente,email_paciente,diad_cod,usuario_registro) in openmrsResult:
        try:
            
            print("existen resultados, entro al ciclo for para revisarlos por fila ")
            # Consulto por el detalle del diagnostico

            diag = cielConceptToGesApi.get_concept_details(diad_cod)          
            print("*** detalle del diagnostico ***")
            print(diag)
            # Consulto si es posible ges con el codigo de cie10
            # ges = cielConceptToGesApi.get_who_concept_details(icd10)

            # Si la respuesta arroja algun ges
            if diag['ges_concept_id']!="":

                print("es ges")
                # Consulto los detalles del ges
                # ges_name = cielConceptToGesApi.get_ges_concept_details(ges[0])
                
                openmrscursor2 = openmrsdb.cursor()
                agregar_posible_ges_query = ("INSERT INTO "+notificacionesdb_name+".notificacion_ges (obs_id, condition_id, nombre_establecimiento, direccion_establecimiento, ciudad_establecimiento, notificador_id, nombre_notificador, rut_notificador, nombre_paciente, rut_paciente, aseguradora_paciente, direccion_paciente, comuna_paciente, region_paciente, telefono_fijo_paciente, celular_paciente, email_paciente, cie10, diagnostico_ges, tipo, fechahora_notificacion, firma_notificador, firma_paciente, tipo_notificado, nombre_representante, rut_representante, telefono_fijo_representante, celular_representante, email_representante, fechahora_registro, fechahora_actualizacion, usuario_registro, usuario_actualizacion, estado)"
                         " VALUES (%s, %s, 'Centro Medico y Dental Fundación', 'Amanda Labarca 70', 'Santiago', %s, %s, null, %s, %s, null, %s, %s, null, null, %s, %s, %s, %s, null, null, null, null, null, null, null, null, null, null, current_timestamp, null, %s, null, 'P')")
                
                icd10 = diag['icd10_who_concept_id']
                ges_name = diag['display_name_ges']
                # Ejecutar la sentencia SQL
                openmrscursor2.execute(agregar_posible_ges_query,(obs_id,condition_id,id_notificador,nombre_notificador,nombre_paciente,rut_paciente,direccion_paciente,comuna_paciente,celular_paciente,email_paciente,icd10,ges_name,usuario_registro))

                
                # Confirmar los cambios en la base de datos
                openmrsdb.commit()
                openmrscursor2.close()

            else:
                print("no era ges")
            if obs_id is not None:
                obs_id_inicio = obs_id
            if condition_id is not None:
                condition_id_inicio = condition_id
            print(obs_id_inicio)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
    

    # Pausar la ejecución durante 5 segundos
    time.sleep(int(os.getenv("intervalo_seg")))
