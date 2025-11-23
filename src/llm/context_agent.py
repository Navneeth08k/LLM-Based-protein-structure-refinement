from .client import LLMClient

import requests

class ContextAgent:
    """
    Agent to retrieve biological context for a given protein (UniProt ID) using an LLM.
    """
    def __init__(self, client: LLMClient):
        self.client = client

    def fetch_protein_name(self, uniprot_id):
        """
        Fetches the protein name from UniProt API.
        """
        url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Try to get recommended name
                try:
                    name = data['proteinDescription']['recommendedName']['fullName']['value']
                    return name
                except KeyError:
                    # Fallback to submitted name or gene name
                    try:
                        name = data['proteinDescription']['submissionNames'][0]['fullName']['value']
                        return name
                    except (KeyError, IndexError):
                         return uniprot_id # Fallback
            else:
                print(f"UniProt API failed: {response.status_code}")
                return uniprot_id
        except Exception as e:
            print(f"Error fetching from UniProt: {e}")
            return uniprot_id

    def get_context(self, uniprot_id):
        """
        Queries the LLM to get the folding-upon-binding context for a UniProt ID.
        """
        protein_name = self.fetch_protein_name(uniprot_id)
        print(f"Identified protein: {protein_name} ({uniprot_id})")

        prompt = f"""
You are an expert structural biologist preparing input for an AlphaFold refinement pipeline. 
I will give you a protein name and its UniProt ID. 
Your goal is to provide a **highly specific structural description** of its folding-upon-binding behavior.

**Instructions:**
1. Identify the specific domain or region that is disordered in isolation but folds upon binding.
2. Describe the **exact secondary structure** it adopts (e.g., "forms an amphipathic alpha-helix", "folds into a three-helix bundle", "forms a beta-hairpin").
3. Mention the binding partner and the specific interface if known.
4. **Crucial:** Be as precise as possible about the shape. General statements like "it becomes ordered" are not helpful. We need "it becomes a helix".

Protein: {protein_name}
UniProt ID: {uniprot_id}

Output JSON format:
{{
    "protein_name": "Name of the protein",
    "binding_partner": "Name of the binding partner",
    "folding_mechanism": "Detailed description of the folding event",
    "context_summary": "A single, structurally rich sentence. Example: 'The C-terminal TAD folds into three alpha-helices (H1, H2, H3) that wrap around the TAZ1 domain of CBP.'"
}}
"""
        print(f"Querying LLM for detailed structural context of {protein_name}...")
        response = self.client.query(prompt)
        
        if isinstance(response, list):
            if len(response) > 0:
                response = response[0]
            else:
                response = {}

        if response and "context_summary" in response:
            print(f"Context retrieved: {response['context_summary']}")
            return response["context_summary"]
        else:
            print("Failed to retrieve context from LLM.")
            return None
