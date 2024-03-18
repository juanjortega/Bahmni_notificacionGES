from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

def get_concept_details(concept_id):
    base_url = "https://api.centromedicofundacion.cl"
    concept_url = f"{base_url}/orgs/CIEL/sources/CIEL/concepts/{concept_id}/$cascade/?cascadeLevels=1&method=sourceToConcepts&view=hierarchy&includeRetired=false"
    response = requests.get(concept_url)
    
    if response.status_code == 200:
        concept_data = response.json()
        display_name = concept_data['entry']['display_name']
        
        mappings = []
        icd10_who_concept_id = ""
        
        for mapping in concept_data['entry']['entries']:
            if mapping['type'] == 'Mapping':
                source = mapping['cascade_target_source_name']
                code = mapping['cascade_target_concept_code']
                
                mappings.append({'source': source, 'code': code})
                
                if source == 'ICD-10-WHO':
                    icd10_who_concept_id = code
        
        concept_details = {
            'concept_id': concept_id,
            'display_name': display_name,
            'mappings': mappings,
        }
        
        if icd10_who_concept_id:
            ges_concept_id, display_name_icd10_who = get_who_concept_details(icd10_who_concept_id)
            concept_details['display_name_icd10_who'] = display_name_icd10_who
            concept_details['ges_concept_id'] = ges_concept_id
            concept_details['display_name_ges'] = get_ges_concept_details(ges_concept_id)
        
        return concept_details
    else:
        raise Exception(f"No se encontró un concepto con ID {concept_id}")
        
def get_who_concept_details(icd10_who_concept_id):
    base_url = "https://api.centromedicofundacion.cl"
    concept_url = f"{base_url}/orgs/WHO/sources/ICD-10-WHO/concepts/{icd10_who_concept_id}/$cascade/?cascadeLevels=1&method=sourceToConcepts&view=hierarchy&includeRetired=false"
    response = requests.get(concept_url)
    
    if response.status_code == 200:
        concept_data = response.json()
        display_name = concept_data['entry']['display_name']
        
        mappings = []
        ges_concept_id = ""
        
        for mapping in concept_data['entry']['entries']:
            if mapping['type'] == 'Mapping':
                source = mapping['cascade_target_source_name']
                code = mapping['cascade_target_concept_code']
                
                mappings.append({'source': source, 'code': code})
                
                if source == 'GES':
                    ges_concept_id = code
        
        concept_details = {
            'concept_id': icd10_who_concept_id,
            'display_name': display_name,
            'mappings': mappings
        }
        
        return ges_concept_id, display_name
    else:
        raise Exception(f"No se encontró un concepto de la OMS con ID {icd10_who_concept_id}")


def get_ges_concept_details(ges_concept_id):
    base_url = "https://api.centromedicofundacion.cl"
    concept_url = f"{base_url}/orgs/MINSAL/sources/GES/concepts/{ges_concept_id}/$cascade/?cascadeLevels=1&method=sourceToConcepts&view=hierarchy&includeRetired=false"
    response = requests.get(concept_url)
    
    if response.status_code == 200:
        concept_data = response.json()
        display_name = concept_data['entry']['display_name']
        
        mappings = []
        
        for mapping in concept_data['entry']['entries']:
            if mapping['type'] == 'Mapping':
                source = mapping['cascade_target_source_name']
                code = mapping['cascade_target_concept_code']
                
                mappings.append({'source': source, 'code': code})
        
        concept_details = {
            'concept_id': ges_concept_id,
            'display_name': display_name,
            'mappings': mappings
        }
        
        return display_name
    else:
        raise Exception(f"No se encontró un concepto GES con ID {ges_concept_id}")
    

@app.route('/api/concept-to-ges', methods=['GET'])
def concept_details():
    concept_id = request.args.get('concept_id')
    
    if concept_id:
        try:
            concept_details = get_concept_details(concept_id)
            return jsonify(concept_details)
        except Exception as e:
            return jsonify({'error': str(e)})
    else:
        return jsonify({'error': 'No se proporcionó el ID del concepto.'})


if __name__ == '__main__':
    app.run()
