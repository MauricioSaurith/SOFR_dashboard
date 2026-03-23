import pandas as pd
import requests
import os

def update_sofr_official_api(api_key, filename="historico_sofr.xlsx"):
    '''Actualiza el archivo histórico de SOFR utilizando la API oficial de FRED.
    Si el archivo no existe, se crea uno nuevo. Si ya existe, se actualiza con los datos más recientes.
    Parámetros:
        api_key: Clave de API para acceder a FRED.
        filename: Nombre del archivo Excel donde se almacenará el histórico.
    '''
    # Endpoint oficial de la documentación de FRED
    url = "https://api.stlouisfed.org/fred/series/observations"
    
    # Parámetros de consulta
    params = {
        'series_id': 'SOFR',
        'api_key': api_key,
        'file_type': 'json' # Data estructurada en JSON
    }
    
    print("Conectando con la API Oficial de FRED...")
    
    try:
        # Petición API
        response = requests.get(url, params=params)
        response.raise_for_status() # Verifica si hubo errores de conexión
        data = response.json()
        
        # JSON a DataFrame
        df_new = pd.DataFrame(data['observations'])
        
        # Seleccionar y renombrar columnas, convertir a tipo de dato preferencial
        df_new = df_new[['date', 'value']].rename(columns={'date': 'DATE', 'value': 'SOFR'})
        df_new['DATE'] = pd.to_datetime(df_new['DATE'])
        df_new['SOFR'] = pd.to_numeric(df_new['SOFR'], errors='coerce')
        df_new = df_new.dropna() # Si hay días sin valor, eliminados
        
        # Verificación si el archivo existe
        if os.path.exists(filename):
            print(f"Actualizando archivo existente: {filename}")
            df_old = pd.read_excel(filename)
            df_old['DATE'] = pd.to_datetime(df_old['DATE'])
            
            # Combinar y dejar solo registros únicos en caso de que existan duplicados
            df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=['DATE'], keep='last')
        else:
            print(f"Creando nuevo archivo histórico: {filename}")
            df_final = df_new

        # Orden por fecha
        df_final = df_final.sort_values(by='DATE', ascending=False)
        df_final.to_excel(filename, index=False)
        
        print(f"Último dato registrado: {df_final.iloc[0]['DATE'].date()} - Valor: {df_final.iloc[0]['SOFR']}%")

    except Exception as e:
        print(f"Error durante la ejecución: {e}")
    # Ejemplo: El archivo se encuentra abierto en caso de que se ejecute desde la terminal, y así no se lograría actualizar

if __name__ == "__main__":
    API_KEY = "d63d54ada6ed77d8f3b400c68d0e663f" 
    update_sofr_official_api(api_key=API_KEY)