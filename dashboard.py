#!/usr/bin/env python3
"""
E-commerce Competitor Monitoring Dashboard
Interactive web dashboard for monitoring data visualization
"""

import dash
from dash import dcc, html, Input, Output, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import requests
from datetime import datetime, timedelta
import json

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Competitor Monitor Dashboard"

# API base URL
API_BASE = "http://localhost:8000/api"

def get_api_data(endpoint):
    """Get data from API endpoint."""
    try:
        response = requests.get(f"{API_BASE}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return {}

def create_price_history_chart(product_id):
    """Create price history chart for a product."""
    data = get_api_data(f"products/{product_id}/history")
    
    if not data or 'price_history' not in data:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    df = pd.DataFrame(data['price_history'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Price History', 'Stock Status'),
        vertical_spacing=0.1,
        row_heights=[0.7, 0.3]
    )
    
    # Price line
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            mode='lines+markers',
            name='Price',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ),
        row=1, col=1
    )
    
    # Stock status
    stock_colors = {
        'in_stock': 'green',
        'out_of_stock': 'red',
        'limited': 'orange',
        'unknown': 'gray'
    }
    
    for status in df['stock_status'].unique():
        if pd.notna(status):
            status_data = df[df['stock_status'] == status]
            fig.add_trace(
                go.Scatter(
                    x=status_data['timestamp'],
                    y=[status] * len(status_data),
                    mode='markers',
                    name=f'Stock: {status}',
                    marker=dict(
                        color=stock_colors.get(status, 'gray'),
                        size=10,
                        symbol='circle'
                    )
                ),
                row=2, col=1
            )
    
    fig.update_layout(
        title=f"Product {product_id} - Price and Stock History",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=600,
        showlegend=True
    )
    
    return fig

def create_competitor_summary_chart():
    """Create competitor summary chart."""
    data = get_api_data("competitors")
    
    if not data or 'products_per_competitor' not in data:
        return go.Figure().add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    competitors = list(data['products_per_competitor'].keys())
    counts = list(data['products_per_competitor'].values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=competitors,
            y=counts,
            marker_color='lightblue',
            text=counts,
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Products per Competitor",
        xaxis_title="Competitor",
        yaxis_title="Number of Products",
        height=400
    )
    
    return fig

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🛒 Competitor Monitor Dashboard", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    # Status cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Monitoring Status", className="card-title"),
                    html.P(id="status-text", className="card-text")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Products", className="card-title"),
                    html.P(id="total-products", className="card-text")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Competitors", className="card-title"),
                    html.P(id="total-competitors", className="card-text")
                ])
            ])
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Last Update", className="card-title"),
                    html.P(id="last-update", className="card-text")
                ])
            ])
        ], width=3)
    ], className="mb-4"),
    
    # Control buttons
    dbc.Row([
        dbc.Col([
            dbc.ButtonGroup([
                dbc.Button("Start Monitoring", id="start-btn", color="success", n_clicks=0),
                dbc.Button("Stop Monitoring", id="stop-btn", color="danger", n_clicks=0),
                dbc.Button("Run Cycle", id="cycle-btn", color="primary", n_clicks=0),
                dbc.Button("Refresh Data", id="refresh-btn", color="info", n_clicks=0)
            ], className="mb-3")
        ], className="text-center")
    ]),
    
    # Products table
    dbc.Row([
        dbc.Col([
            html.H3("Monitored Products"),
            html.Div(id="products-table")
        ])
    ], className="mb-4"),
    
    # Charts
    dbc.Row([
        dbc.Col([
            html.H3("Competitor Summary"),
            dcc.Graph(id="competitor-chart")
        ], width=6),
        dbc.Col([
            html.H3("Product Price History"),
            dcc.Dropdown(
                id="product-dropdown",
                placeholder="Select a product to view price history"
            ),
            dcc.Graph(id="price-history-chart")
        ], width=6)
    ]),
    
    # Hidden div for storing data
    html.Div(id="data-store", style={"display": "none"}),
    
    # Interval component for auto-refresh
    dcc.Interval(
        id="interval-component",
        interval=30000,  # 30 seconds
        n_intervals=0
    )
], fluid=True)

