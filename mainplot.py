import numpy as np
from bokeh.models import ColumnDataSource, Range1d, HoverTool, FuncTickFormatter
from bokeh.models.glyphs import MultiLine
from bokeh.plotting import figure

def get_tooltip():
    return """
    <div>
        <div>
            <span style="font-size: 20px; font-weight: bold;">@score</span>
        </div>
        <div>
            <span style="font-size: 15px; color: #008;">@first</span>
        </div>
        <div>
            <span style="font-size: 15px; color: #080;">@last</span>
        </div>
        <div>
            <span style="font-size: 15px;"><span style="font-weight: bold;">@txt</span></span>
        </div>
    </div>
    """


class MainPlot(object):
    def __init__(self, source):
        plot = figure(width=900, height=900,
                      x_minor_ticks='auto', y_minor_ticks='auto',
                      x_axis_location='above',
                      tools='save')
        plot.y_range = Range1d(-73.5, 0.5)
        plot.x_range = Range1d(-0.5, 73.5)
        plot.xaxis.axis_label = 'Winning Score'
        plot.yaxis.axis_label = 'Losing Score'
        plot.xaxis.axis_label_text_font_size = '18pt'
        plot.yaxis.axis_label_text_font_size = '18pt'
        plot.xaxis.axis_label_text_font_style = 'bold'
        plot.yaxis.axis_label_text_font_style = 'bold'

        plot.yaxis.formatter = FuncTickFormatter(code='return -tick')

        plot.background_fill_color = '#cccccc'
        plot.grid.grid_line_color = None
        plot.xaxis.ticker = list(range(0, 74, 7))
        plot.yaxis.ticker = list(range(0, -74, -7))
        plot.axis.major_tick_in = 1
        plot.axis.major_tick_out = -1
        plot.axis.major_label_text_font_size = '8pt'
        plot.outline_line_width = 1
        plot.outline_line_color = 'black'
        self.plot = plot

        self.gridlines = self.set_up_gridlines()
        self.set_up_quad(source)

    def set_up_gridlines(self):
        xpts = [-1, 74]
        ypts = [1, -74]
        xs = [xpts for _ in np.arange(-70, 71, 7)]
        ys = [ypts + yy for yy in np.arange(-70, 71, 7)]
        mov_lines = ColumnDataSource(dict(x=xs, y=ys))
        glyph = MultiLine(xs='x', ys='y', line_color='#7f7f7f', line_width=3, line_dash='dotted')
        mov_line = self.plot.add_glyph(mov_lines, glyph)
        zero_line = self.plot.line([-1, 74], [1, -74], line_color='#7f7f7f', line_width=5)
        return [mov_line, zero_line]

    def set_up_quad(self, source):
        self.plot.quad(top='U', bottom='D', left='L', right='R', source=source,
                       fill_color='color', line_color=None)
        self.plot.add_tools(HoverTool(tooltips=get_tooltip()))

    def toggle_gridlines(self, show_lines):
        if show_lines:
            for r in self.gridlines:
                r.glyph.line_alpha = 1
        else:
            for r in self.gridlines:
                r.glyph.line_alpha = 0

    def set_axis_labels(self, short_name, upper_only):
        if upper_only:
            self.plot.xaxis.axis_label = 'Winning Score'
            self.plot.yaxis.axis_label = 'Losing Score'
        elif short_name == 'All':
            self.plot.xaxis.axis_label = 'Home Score'
            self.plot.yaxis.axis_label = 'Away Score'
        else:
            self.plot.xaxis.axis_label = short_name + ' Score'
            self.plot.yaxis.axis_label = 'Opponent Score'

    def get_plot(self):
        return self.plot
