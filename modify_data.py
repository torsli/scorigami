import pandas as pd
import json

new_data = pd.read_csv('data/2023-data.csv')

with open('data/teamdirectory.json', 'r') as json_file:
    team_info = json.load(json_file)

bar = dict()
for team in team_info['teams']:
    if team['code'] == 'NONE':
        break
    bar[team['full_name']] = team['code']

bar['Los Angeles Chargers'] = 'LAC'
bar['Las Vegas Raiders'] = 'LVR'
bar['Washington Football Team'] = 'WAS'
bar['Washington Redskins'] = 'WAS'


for index, row in new_data.iterrows():
    # Rk,Tm,Year,Date,Time,LTime,Neut,Opp,Week,G#,Day,Result,OT,PF,PA,PD,PC

    home_team_wins = (row['Neut'] != '@')
    if row['PF'] == row['PA']:
        res = 'T'
    else:
        res = 'W'

    foo = [''] * 17
    foo[0] = str(index)
    foo[1] = bar[row['Winner/tie']] if home_team_wins else bar[row['Loser/tie']]
    foo[2] = row['Date'][:4]
    foo[3] = row['Date']
    foo[4] = row['Time'][:-2]
    foo[6] = 'N' if row['Neut'] == 'N' else ''
    foo[7] = bar[row['Loser/tie']] if home_team_wins else bar[row['Winner/tie']]
    # if 'Wild' in row['Week']:
    #     foo[8] = 19
    # elif 'Divis' in row['Week']:
    #     foo[8] = 20
    # elif 'ConfC' in row['Week']:
    #     foo[8] = 21
    # elif 'Super' in row['Week']:
    #     foo[8] = 22
    # else:
    foo[8] = row['Week']
    foo[10] = row['Day']
    foo[11] = f"{res} {max(row['PF'], row['PA'])}-{min(row['PF'], row['PA'])}"
    foo[13] = row['PF'] if home_team_wins else row['PA']
    foo[14] = row['PA'] if home_team_wins else row['PF']
    foo[15] = abs(row['PF'] - row['PA'])
    foo[16] = row['PF'] + row['PA']
    print(','.join([str(x) for x in foo]))
