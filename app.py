import random

import pandas as pd
import numpy as np

from bokeh.layouts import column
from bokeh.models import Button
from bokeh.palettes import RdYlBu3
from bokeh.plotting import figure, curdoc

from bokeh.models import LogColorMapper, LogTicker, ColorBar
from bokeh.palettes import Magma256 as palette
from bokeh.palettes import Spectral4
from bokeh.layouts import widgetbox
from bokeh.models.widgets import Dropdown, Select, Slider


YEAR_TO_PLOT='2010'
COL_TO_PLOT='energy'
COUNTY_TO_PLOT='Denver'

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
        'value':[data_dict[county_id] if county_id in data_dict else float('NaN') for county_id in counties],
    })

def plot_state_data(dataname, data):
    color_mapper = LogColorMapper(palette=palette)


    TOOLS = "pan,wheel_zoom,reset,hover,save"

    p = figure(
        tools=TOOLS,
        x_axis_location=None, y_axis_location=None,
        match_aspect=True,
        plot_width=800, plot_height=350,
        tooltips=[
            ("Name", "@name"), ('value', "@value"), ("(Long, Lat)", "($x, $y)")
    ])
    p.grid.grid_line_color = None
    p.hover.point_policy = "follow_mouse"

    patches = p.patches('x', 'y', source=data,
              fill_color={'field': 'value', 'transform': color_mapper},
              fill_alpha=0.7, line_color="white", line_width=0.5)
    p.title.text = f'{dataname} in {YEAR_TO_PLOT}'.replace('_', ' ').title()
    # color_bar = ColorBar(color_mapper=color_mapper, ticker=LogTicker(),
    #                      label_standoff=12, border_line_color=None, location=(0,0))
    # p.add_layout(color_bar, 'right')

    return p, patches

def rename_columns(df):
    df['PV Capacity Installed, KWHr'] = df['energy']
    # df = df.drop('energy', axis=1)
    df = df['Energy Ussed, KWHr'] = df['energy_use']
    # df = df.drop('energy_use', axis=1)
    return df

def make_county_plot_data(dataname, data, county):

    for (c, df) in data.groupby('county'):
        if c == county:
            return (county, df['year'], df[dataname])



def plot_county_data(dataname, data, county):
    p = figure(plot_width=800, plot_height=250)
    # plots = {}
    p.title.text = f'{dataname} Over Time In {COUNTY_TO_PLOT}'.replace('_', ' ').title()
    (_, x, y) = make_county_plot_data(dataname, data, county)
    plot = p.line(x, y, line_width=2, alpha=0.8)
    return p, plot


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



def estimate_intalls(df):
    years = np.array(sorted(set(df['year'])))
    def gen():
        for county, county_df in df[['year', 'energy', 'county', 'energy_use']].groupby('county'):
            county_df = county_df.dropna()
            x = np.array([*county_df['year']])
            x = np.array([[xx-years[0], 1] for xx in x])
            y = np.array([*county_df['energy']])

            if len(y) > 2:
                (a,b), *_ = np.linalg.lstsq(x, y)
            else:
                a,b = 0, 0
            print(county)
            print(a,b)
            estimated_energy_installed = np.array([max(v, 0) for v in ((years-years[0]) * a + b)])
            print(estimated_energy_installed)
            esimtimated_total_energy = np.cumsum(estimated_energy_installed)
            energy_use = np.array([*df.loc[df['county'] == county, 'energy_use']])
            frac_solar_power = esimtimated_total_energy/energy_use
            # print(esimtimated_total_energy)
            for year, install, tot_install, non_sololar_pow in zip(years, estimated_energy_installed, esimtimated_total_energy, frac_solar_power):
                print(county, year, install, tot_install)
                yield {'year': year, 'power_installed': install, 'total_power_installed': tot_install, 'county': county, 'solar_power_fraction': non_sololar_pow}

    new_df = pd.DataFrame.from_dict(list(gen()))
    return do_merge(df, new_df)

def do_merge(A, B):
    return A.merge(B, on=['year', 'county'], how='outer').sort_values(by=['year'])


def merge_datafames(*args):
    args = list(args)
    A = args.pop()
    while args:
        A = do_merge(A, args.pop())
    return A

# df = pd.DataFrame.from_dict(list(gen_fake_rows()))
A, B = [pd.read_csv('data/estimate_install_production.csv'), pd.read_csv('data/EnergyConsumption.csv')]
df = do_merge(A, B)#A.merge(B, on=['year', 'county'], how='outer').sort_values(by=['year'])
df = estimate_intalls(df)
# df = rename_columns(df)

# import ipdb; ipdb.set_trace()

CO_data = make_state_data(df, counties, YEAR_TO_PLOT, COL_TO_PLOT)
(CO_plot_fig, CO_plot_patches) = plot_state_data(COL_TO_PLOT, CO_data)
(CO_county_fig, county_plot) = plot_county_data(COL_TO_PLOT, df, COUNTY_TO_PLOT)

def update_data():
    print('Updating plots:', YEAR_TO_PLOT, COL_TO_PLOT, COUNTY_TO_PLOT)
    new_data = make_state_data(df, counties, YEAR_TO_PLOT, COL_TO_PLOT)
    # CO_data[COL_TO_PLOT] = new_data[COL_TO_PLOT]
    CO_plot_fig.title.text = f'{COL_TO_PLOT} in {YEAR_TO_PLOT}'.replace('_', ' ').title()
    CO_plot_patches.data_source.data = new_data
    # color_mapper = LogColorMapper(palette=palette, low=min(new_data['value']), high=max(new_data['value']))
    cm = CO_plot_fig.select_one(LogColorMapper)
    # cm.update(low=min(new_data['value']), high=max(new_data['value']))
    cm.update(high=max(new_data['value']))

    (county, x, y) = make_county_plot_data(COL_TO_PLOT, df, COUNTY_TO_PLOT)
    county_plot.data_source.data = {'x': x, 'y': y}
    CO_county_fig.title.text = f'{COL_TO_PLOT} Over Time in {COUNTY_TO_PLOT}'.replace('_', ' ').title()


# construct year dropdown
def update_year_to_plot(atr, old, new):
    global YEAR_TO_PLOT
    YEAR_TO_PLOT = new
    update_data()

years = sorted(set(y for y in df['year']))
year_slider = Slider(start=years[0], end=years[-1], value=years[0], step=1,
                     title="Year")
year_slider.on_change('value', update_year_to_plot)
# construct counrt dropdown
def update_county_to_plot(atr, old, new):
    global COUNTY_TO_PLOT
    COUNTY_TO_PLOT = new
    update_data()

county_menu = sorted(set(((str(y), str(y)) for y in df['county'])))
county_dropdown = Select(title="County:", options=county_menu, value=COUNTY_TO_PLOT)
county_dropdown.on_change('value', update_county_to_plot)

# construct column dropdown
def update_col_to_plot(atr, old, new):
    global COL_TO_PLOT
    COL_TO_PLOT = new
    update_data()
col_data_menu = [(str(c), str(c)) for c in df.columns if c not in ['year','county']]
col_dropdown = Select(title="Data:", options=col_data_menu, value=COL_TO_PLOT)
col_dropdown.on_change('value', update_col_to_plot)

curdoc().add_root(column(year_slider, col_dropdown, CO_plot_fig, county_dropdown, CO_county_fig))
