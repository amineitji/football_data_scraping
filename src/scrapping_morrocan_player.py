# libraries
import pandas as pd

# fbref table link
url_df = 'https://fbref.com/en/stathead/scout/m/MAR'

df = pd.read_html(url_df)
print(df)