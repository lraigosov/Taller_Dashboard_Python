import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go

# ETL para cargar y procesar datos
def load_and_process_data(file_path):
    df = pd.read_csv(file_path)
    
    # Proceso ETL para eliminar símbolos de dólar y comas
    if 'Client Name' in df.columns:
        df.iloc[:, 4:] = df.iloc[:, 4:].replace('[\$,]', '', regex=True).astype(float)        

    # Reemplazar puntos por comas en todos los valores correspondientes a períodos
    df.iloc[:, 4:] = df.iloc[:, 4:].replace('\.', ',', regex=True)

    return df

# Cargar datos
costs_df = load_and_process_data('data\\costs_2022.csv')
revenue_df = load_and_process_data('data\\revenue_2022.csv')

# Eliminar "Revenue" del campo 'Line Of Business'
revenue_df['Line Of Business'] = revenue_df['Line Of Business'].str.replace(' Revenue', '')

# Obtener todas las opciones únicas de 'Line Of Business'
all_lines = list(set(costs_df['Line Of Business'].unique()) | set(revenue_df['Line Of Business'].unique()))

# Iniciar la aplicación Dash
app = dash.Dash(__name__)

# Crear el layout del Dashboard
app.layout = html.Div([
    html.H1("Evolución de Ingresos y Costos"),
    
    html.Div([
        html.P("La escala de los costos se ha ajustado para mejorar la visualización. Los valores de costos se han dividido por un factor muy pequeño (0.00000001) para reducir su magnitud en la gráfica. Esto significa que un valor de costo en la gráfica es equivalente a {cost_scaling_factor:.0e} veces el valor real."),
    ], style={'margin-bottom': '20px'}),

    dcc.Dropdown(
        id='line-of-business-dropdown',
        options=[{'label': i, 'value': i} for i in all_lines],
        multi=True,
        value=all_lines
    ),

    dcc.Graph(id='combined-graph')
])

# Callback para actualizar la gráfica según la selección
@app.callback(
    Output('combined-graph', 'figure'),
    [Input('line-of-business-dropdown', 'value')]
)
def update_graph(selected_lines):
    # Filtrar datos según la selección de líneas de negocio
    filtered_revenue = revenue_df[revenue_df['Line Of Business'].isin(selected_lines)]
    filtered_costs = costs_df[costs_df['Line Of Business'].isin(selected_lines)]

    # Agrupar y sumar los ingresos y costos de cada mes
    grouped_revenue = filtered_revenue.groupby('Line Of Business').sum().iloc[:, 3:-1]
    grouped_costs = filtered_costs.groupby('Line Of Business').sum().iloc[:, 3:-1]

    # Normalizar los costos dividiéndolos por un factor
    cost_scaling_factor = 0.00000001
    scaled_costs = grouped_costs * cost_scaling_factor

    # Crear gráfica con barras para ingresos y costos
    fig = go.Figure()

    for line in grouped_revenue.index:
        # Añadir barras para los ingresos (valores positivos)
        fig.add_trace(go.Bar(x=grouped_revenue.columns, y=grouped_revenue.loc[line], name=f'{line}'))

    for line in scaled_costs.index:
        # Añadir barras para los costos (valores negativos y normalizados)
        fig.add_trace(go.Bar(x=grouped_costs.columns, y=-scaled_costs.loc[line], name=f'{line}'))

    # Establecer títulos de ejes para la gráfica
    fig.update_layout(
        title='Evolución de Ingresos y Costos por Línea de Negocio',
        xaxis={'title': 'Mes'},
        yaxis={'title': 'Valor'},
        legend={'orientation': 'h', 'y': 1.2},
        height=800
    )

    return fig

# Iniciar la aplicación
if __name__ == '__main__':
    app.run_server(debug=True)