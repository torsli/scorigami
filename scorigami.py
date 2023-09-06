from datetime import datetime, timedelta

import pandas as pd
from bokeh.layouts import row
from bokeh.plotting import figure, curdoc
from bokeh.settings import settings

from controlbox import ControlBox
from displaydata import DisplayData
from mainplot import MainPlot

pd.set_option("display.max_colwidth", 10000)
settings.resources = 'cdn'

def convert_time_values(val):
    if type(val[0]) == int or type(val[0]) == float:
        s = datetime.utcfromtimestamp(float(val[0]/1000)) if val[0] > 0 \
            else datetime(1970, 1, 1) + timedelta(seconds=val[0]/1000)
        start = 10000*s.year + 100*s.month + s.day
    else:
        s = val[0]
        # start = 10000*s.year + 100*s.month + s.day
        start = int(val[0].replace('-', ''))
    if type(val[1]) == int or type(val[1]) == float:
        s = datetime.utcfromtimestamp(float(val[1]/1000)) if val[1] > 0 \
            else datetime(1970, 1, 1) + timedelta(seconds=val[1]/1000)
        end = 10000 * s.year + 100 * s.month + s.day
    else:
        s = val[1]
        # end = 10000 * s.year + 100 * s.month + s.day
        end = int(val[1].replace('-', ''))
    return start, end


def get_display_names(team_list):
    out = list()
    for x in team_list:
        if 'show' not in x or x['show'] is True:
            out.append(x['display_name'])
    return out


class Scorigami(object):
    def __init__(self, input_csv, team_list_json):
        self.display_data = DisplayData(input_csv, team_list_json)
        self.control_box = ControlBox(get_display_names(self.display_data.team_list),
                                      self.display_data.get_time_interval())

        self.main_plot = MainPlot(self.display_data.source)
        self.set_up_callbacks()

    def set_up_callbacks(self):
        self.control_box.team.on_change('value', lambda attr, old, new: self.update())
        self.control_box.dp1.on_change('value', lambda attr, old, new: self.update())
        self.control_box.dp2.on_change('value', lambda attr, old, new: self.update())
        self.control_box.movbox.on_change('active', lambda attr, old, new: self.toggle_gridlines())
        self.control_box.gradient.on_change('active', lambda attr, old, new: self.update_colors())
        self.control_box.upperbox.on_change('active', lambda attr, old, new: self.update())

    def toggle_gridlines(self):
        self.main_plot.toggle_gridlines(0 in self.control_box.movbox.active)

    def update_colors(self):
        use_gradient = self.control_box.gradient.active
        self.display_data.update_colors(use_gradient)

    def update(self):
        new_team = self.control_box.team.value
        upper_only = not self.control_box.upperbox.active
        start, end = convert_time_values((self.control_box.dp1.value, self.control_box.dp2.value))

        self.display_data.update_team(new_team, upper_only, start, end)
        self.update_colors()

        self.main_plot.set_axis_labels(self.display_data.get_short_name(new_team), upper_only)

        self.control_box.update_ticker(self.display_data.scorigami_df)

    def get_layout(self):
        return row(self.control_box.get_layout(), self.main_plot.get_plot())


if __name__ == '__main__' or 'bokeh' in __name__ or 'bk' in __name__:
    p = Scorigami('data/scorigami.csv', 'data/teamdirectory.json')
    p.toggle_gridlines()
    p.update()
    lyt = p.get_layout()
    curdoc().add_root(lyt)
    curdoc().title = 'Scorigami App'
