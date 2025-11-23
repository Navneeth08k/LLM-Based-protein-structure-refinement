import os
import requests

class AlphaFoldFetcher:
    """
    Fetches PDB and confidence JSON files from the AlphaFold Protein Structure Database.
    """
    BASE_URL = "https://alphafold.ebi.ac.uk/files"

    def __init__(self, download_dir="data"):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

    def fetch(self, uniprot_id):
        """
        Downloads the PDB and JSON for a given Uniprot ID.
        Tries versions v6 down to v1.
        Also tries appending '-1' for isoform 1 if base ID fails.
        
        Args:
            uniprot_id (str): The Uniprot accession ID (e.g., Q92947).
            
        Returns:
            tuple: (pdb_path, json_path)
        """
        versions = ["v6", "v5", "v4", "v3", "v2", "v1"]
        
        # List of ID formats to try: [ID, ID-1]
        # Some entries require explicit isoform 1 suffix, others don't.
        # Also, sometimes the user might provide 'P04637-4', so we should just try what they gave first.
        ids_to_try = [uniprot_id]
        if "-" not in uniprot_id:
            ids_to_try.append(f"{uniprot_id}-1")
            
        for uid in ids_to_try:
            for version in versions:
                # Filename format: AF-<ID>-F1-model_<version>.pdb
                pdb_filename = f"AF-{uid}-F1-model_{version}.pdb"
                json_filename = f"AF-{uid}-F1-confidence_{version}.json"
                
                pdb_url = f"{self.BASE_URL}/{pdb_filename}"
                json_url = f"{self.BASE_URL}/{json_filename}"
                
                pdb_path = os.path.join(self.download_dir, pdb_filename)
                json_path = os.path.join(self.download_dir, json_filename)
                
                try:
                    print(f"Trying {uid} {version}...")
                    self._download(pdb_url, pdb_path)
                    self._download(json_url, json_path)
                    print(f"Successfully fetched {uid} {version}")
                    return pdb_path, json_path
                except ValueError:
                    continue
                
        raise ValueError(f"Could not download data for {uniprot_id} (tried v6-v1 and isoforms)")

    def _download(self, url, path):
        if os.path.exists(path):
            print(f"File already exists: {path}")
            return

        print(f"Downloading {url}...")
        # Add User-Agent to avoid being blocked
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(path, 'wb') as f:
                f.write(response.content)
            print(f"Saved to {path}")
        else:
            raise ValueError(f"Failed to download {url}. Status code: {response.status_code}")

class RCSBFetcher:
    """
    Fetches experimental structures from RCSB PDB.
    """
    def __init__(self, download_dir="data"):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        
    def fetch(self, pdb_id):
        """
        Downloads PDB file from RCSB.
        """
        pdb_id = pdb_id.lower()
        url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
        output_path = os.path.join(self.download_dir, f"{pdb_id}.pdb")
        
        if os.path.exists(output_path):
            print(f"File {output_path} already exists. Skipping download.")
            return output_path
            
        print(f"Downloading PDB {pdb_id} from {url}...")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                print(f"Downloaded {output_path}")
                return output_path
            else:
                print(f"Failed to download {pdb_id}: HTTP {response.status_code}")
                return None
        except Exception as e:
            print(f"Error downloading {pdb_id}: {e}")
            return None
