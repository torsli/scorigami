import json
from copy import deepcopy
from datetime import datetime

import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.palettes import magma


class DisplayData(object):
    def __init__(self, input_csv, team_list_json):
        self.built = False
        pfr = pd.read_csv(input_csv)
        pfr = add_scorigami_column(pfr)

        self.team_list = None
        self.nonleague_dict = None
        self.process_team_list(team_list_json)

        self.in_data = {'Home': pfr['Tm'],
                        'Away': pfr['Opp'],
                        'Home Score': pfr['PF'],
                        'Away Score': pfr['PA'],
                        'Date': [int(x.replace('-', '')) for x in pfr['Date']],
                        'Scorigami': pfr['scorigami_df'],
                        'Neutral': ['N' in str(x) for x in pfr['Neut']]
                        }
        self.start_date = min(self.in_data['Date'])
        self.end_date = max(self.in_data['Date'])
        self.df = pd.DataFrame(self.in_data)
        self.display_df = None
        self.generate_display_df('All', False)
        self.source = ColumnDataSource(self.display_df)
        self.scorigami_df = None
        self.generate_scorigami_df()
        self.built = True

    def get_time_interval(self):
        return self.start_date, self.end_date

    def process_team_list(self, team_list_json):
        with open(team_list_json, 'r') as json_file:
            team_info = json.load(json_file)
        self.nonleague_dict = team_info['nonleague']

        x = dict()
        x['full_name'] = 'All'
        x['display_name'] = 'All'
        x['code'] = ['']
        x['short_name'] = 'All'
        self.team_list = [x]
        for x in team_info['teams']:
            x['code'] = [x['code']]
            x['display_name'] = x['full_name']
            if 'disambiguation' in x:
                x['display_name'] += x['disambiguation']
            self.team_list.append(x)
            if x['aliases']:
                ix = self.team_list.index(x)
                y = deepcopy(x)
                y['display_name'] = '--- as ' + y['full_name']
                if 'disambiguation' in y:
                    y['display_name'] += y['disambiguation']
                self.team_list.append(y)
                for y in x['aliases']:
                    y['display_name'] = '--- as ' + y['full_name']
                    if 'disambiguation' in y:
                        y['display_name'] += y['disambiguation']
                    self.team_list[ix]['code'].append(y['code'])
                    y['code'] = [y['code']]
                    self.team_list.append(y)

    def update_team(self, team, upper_only, start, end):
        if team == 'All':
            self.df = pd.DataFrame(self.in_data)
            if not upper_only:
                self.df = self.df[self.df['Neutral'] == False]
            ix = 0
        else:
            df = pd.DataFrame(self.in_data)
            display_list = [x['display_name'] for x in self.team_list]
            ix = display_list.index(team)
            code_list = [x['code'] for x in self.team_list][ix]
            df1 = df[df['Away'].isin(code_list)].rename(columns={'Away': 'Team', 'Away Score': 'Team Score',
                                                                 'Home': 'Opp', 'Home Score': 'Opp Score'})
            df2 = df[df['Home'].isin(code_list)].rename(columns={'Home': 'Team', 'Home Score': 'Team Score',
                                                                 'Away': 'Opp', 'Away Score': 'Opp Score'})
            self.df = pd.concat([df1, df2], sort=True)

        self.df = self.df[self.df['Date'] <= end]
        self.df = self.df[self.df['Date'] >= start]

        self.df = self.df.sort_values('Date')
        self.generate_scorigami_df()
        self.generate_display_df([x['short_name'] for x in self.team_list][ix], upper_only)

    def get_scorigami_html(self, row):
        codes = [x['code'] for x in self.team_list]
        names = [x['full_name'] for x in self.team_list]

        home_code = row['Home'] if 'Home' in row else row['Team']
        away_code = row['Away'] if 'Away' in row else row['Opp']
        home_score = row['Home Score'] if 'Home Score' in row else row['Team Score']
        away_score = row['Away Score'] if 'Away Score' in row else row['Opp Score']

        home = self.nonleague_dict[home_code] if [home_code] not in codes else names[codes.index([home_code])]
        away = self.nonleague_dict[away_code] if [away_code] not in codes else names[codes.index([away_code])]
        dt = datetime.strptime(str(row['Date']), '%Y%m%d')
        st = '<div style="color:red;font-weight:bold">{dt:%B} {dt.day}, {dt.year}: </div>'.format(dt=dt)
        if away_score < home_score:
            st += '<div style="text-indent:12pt">{team} {score},</div>'.format(team=home, score=home_score)
            st += '<div style="text-indent:12pt">{team} {score}</div>'.format(team=away, score=away_score)
        else:
            st += '<div style="text-indent:12pt">{team} {score},</div>'.format(team=away, score=away_score)
            st += '<div style="text-indent:12pt">{team} {score}</div>'.format(team=home, score=home_score)
        return st

    def generate_scorigami_df(self):
        scori_table = self.df.loc[self.df['Scorigami'] == True]
        self.scorigami_df = pd.DataFrame(scori_table.apply(self.get_scorigami_html, axis=1))

    def update_colors(self, use_gradient):
        if use_gradient:
            mx = np.max(self.display_df['total'])
            if mx > 1:
                mx = np.ceil(10 * np.log2(mx)) / 10
                if not np.isnan(mx):
                    self.display_df['color'] = [magma(256)[int(np.log2(tot) * 255 / mx)]
                                                for tot in self.display_df['total']]
        else:
            self.display_df['color'] = magma(4)[0]
        if self.built:
            self.source.data = self.display_df.to_dict(orient='list')

    def aggregate(self):
        agg = self.df.groupby(['F', 'A']).agg(['count', 'max', 'min'])
        self.display_df = pd.DataFrame({'F': agg['fer']['max'],
                                        'A': agg['agin']['min'],
                                        'total': agg['fer']['count']})

        date_strings = [generate_tooltip_data(x) for x in zip(agg['Date']['min'], agg['Date']['max'])]
        self.display_df['first'] = [x[0] for x in date_strings]
        self.display_df['last'] = [x[1] for x in date_strings]
        self.display_df['color'] = magma(4)[0]

    def add_box_columns(self):
        self.display_df['L'] = self.display_df['F'] - 0.5
        self.display_df['R'] = self.display_df['F'] + 0.5
        self.display_df['U'] = -self.display_df['A'] + 0.5
        self.display_df['D'] = -self.display_df['A'] - 0.5

    def generate_df_for_all(self, upper_only):
        if upper_only:
            self.df['F'] = self.df[['Away Score', 'Home Score']].max(axis=1)
            self.df['A'] = self.df[['Away Score', 'Home Score']].min(axis=1)
        else:
            self.df['F'] = self.df['Home Score']
            self.df['A'] = self.df['Away Score']
        self.df['fer'] = self.df['F']
        self.df['agin'] = self.df['A']
        self.aggregate()
        self.display_df.loc[self.display_df['total'] == 1, 'txt'] = 'This final score occurred once.'
        self.display_df.loc[self.display_df['total'] == 2, 'txt'] = 'This final score occurred twice.'
        self.display_df.loc[self.display_df['total'] > 2, 'txt'] = 'This final score occurred ' \
                                                                   + self.display_df.loc[self.display_df['total'] > 2,
                                                                                         'total'].astype(str) \
                                                                   + ' times.'
        self.display_df['score'] = self.display_df['F'].astype(int).astype(str) + '-' \
            + self.display_df['A'].astype(int).astype(str)
        self.add_box_columns()

    def generate_df_for_team(self, team, upper_only):
        if upper_only:
            self.df['F'] = self.df[['Team Score', 'Opp Score']].max(axis=1)
            self.df['A'] = self.df[['Team Score', 'Opp Score']].min(axis=1)
        else:
            self.df['F'] = self.df['Team Score']
            self.df['A'] = self.df['Opp Score']

        self.df['fer'] = self.df['F']
        self.df['agin'] = self.df['A']
        self.aggregate()
        self.display_df.loc[self.display_df['total'] == 1, 'txt'] = 'The ' + team + \
                                                                    ' played one game with this final score.'
        self.display_df.loc[self.display_df['total'] == 2, 'txt'] = 'The ' + team + \
                                                                    ' played two games with this final score.'
        self.display_df.loc[self.display_df['total'] > 2, 'txt'] = 'The ' + team + ' played ' \
                                                                   + self.display_df.loc[self.display_df['total'] > 2,
                                                                                         'total'].astype(str) \
                                                                   + ' games with this final score.'
        self.display_df['score'] = self.display_df['F'].astype(int).astype(str) + '-' \
            + self.display_df['A'].astype(int).astype(str)
        self.display_df['score'] = self.display_df[['F', 'A']].max(axis=1).astype(int).astype(str) + '-' \
            + self.display_df[['F', 'A']].min(axis=1).astype(int).astype(str)

        if not upper_only:
            self.display_df.loc[self.display_df['F'] > self.display_df['A'], 'score'] += ' W'
            self.display_df.loc[self.display_df['F'] < self.display_df['A'], 'score'] += ' L'
            self.display_df.loc[self.display_df['F'] == self.display_df['A'], 'score'] += ' T'

        self.add_box_columns()

    def generate_display_df(self, team, upper_only):
        if self.df.empty:
            self.display_df = pd.DataFrame({'F': [-100], 'A': [-100], 'first': [''], 'last': [''], 'total': [0],
                                            'color': '#000003'})
            self.add_box_columns()
            self.update_colors(False)
        elif team == 'All':
            self.generate_df_for_all(upper_only)
        else:
            self.generate_df_for_team(team, upper_only)

    def get_short_name(self, display_name):
        ix = [x['display_name'] for x in self.team_list].index(display_name)
        return [x['short_name'] for x in self.team_list][ix]


def generate_tooltip_data(date_int):
    dmin = str(date_int[0])
    dmax = str(date_int[1])
    if dmin == dmax:
        dt = datetime.strptime(dmin, '%Y%m%d')
        str1 = 'First & last: ' + '{dt:%B} {dt.day}, {dt.year}'.format(dt=dt)
        str2 = ''
    else:
        dt1 = datetime.strptime(dmin, '%Y%m%d')
        dt2 = datetime.strptime(dmax, '%Y%m%d')
        str1 = 'First: ' + '{dt:%B} {dt.day}, {dt.year}'.format(dt=dt1)
        str2 = 'Last: ' + '{dt:%B} {dt.day}, {dt.year}'.format(dt=dt2)
    return str1, str2


def add_scorigami_column(in_df):
    df = in_df.sort_values('Date')
    df['scorigami_df'] = False
    df = df.reset_index()
    unique_scores = dict()
    for index, row in df.iterrows():
        key = (max(row['PF'], row['PA']), min(row['PF'], row['PA']))
        if key not in unique_scores:
            df.at[index, 'scorigami_df'] = True
            unique_scores[key] = 'seen'
    return df
