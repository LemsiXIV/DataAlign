import pickle
import os

# Check the most recent pickle file
pickle_path = r"C:\Users\mlemsi\AppData\Local\Temp\tmpujox76u3.pkl"

try:
    with open(pickle_path, 'rb') as f:
        data = pickle.load(f)
    
    print("=== Pickle File Analysis ===")
    print(f"Keys: {list(data.keys())}")
    
    for key in ['ecarts_fichier1', 'ecarts_fichier2', 'communs']:
        if key in data:
            df = data[key]
            print(f"\n{key}: {len(df)} rows")
            if len(df) == 1004:
                print(f"  *** FOUND 1004! ***")
                print(f"  Columns: {list(df.columns)}")
            
except Exception as e:
    print(f"Error: {e}")
