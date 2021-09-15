import os

import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as dhc
from dash.dependencies import Input, Output, State
from paperworld.search.engine import SearchEngineFileSystem

search_engine = None

stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=stylesheets)


search_layout = dhc.Div([
    dcc.Input(id="search-input",
              type='search'),
    dhc.Button("Search", id="search-button", n_clicks=0),
])

main_layout = dhc.Div([],
                      id='main-layout')

app.layout = dhc.Div(
    [
        search_layout,
        main_layout

    ])


@app.callback(
    Output(component_id='main-layout', component_property='children'),
    Input(component_id='search-button', component_property='n_clicks'),
    State(component_id='search-input', component_property='value')
)
def update_output_div(n_clicks: int, query: str):
    if query is not None:

        query_result = search_engine.find_string(query, limit=None)

        cards = []
        for result in query_result:

            new_card = dbc.Card(
                [
                    dbc.CardBody(
                        [
                            dhc.H4(result['title'], className="card-title"),
                            dhc.P(result['path'], className="card-text")
                        ]
                    ),
                ],
                style={"width": "18rem"},
            )
            cards.append(new_card)
    else:
        cards = []

    return cards


if __name__ == "__main__":

    search_engine = SearchEngineFileSystem(
        path=os.path.expanduser('~/wbm_data/data'))

    search_engine.analyse()

    app.run_server(debug=True,
                   use_reloader=True,
                   dev_tools_hot_reload=True,
                   port=9090,
                   dev_tools_props_check=False)