# Callbacks
@app.callback(
    [Output("status-text", "children"),
     Output("total-products", "children"),
     Output("total-competitors", "children"),
     Output("last-update", "children")],
    [Input("refresh-btn", "n_clicks"),
     Input("interval-component", "n_intervals")]
)
def update_status_cards(n_clicks, n_intervals):
    """Update status cards with current monitoring information."""
    status_data = get_api_data("status")
    
    if not status_data:
        return "Error", "Error", "Error", "Error"
    
    status_text = "🟢 Running" if status_data.get('is_running', False) else "🔴 Stopped"
    total_products = str(status_data.get('total_products', 0))
    total_competitors = str(status_data.get('total_competitors', 0))
    
    last_session = status_data.get('last_session', {})
    if last_session and last_session.get('started_at'):
        last_update = datetime.fromisoformat(last_session['started_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
    else:
        last_update = "Never"
    
    return status_text, total_products, total_competitors, last_update

@app.callback(
    Output("products-table", "children"),
    [Input("refresh-btn", "n_clicks"),
     Input("interval-component", "n_intervals")]
)
def update_products_table(n_clicks, n_intervals):
    """Update products table."""
    products_data = get_api_data("products")
    
    if not products_data or 'products' not in products_data:
        return html.P("No products found or error loading data")
    
    products = products_data['products']
    
    if not products:
        return html.P("No products are currently being monitored")
    
    # Create table
    table_header = [
        html.Thead(html.Tr([
            html.Th("ID"),
            html.Th("Name"),
            html.Th("Competitor"),
            html.Th("Category"),
            html.Th("Target Price"),
            html.Th("Added")
        ]))
    ]
    
    table_body = [html.Tbody([
        html.Tr([
            html.Td(product['id']),
            html.Td(html.A(product['name'], href=product['url'], target="_blank")),
            html.Td(product['competitor']),
            html.Td(product['category'] or "N/A"),
            html.Td(f"${product['target_price']:.2f}" if product['target_price'] else "N/A"),
            html.Td(datetime.fromisoformat(product['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d'))
        ]) for product in products
    ])]
    
    return dbc.Table(table_header + table_body, bordered=True, hover=True)

@app.callback(
    Output("competitor-chart", "figure"),
    [Input("refresh-btn", "n_clicks"),
     Input("interval-component", "n_intervals")]
)
def update_competitor_chart(n_clicks, n_intervals):
    """Update competitor summary chart."""
    return create_competitor_summary_chart()

@app.callback(
    [Output("product-dropdown", "options"),
     Output("product-dropdown", "value")],
    [Input("refresh-btn", "n_clicks"),
     Input("interval-component", "n_intervals")]
)
def update_product_dropdown(n_clicks, n_intervals):
    """Update product dropdown options."""
    products_data = get_api_data("products")
    
    if not products_data or 'products' not in products_data:
        return [], None
    
    products = products_data['products']
    options = [
        {"label": f"{p['id']} - {p['name']}", "value": p['id']}
        for p in products
    ]
    
    return options, None

@app.callback(
    Output("price-history-chart", "figure"),
    [Input("product-dropdown", "value")]
)
def update_price_history_chart(selected_product_id):
    """Update price history chart based on selected product."""
    if not selected_product_id:
        return go.Figure().add_annotation(
            text="Select a product to view price history",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
    
    return create_price_history_chart(selected_product_id)

@app.callback(
    [Output("start-btn", "disabled"),
     Output("stop-btn", "disabled")],
    [Input("start-btn", "n_clicks"),
     Input("stop-btn", "n_clicks"),
     Input("interval-component", "n_intervals")]
)
def update_button_states(start_clicks, stop_clicks, n_intervals):
    """Update button states based on monitoring status."""
    status_data = get_api_data("status")
    is_running = status_data.get('is_running', False)
    
    return is_running, not is_running

@app.callback(
    Output("data-store", "children"),
    [Input("start-btn", "n_clicks"),
     Input("stop-btn", "n_clicks"),
     Input("cycle-btn", "n_clicks")]
)
def handle_button_clicks(start_clicks, stop_clicks, cycle_clicks):
    """Handle button clicks for monitoring control."""
    ctx = callback_context
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == "start-btn":
            response = requests.post(f"{API_BASE}/monitor/start")
            return f"Start monitoring: {response.status_code}"
        elif button_id == "stop-btn":
            response = requests.post(f"{API_BASE}/monitor/stop")
            return f"Stop monitoring: {response.status_code}"
        elif button_id == "cycle-btn":
            response = requests.post(f"{API_BASE}/monitor/run-cycle")
            return f"Run cycle: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"
    
    return ""

if __name__ == "__main__":
    app.run_server(
        host="0.0.0.0",
        port=8050,
        debug=True
    )