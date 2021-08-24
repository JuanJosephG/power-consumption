import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px


from dash.dependencies import Input, Output
from utils.s3_connection import S3Connection
from utils.figures import Figures


app = dash.Dash(__name__,title="CNEL")
server = app.server

# Read s3Utils
cnel_bucket = S3Connection()
df_cnel= cnel_bucket.read_df_cnel_latlong()

#df_cnel_gye.drop('Unnamed: 0', axis=1, inplace=True)

figures = Figures(df_cnel)

cluster_2dim_data = []
for cluster2 in sorted(df_cnel['cluster_2d'].unique()):
  count = df_cnel.loc[(df_cnel["cluster_2d"] == cluster2)].shape[0]
  data = (cluster2, count)
  cluster_2dim_data.append(data)

cluster_24dim_data = []
for cluster24 in sorted(df_cnel['cluster'].unique()):
  count = df_cnel.loc[(df_cnel["cluster"] == cluster24)].shape[0]
  data = (cluster24, count)
  cluster_24dim_data.append(data)

cluster_2dim_dbscan_data = []
for cluster_2d_dbscan in sorted(df_cnel['cluster_dbscan_2d'].unique(),key=int):
  if(cluster_2d_dbscan != '-1'):
    count = df_cnel.loc[(df_cnel["cluster_dbscan_2d"] == cluster_2d_dbscan)].shape[0]
    data = (cluster_2d_dbscan, count)
    cluster_2dim_dbscan_data.append(data)

estratos_data = []
for estrato in sorted(df_cnel['estrato'].unique()):
  if (estrato != '5' and estrato != "X"):
    count = df_cnel.loc[(df_cnel["estrato"] == estrato)].shape[0]
    data = (estrato, count)
    estratos_data.append(data)

app.layout = html.Div(
    [
        dcc.Store(id='aggregate_data'),
        html.Div(
            [
                html.Div(
                    [
                        html.H2(
                            'CNEL Consumo Eléctrico',
                        ),
                        html.H4(
                            'Evaluación de Clustering',
                        )
                    ],

                    className='eight columns'
                ),
                html.Img(
                    src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe.png",
                    className='two columns',
                ),
                html.A(
                    html.Button(
                        "Learn More",
                        id="learnMore"

                    ),
                    href="https://plot.ly/dash/pricing/",
                    className="two columns"
                )
            ],
            id="header",
            className='row',
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            'Métodos de Clustering y Estratificación:',
                            className="control_label"
                        ),
                        dcc.RadioItems(
                            id='clustering_selector',
                            options=[
                                {'label': 'Kmeans', 'value': 'kmeans'},
                                {'label': 'DBSCAN', 'value': 'dbscan'},
                                {'label': 'Estratificación Actual', 'value': 'actual'},
                            ],
                            value='kmeans',
                            labelStyle={'display': 'inline-block'},
                            className="dcc_control"
                        ),
                        html.P(
                            'Estratificaciones Disponibles:',
                            className="control_label"
                        ),
                        dcc.RadioItems(
                            id = 'dim_selector',
                            options=[
                                {'label': 'Usando 24 Meses', 'value': '24'},
                                {'label': 'Usando Promedio y Desviación Estándar', 'value': '2'},
                            ],
                            value='24',
                            labelStyle={'display': 'block'},
                            className="dcc_control"
                        ),
                    ],
                    className="pretty_container four columns"
                ),
                html.Div(
                    [   
                        html.Div(
                            [
                                html.P(
                                    'Registros de CNEL - Consumo 2019 a 2020',
                                ),
                            ],
                            className="info_text"
                        ),
                        # Row para CNEL original
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P("No. de Registros"),
                                        html.H6(
                                            "458860",
                                            id="total_reg",
                                            className="info_text"
                                        )
                                    ],
                                    id="wells",
                                    className="pretty_container"
                                ),

                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.P("No. Reg. < 10 KWH"),
                                                html.H6(
                                                    "27345",
                                                    id="less10Text",
                                                    className="info_text"
                                                )
                                            ],
                                            id="less10",
                                            className="pretty_container"
                                        ),
                                        html.Div(
                                            [
                                                html.P("No. Reg. > 1000 KWH"),
                                                html.H6(
                                                    "23353",
                                                    id="grather10Text",
                                                    className="info_text"
                                                )
                                            ],
                                            id="grather10",
                                            className="pretty_container"
                                        ),
                                        html.Div(
                                            [
                                                html.P("Registros Usados"),
                                                html.H6(
                                                    "408162",
                                                    id="regUseText",
                                                    className="info_text"
                                                )
                                            ],
                                            id="reguse",
                                            className="pretty_container"
                                        ),
                                    ],
                                    id="tripleContainer",
                                )

                            ],
                            id="infoContainer",
                            className="row"
                        ),
                    ],
                    id="rightCol",
                    className="eight columns"
                )
            ],
            className="row"
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Loading(
                            children=dcc.Graph(
                                id='main_graph',
                                figure=figures.plot_fig()
                            )
                        )
                    ],
                    className='pretty_container six columns',
                ),
                html.Div(
                    [
                        dcc.Loading(
                            children=dcc.Graph(
                                id='individual_graph'
                            )
                        )
                    ],
                    className='pretty_container six columns',
                ),

            ],
            className='row'
        )
    ],
    id="mainContainer",
    style={
        "display": "flex",
        "flex-direction": "column"
    }
)

# Callback to use map
@app.callback(
    Output("main_graph", "figure"),
    [Input("clustering_selector", "value")],
    [Input("dim_selector", "value")])
def update_figure(clustering_selector, dim_selector):
    if clustering_selector == 'kmeans':
        if dim_selector == '2':
            list_cluster = cluster_2dim_data
            return figures.plot_fig2d()
        elif dim_selector == '24':
            list_cluster = cluster_24dim_data
            return figures.plot_fig()

    if clustering_selector == 'dbscan':
        if dim_selector == '2':
            list_cluster = cluster_2dim_dbscan_data
            return figures.plot_fig2d_dbscan()

    if clustering_selector == 'actual':
        list_cluster = estratos_data
        return figures.plot_estratos()

# Callback to use line plot
@app.callback(
    Output("individual_graph", "figure"),
    [Input("main_graph", "hoverData")])
def update_line_plot(hoverData):
  chosen = [point['hovertext'] for point in hoverData['points']]
  promedio = hoverData['points'][0]['customdata'][0]
  cuentacontrato = chosen[0]
  return figures.plot_individual(cuentacontrato, promedio)


# Main
if __name__ == '__main__':
    app.run_server(debug=True, threaded=True, dev_tools_ui=True)
