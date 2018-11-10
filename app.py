import random

import pandas as pd
import numpy as np

from bokeh.layouts import column
from bokeh.models import Button
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc

from bokeh.models import LogColorMapper
from bokeh.palettes import Viridis6 as palette

from bokeh.layouts import widgetbox
from bokeh.models.widgets import Dropdown


def make_state_data(df, counties, year, col):
    county_name_to_id = {county['name']: county_id for county_id, county in counties.items()}

    county_xs = [county["lons"] for county in counties.values()]
    county_ys = [county["lats"] for county in counties.values()]

    county_names = [county['name'] for county in counties.values()]
    # data = df[df['year'] == year][['county_id', 'col']]
    data_dict = {}
    df = df[df['year'] == int(year)]
    for county, data in zip(df['county'], df[col]):
        county_id = county_name_to_id[county]
        assert county_id not in data_dict, f'duplicate county data for county {county_id} in {year}'
        data_dict[county_id] = data

    # return ColumnDataSource(data={
    return ({
        'x':county_xs,
        'y':county_ys,
        'name':county_names,
        # col:[data_dict[county_id] for county_id in counties],
        'value':[data_dict[county_id] for county_id in counties],
    })

def plot_state_data(dataname, data):
    palette.reverse()

    color_mapper = LogColorMapper(palette=palette)


    TOOLS = "pan,wheel_zoom,reset,hover,save"

    p = figure(
        tools=TOOLS,
        x_axis_location=None, y_axis_location=None,
        match_aspect=True,
        tooltips=[
            ("Name", "@name"), ('value', "@value"), ("(Long, Lat)", "($x, $y)")
    ])
    p.grid.grid_line_color = None
    p.hover.point_policy = "follow_mouse"

    patches = p.patches('x', 'y', source=data,
              fill_color={'field': 'value', 'transform': color_mapper},
              fill_alpha=0.7, line_color="white", line_width=0.5)
    return p, patches

# create a plot and style its properties
p = figure(x_range=(0, 100), y_range=(0, 100), toolbar_location=None)
p.border_fill_color = 'black'
p.background_fill_color = 'black'
p.outline_line_color = None
p.grid.grid_line_color = None

# add a text renderer to our plot (no data yet)
r = p.text(x=[], y=[], text=[], text_color=[], text_font_size="20pt",
           text_baseline="middle", text_align="center")

i = 0

ds = r.data_source

# create a callback that will add a number in a random location
def callback():
    global i

    # BEST PRACTICE --- update .data in one step with a new dict
    new_data = dict()
    new_data['x'] = ds.data['x'] + [random()*70 + 15]
    new_data['y'] = ds.data['y'] + [random()*70 + 15]
    new_data['text_color'] = ds.data['text_color'] + [RdYlBu3[i%3]]
    new_data['text'] = ds.data['text'] + [str(i)]
    ds.data = new_data

    i = i + 1

from bokeh.sampledata.us_counties import data as counties

counties = {
    code: county for code, county in counties.items() if county["state"] == 'co'
}
def gen_fake_rows():
    for year in range(1990, 2031):
        for county in counties.values():
            yield {
                'year': year,
                'total_population': int(random.random() * 100000),
                'energy_use': random.random() * 100000,
                'energy_cost': random.random(),
                'solar_installed': random.random() * 100000,
                'county': county['name']
            }
df = pd.DataFrame.from_dict(list(gen_fake_rows()))

YEAR_TO_PLOT='2000'
COL_TO_PLOT='total_population'
CO_data = make_state_data(df, counties, YEAR_TO_PLOT, COL_TO_PLOT)
(CO_plot_fig, CO_plot_patches) = plot_state_data(COL_TO_PLOT, CO_data)
CO_ds = CO_plot_patches.data_source

def update_data():
    print('updating data', YEAR_TO_PLOT, COL_TO_PLOT)
    new_data = make_state_data(df, counties, YEAR_TO_PLOT, COL_TO_PLOT)
    # CO_data[COL_TO_PLOT] = new_data[COL_TO_PLOT]
    CO_ds.data = new_data


# construct year dropdown
def update_year_to_plot(atr, old, new):
    global YEAR_TO_PLOT
    YEAR_TO_PLOT = new
    update_data()

year_menu = sorted(set(((str(y), str(y)) for y in df['year'])))
year_dropdown = Dropdown(label="Year", button_type="warning", menu=year_menu, value=YEAR_TO_PLOT)
year_dropdown.on_change('value', update_year_to_plot)

# construct column dropdown
def update_col_to_plot(atr, old, new):
    global COL_TO_PLOT
    COL_TO_PLOT = new
    update_data()
col_data_menu = [(str(c), str(c)) for c in df.columns if c not in ['year','county']]
col_dropdown = Dropdown(label="Data", button_type="warning", menu=col_data_menu, value=COL_TO_PLOT)
col_dropdown.on_change('value', update_col_to_plot)

curdoc().add_root(column(year_dropdown, col_dropdown, CO_plot_fig))
