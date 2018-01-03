from datetime import datetime as dt, timedelta

from bokeh.layouts import widgetbox
from bokeh.models import Select, DatePicker, CheckboxGroup, Div


class ControlBox(object):
    def __init__(self, team_list, interval):
        self.team = Select(title='Choose a Team', options=team_list, value='All')
        st = dt.strptime(str(interval[0]), '%Y%m%d')
        en = dt.strptime(str(interval[1]), '%Y%m%d') + timedelta(1)
        self.dp1 = DatePicker(title='Start Date:', min_date=st, max_date=en, value=st)
        self.dp2 = DatePicker(title='End Date:', min_date=st, max_date=en, value=en)

        self.gradient = CheckboxGroup(labels=['Show gradient'], active=[])
        self.movbox = CheckboxGroup(labels=['Show margin of victory grid'], active=[])
        self.upperbox = CheckboxGroup(labels=['Split wins and losses'], active=[])
        self.ticker = Div(text='')

    def get_layout(self):
        return widgetbox(self.team,
                         self.dp1,
                         self.dp2,
                         self.gradient,
                         self.movbox,
                         self.upperbox,
                         self.ticker,
                         width=300)

    def update_ticker(self, df):
        if df.empty:
            self.ticker.text = ''
        else:
            header = '<div style="color:blue;font-weight:bold;font-size:18pt;margin-bottom:12pt">Scorigamis</div>'
            self.ticker.text = header + df.to_string(index=False, header=False, line_width=50,
                                                     max_rows=12, justify='left')
