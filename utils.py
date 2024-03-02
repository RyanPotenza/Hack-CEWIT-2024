import googlemaps

def getAPIKey(file_path: str):
    try:
        with open(file_path, 'r') as file:
            api_key = file.read().strip()
        return api_key
    except FileNotFoundError:
        print(f"Error: API key file '{file_path}' not found.")
        return None
    
def get_client():
    return googlemaps.Client(key=getAPIKey('APIKey.txt'))