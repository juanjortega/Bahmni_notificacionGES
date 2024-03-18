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

# Cargar nombres de las bases de datos desde variables de entorno
openmrsdb_name = os.getenv('MYSQL_OPENMRS_DATABASE')
notificacionesdb_name = os.getenv("NOTIFICACIONES_DATABASE")

# Establecer la conexión con la base de datos de OpenMRS
openmrsdb = mysql.connector.connect(
    host=os.getenv("OPENMMRS_MYSQL_HOST"),  # Obtener la dirección IP del host de OpenMRS desde una variable de entorno
    user=os.getenv("MYSQL_OPENMRS_USER"),  # Obtener el nombre de usuario para OpenMRS desde una variable de entorno
    password=os.getenv("MYSQL_OPENMRS_PASSWORD"),  # Obtener la contraseña para OpenMRS desde una variable de entorno
    database=openmrsdb_name  # Obtener el nombre de la base de datos de OpenMRS desde una variable de entorno
)

# Establecer la conexión con la base de datos de Notificaciones
notificacionesdb = mysql.connector.connect(
    host=os.getenv("NOTIFICACIONES_HOST"),  # Obtener la dirección IP del host de Notificaciones desde una variable de entorno
    user=os.getenv("MYSQL_USER_NOTIFICACIONES"),  # Obtener el nombre de usuario para Notificaciones desde una variable de entorno
    password=os.getenv("MYSQL_PASSWORD_NOTIFICACIONES"),  # Obtener la contraseña para Notificaciones desde una variable de entorno
    database=notificacionesdb_name  # Obtener el nombre de la base de datos de Notificaciones desde una variable de entorno
)


obs_id_inicio = 0
condition_id_inicio = 0

# UUID del concepto que deseas buscar
concept_uuid = os.getenv("CONCEPT_UUID_VAR")

# Crear un cursor para ejecutar la consulta
openmrscursor = openmrsdb.cursor()

try:
    # Consulta para obtener directamente el concept_id basado en el UUID
    openmrscursor.execute(f"SELECT concept_id FROM {openmrsdb_name}.concept WHERE uuid = '{concept_uuid}';")

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
       cd.uuid as diag_cod,
       o.creator as usuario_registro
        from """+openmrsdb_name+""".obs o
        inner join """+openmrsdb_name+""".users pr_u on o.creator = pr_u.user_id
        inner join """+openmrsdb_name+""".person pr_p on pr_u.person_id = pr_p.person_id
        inner join """+openmrsdb_name+""".person_name pr_pn on pr_u.person_id = pr_pn.person_id
        inner join """+openmrsdb_name+""".person_name pn on o.person_id = pn.person_id
        inner join """+openmrsdb_name+""".patient_identifier pi on o.person_id = pi.patient_id AND pi.identifier_type = 4
        inner join """+openmrsdb_name+""".concept cd on o.value_coded = cd.concept_id
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
       cd.uuid as diag_cod,
       -- crt.code as icd10,
       c.creator as usuario_registro
       from """+openmrsdb_name+""".conditions c
       -- inner join """+openmrsdb_name+""".concept_reference_map crm on c.condition_coded = crm.concept_id
       -- inner join """+openmrsdb_name+""".concept_reference_term crt on crt.concept_reference_term_id = crm.concept_reference_term_id
       inner join """+openmrsdb_name+""".users pr_u on c.creator = pr_u.user_id
       inner join """+openmrsdb_name+""".person_name pr_pn on pr_u.person_id = pr_pn.person_id
       inner join """+openmrsdb_name+""".person_name pn on c.patient_id = pn.person_id
       inner join """+openmrsdb_name+""".patient_identifier pi on c.patient_id = pi.patient_id AND pi.identifier_type = 4
       inner join """+openmrsdb_name+""".concept cd on c.condition_coded = cd.concept_id
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
    for (obs_id,condition_id,id_notificador,nombre_notificador,nombre_paciente,rut_paciente,direccion_paciente,comuna_paciente,celular_paciente,email_paciente,diag_cod,usuario_registro) in openmrsResult:
        try:
            
            print("existen resultados, entro al ciclo for para revisarlos por fila ")
            # Consulto por el detalle del diagnostico con el uuid
            
            diag1 = cielConceptToGesApi.get_concept_details_q(diag_cod)
            print("*** detalle del diagnostico  por uuid ***")
            print(diag1)
            if diag1[0].get('id') is not None:     
                # Consulto por el detalle del diagnostico con id de ciel
                diag2 = cielConceptToGesApi.get_concept_details(diag1[0]['id'])          
                print("*** detalle del diagnostico ***")
                print(diag2)
                # Consulto si es posible ges con el codigo de cie10
                # ges = cielConceptToGesApi.get_who_concept_details(icd10)

                # Si la respuesta arroja algun ges
                if diag2.get('ges_concept_id') is not None:

                    print("es ges")
                    # Consulto los detalles del ges
                    # ges_name = cielConceptToGesApi.get_ges_concept_details(ges[0])
                
                    notificacionescursor = notificacionesdb.cursor()
                    #openmrscursor2 = openmrsdb.cursor()
                    agregar_posible_ges_query = ("INSERT INTO "+notificacionesdb_name+".notificacion_ges (obs_id, condition_id, nombre_establecimiento, direccion_establecimiento, ciudad_establecimiento, notificador_id, nombre_notificador, rut_notificador, nombre_paciente, rut_paciente, aseguradora_paciente, direccion_paciente, comuna_paciente, region_paciente, telefono_fijo_paciente, celular_paciente, email_paciente, cie10, diagnostico_ges, tipo, fechahora_notificacion, firma_notificador, firma_paciente, tipo_notificado, nombre_representante, rut_representante, telefono_fijo_representante, celular_representante, email_representante, fechahora_registro, fechahora_actualizacion, usuario_registro, usuario_actualizacion, estado)"
                         " VALUES (%s, %s, 'Centro Medico y Dental Fundación', 'Amanda Labarca 70', 'Santiago', %s, %s, null, %s, %s, null, %s, %s, null, null, %s, %s, %s, %s, null, null, null, null, null, null, null, null, null, null, current_timestamp, null, %s, null, 'P')")
                
                    icd10 = diag2['icd10_who_concept_id']
                    ges_name = diag2['display_name_ges']
                    # Ejecutar la sentencia SQL
                    #openmrscursor2.execute(agregar_posible_ges_query,(obs_id,condition_id,id_notificador,nombre_notificador,nombre_paciente,rut_paciente,direccion_paciente,comuna_paciente,celular_paciente,email_paciente,icd10,ges_name,usuario_registro))
                    notificacionescursor.execute(agregar_posible_ges_query,(obs_id,condition_id,id_notificador,nombre_notificador,nombre_paciente,rut_paciente,direccion_paciente,comuna_paciente,celular_paciente,email_paciente,icd10,ges_name,usuario_registro))

                
                    # Confirmar los cambios en la base de datos
                    #openmrsdb.commit()
                    #openmrscursor2.close()
                    notificacionesdb.commit()
                    notificacionescursor.close()

                else:
                    print("no era ges")
                if obs_id is not None:
                    obs_id_inicio = obs_id
                if condition_id is not None:
                    condition_id_inicio = condition_id
                print(obs_id_inicio)
            else:
                print("no encontro diagnostico")
               
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
    

    # Pausar la ejecución durante 5 segundos
    time.sleep(int(os.getenv("INTERVALO_SEG")))
