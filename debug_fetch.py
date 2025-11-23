import requests

def test_url(url):
    print(f"Testing {url}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.head(url, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Headers: {response.headers}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Try P04637 (p53)
    test_url("https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v4.pdb")
    test_url("https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v3.pdb")
    test_url("https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v2.pdb")
    test_url("https://alphafold.ebi.ac.uk/files/AF-P04637-F1-model_v1.pdb")
