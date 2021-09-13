import code
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import requests

from bokeh.plotting import figure, show
from bokeh.layouts import gridplot, row
from bokeh.models import HoverTool
from os.path import exists

if exists('borrowed_df.csv'):
    borrowed_df = pd.read_csv('borrowed_df.csv')
else:
    borrowed_query = 'https://api.flipsidecrypto.com/api/v2/queries/68944cd0-ec1d-41ab-91d8-a3e2f41337c2/data/latest'
    response = requests.get(borrowed_query)
    borrowed_df = pd.DataFrame(response.json())
    borrowed_df.to_csv("borrowed_df.csv", index=False)

if exists('apy_df.csv'):
    apy_df = pd.read_csv('apy_df.csv')
else:
    apy_query = 'https://api.flipsidecrypto.com/api/v2/queries/19d3906a-3c7c-43cf-bfad-762be909cb27/data/latest'
    response = requests.get(apy_query)
    apy_df = pd.DataFrame(response.json())
    apy_df.to_csv("apy_df.csv", index=False)

borrowed_df.HOUR_OF_ACTION = pd.to_datetime(
    borrowed_df.HOUR_OF_ACTION, format='%Y-%m-%dT%H:%M:%SZ')
apy_df.BLOCK_HOUR = pd.to_datetime(
    apy_df.BLOCK_HOUR, format='%Y-%m-%dT%H:%M:%SZ')

# Find loans for account
account = '0x1e62df63add1f2ab62e3ce3e8b2a968e939087d9'
loans_for_account = borrowed_df[borrowed_df.BORROWER_ADDRESS == account]

# inputs

DEFAULT_DAYS = 60

# Input tx ids from account, or track down interesting transactions elsewhere and skip the account step
# Enter a custom loan term in days if you do not want to use the default
txs = [
    {
        'tx_id': '0xec8891ecba774cf56aaa8b8d25efe037dace2979f7c6f5673e6c51ea6c121833',
        'days_to_track': DEFAULT_DAYS
    },
    {
        'tx_id': '0x8ecca17e68c2b3fbed285c8139eeaaea2c929057ee372f57153e509b6f5853c6',
        'days_to_track': 90
    },
    {
        'tx_id': '0x9aa6470418571da48a5a0a736189425a534be77fc5a39bd7832b26c3bdc7eb60',
        'days_to_track': 100
    },
    {
        'tx_id': '0x75d517d217b37528b5a769d0bb12a4379b86656ce84cee3a3ae0a5036c924056',
        'days_to_track': 5
    },
    {
        'tx_id': '0x27a3642aa0ba839fe5140ef530259a9584fc99c33d6bd91d5cad9470f78fd03f',
        'days_to_track': 30
    }, {
        'tx_id': '0x1a0dd9ad06bb187fabe5217c88ec57bc66508211ab08b239d7ada9a32fe242fb',
        'days_to_track': DEFAULT_DAYS
    },
    {
        'tx_id': '0x90fe309c45b5b50dc07a149519e31a4585395490f2198ccbdce8bcaf7d4f312d',
        'days_to_track': DEFAULT_DAYS
    },
    {
        'tx_id': '0x298a6c4e11c75764730f5f6f1fc6536183299cd8a6c8f7d3471fed8862019072',
        'days_to_track': DEFAULT_DAYS
    }
]

# generate plot
idx = 0
colors = ['blue', 'red', 'green', 'purple', 'orange']
plots = []
for tx in txs:
    loan = borrowed_df[borrowed_df.TX_ID == tx['tx_id']].to_dict('records')[0]
    data = apy_df[
        (apy_df.RESERVE_NAME == loan['SYMBOL']) &
        (apy_df.BLOCKCHAIN == loan['BLOCKCHAIN']) &
        (apy_df.BLOCK_HOUR >= loan['HOUR_OF_ACTION']) &
        (apy_df.BLOCK_HOUR < loan['HOUR_OF_ACTION'] +
         timedelta(days=tx['days_to_track']))
    ].sort_values(by='BLOCK_HOUR')

    if len(data) == 0:
        print(f"ERROR: No data for {tx}")
        continue

    balance = 1000000000
    for i, hour in data.iterrows():
        apy = hour.BORROW_RATE_VARIABLE
        hourly_rate = 1 + apy / 8766  # 8766 hours in a year
        balance = balance * hourly_rate
    pct_gain = (balance - 1000000000) / 1000000000.0
    time = len(data) / 24  # observed hourly periods, accounts for missing data
    fraction_of_year = time / 365.25

    actual_apy = f'{round(100 * pct_gain / fraction_of_year, 3)}%'
    TOOLS = "hover,save,pan,box_zoom,reset,wheel_zoom"
    p = figure(title=f'{loan["SYMBOL"]} LOAN RATES on {loan["BLOCKCHAIN"]}', x_axis_label='Hour',
               y_axis_label='Rate', x_axis_type='datetime', tools=TOOLS)
    p.line(x='BLOCK_HOUR', y='BORROW_RATE_VARIABLE',
           legend_label=f'APY: {actual_apy} - TX origin: {loan["TX_ID"][0:10]}', line_width=2, line_color=colors[idx % 5], source=data)
    hover = p.select(dict(type=HoverTool))
    hover.tooltips = [
        ("Hour", "@BLOCK_HOUR{%Y-%m-%d %H:%M}"),
        ("Rate", "@BORROW_RATE_VARIABLE{1.11111}")
    ]
    hover.formatters = {
        '@BLOCK_HOUR': 'datetime'
    }
    plots.append(p)
    idx = idx + 1

grid = []
for j in range(0, len(plots)):
    grid.append([plots[j]])


show(gridplot(grid))
