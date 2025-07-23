import pandas as pd

class ComparateurFichiers:
    def __init__(self, df1, df2, keys1, keys2):
        self.df1 = df1.copy()
        self.df2 = df2.copy()
        self.keys1 = keys1
        self.keys2 = keys2
        
    def comparer(self):
        """Compare two DataFrames and return comparison results"""
        # Create concatenated keys for comparison
        self.df1['_compare_key'] = self.df1[self.keys1].astype(str).agg('|'.join, axis=1)
        self.df2['_compare_key'] = self.df2[self.keys2].astype(str).agg('|'.join, axis=1)
        
        # Merge DataFrames
        merged = pd.merge(self.df1, self.df2, on='_compare_key', how='outer', indicator=True)
        
        # Filter differences
        ecarts_fichier1 = merged[merged['_merge'] == 'left_only']
        ecarts_fichier2 = merged[merged['_merge'] == 'right_only']
        communs = merged[merged['_merge'] == 'both']
        
        # Calculate statistics
        total = len(merged)
        n1 = len(ecarts_fichier1)
        n2 = len(ecarts_fichier2)
        n_common = len(communs)
        
        pct1 = round(n1 / total * 100, 2) if total > 0 else 0
        pct2 = round(n2 / total * 100, 2) if total > 0 else 0
        pct_both = round(n_common / total * 100, 2) if total > 0 else 0
        
        return {
            'ecarts_fichier1': ecarts_fichier1,
            'ecarts_fichier2': ecarts_fichier2,
            'communs': communs,
            'total': total,
            'n1': n1,
            'n2': n2,
            'n_common': n_common,
            'total_ecarts': n1 + n2,
            'nb_df': len(self.df1),
            'nb_df2': len(self.df2),
            'pct1': pct1,
            'pct2': pct2,
            'pct_both': pct_both
        }
