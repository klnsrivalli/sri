import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import requests
import json

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "E-commerce Competitor Monitor Dashboard"

# API base URL
API_BASE_URL = "http://localhost:8000"

def get_api_data(endpoint):
    """Get data from API"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching data from {endpoint}: {e}")
        return []

def create_overview_cards():
    """Create overview statistics cards"""
    try:
        stats = get_api_data("/stats/overview")
        
        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(stats.get('total_competitors', 0), className="card-title"),
                        html.P("Active Competitors", className="card-text")
                    ])
                ], color="primary", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(stats.get('total_products', 0), className="card-title"),
                        html.P("Products Monitored", className="card-text")
                    ])
                ], color="success", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(stats.get('total_alerts', 0), className="card-title"),
                        html.P("Total Alerts", className="card-text")
                    ])
                ], color="warning", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(stats.get('unread_alerts', 0), className="card-title"),
                        html.P("Unread Alerts", className="card-text")
                    ])
                ], color="danger", outline=True)
            ], width=3)
        ])
    except Exception as e:
        return html.Div(f"Error loading overview: {e}")

def create_price_history_chart(product_id):
    """Create price history chart for a product"""
    try:
        price_data = get_api_data(f"/products/{product_id}/price-history?days=30")
        
        if not price_data:
            return go.Figure().add_annotation(
                text="No price data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        df = pd.DataFrame(price_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            mode='lines+markers',
            name='Price',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=f"Price History - Product {product_id}",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            hovermode='x unified',
            height=400
        )
        
        return fig
    except Exception as e:
        return go.Figure().add_annotation(
            text=f"Error loading price data: {e}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

def create_availability_chart(product_id):
    """Create availability history chart for a product"""
    try:
        availability_data = get_api_data(f"/products/{product_id}/availability-history?days=30")
        
        if not availability_data:
            return go.Figure().add_annotation(
                text="No availability data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        df = pd.DataFrame(availability_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['is_available'].astype(int),
            mode='lines+markers',
            name='Availability',
            line=dict(color='green', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=f"Availability History - Product {product_id}",
            xaxis_title="Date",
            yaxis_title="Available (1=Yes, 0=No)",
            yaxis=dict(tickvals=[0, 1], ticktext=['Unavailable', 'Available']),
            hovermode='x unified',
            height=400
        )
        
        return fig
    except Exception as e:
        return go.Figure().add_annotation(
            text=f"Error loading availability data: {e}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

def create_alerts_table():
    """Create alerts table"""
    try:
        alerts = get_api_data("/alerts/?limit=20")
        
        if not alerts:
            return html.Div("No alerts found")
        
        table_header = [
            html.Thead(html.Tr([
                html.Th("Time"),
                html.Th("Type"),
                html.Th("Severity"),
                html.Th("Message"),
                html.Th("Status")
            ]))
        ]
        
        table_body = [html.Tbody([
            html.Tr([
                html.Td(alert['created_at'][:19]),  # Format timestamp
                html.Td(alert['alert_type'].replace('_', ' ').title()),
                html.Td(html.Span(
                    alert['severity'].upper(),
                    className=f"badge bg-{'danger' if alert['severity'] == 'high' else 'warning' if alert['severity'] == 'medium' else 'success'}"
                )),
                html.Td(alert['message'][:100] + "..." if len(alert['message']) > 100 else alert['message']),
                html.Td("Read" if alert['is_read'] else "Unread")
            ]) for alert in alerts
        ])]
        
        return dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True)
    except Exception as e:
        return html.Div(f"Error loading alerts: {e}")

def create_competitor_comparison_chart():
    """Create competitor comparison chart"""
    try:
        competitors = get_api_data("/competitors/")
        
        if not competitors:
            return go.Figure().add_annotation(
                text="No competitors found",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        competitor_stats = []
        for competitor in competitors:
            stats = get_api_data(f"/stats/competitor/{competitor['id']}")
            if stats:
                competitor_stats.append(stats)
        
        if not competitor_stats:
            return go.Figure().add_annotation(
                text="No competitor statistics available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        df = pd.DataFrame(competitor_stats)
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Total Products', 'Active Products', 'Recent Price Changes', 'Recent Availability Changes'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Total Products
        fig.add_trace(
            go.Bar(x=df['competitor'], y=df['total_products'], name='Total Products'),
            row=1, col=1
        )
        
        # Active Products
        fig.add_trace(
            go.Bar(x=df['competitor'], y=df['active_products'], name='Active Products'),
            row=1, col=2
        )
        
        # Recent Price Changes
        fig.add_trace(
            go.Bar(x=df['competitor'], y=df['recent_price_changes'], name='Price Changes'),
            row=2, col=1
        )
        
        # Recent Availability Changes
        fig.add_trace(
            go.Bar(x=df['competitor'], y=df['recent_availability_changes'], name='Availability Changes'),
            row=2, col=2
        )
        
        fig.update_layout(
            title="Competitor Comparison",
            height=600,
            showlegend=False
        )
        
        return fig
    except Exception as e:
        return go.Figure().add_annotation(
            text=f"Error loading competitor data: {e}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🛒 E-commerce Competitor Monitor", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    # Overview Cards
    dbc.Row([
        dbc.Col([
            html.H3("Overview", className="mb-3"),
            html.Div(id="overview-cards")
        ])
    ], className="mb-4"),
    
    # Main Content Tabs
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Recent Alerts", className="mb-3"),
                            html.Div(id="alerts-table")
                        ], width=12)
                    ])
                ], label="Alerts", tab_id="alerts-tab"),
                
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Competitor Comparison", className="mb-3"),
                            dcc.Graph(id="competitor-comparison-chart")
                        ], width=12)
                    ])
                ], label="Competitors", tab_id="competitors-tab"),
                
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Product Monitoring", className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    html.Label("Select Product ID:"),
                                    dcc.Input(
                                        id="product-id-input",
                                        type="number",
                                        value=1,
                                        placeholder="Enter product ID"
                                    )
                                ], width=3)
                            ], className="mb-3"),
                            dbc.Row([
                                dbc.Col([
                                    dcc.Graph(id="price-history-chart")
                                ], width=6),
                                dbc.Col([
                                    dcc.Graph(id="availability-chart")
                                ], width=6)
                            ])
                        ], width=12)
                    ])
                ], label="Products", tab_id="products-tab"),
                
                dbc.Tab([
                    dbc.Row([
                        dbc.Col([
                            html.H4("Monitoring Control", className="mb-3"),
                            dbc.Button("Start Monitoring", id="start-monitoring-btn", color="success", className="me-2"),
                            dbc.Button("Stop Monitoring", id="stop-monitoring-btn", color="danger", className="me-2"),
                            dbc.Button("Run Single Cycle", id="run-cycle-btn", color="primary", className="me-2"),
                            html.Div(id="monitoring-status", className="mt-3")
                        ], width=12)
                    ])
                ], label="Control", tab_id="control-tab")
            ], id="main-tabs")
        ])
    ]),
    
    # Refresh interval
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # Refresh every 30 seconds
        n_intervals=0
    )
], fluid=True)

# Callbacks
@app.callback(
    Output("overview-cards", "children"),
    Input("interval-component", "n_intervals")
)
def update_overview_cards(n):
    return create_overview_cards()

@app.callback(
    Output("alerts-table", "children"),
    Input("interval-component", "n_intervals")
)
def update_alerts_table(n):
    return create_alerts_table()

@app.callback(
    Output("competitor-comparison-chart", "figure"),
    Input("interval-component", "n_intervals")
)
def update_competitor_chart(n):
    return create_competitor_comparison_chart()

@app.callback(
    [Output("price-history-chart", "figure"),
     Output("availability-chart", "figure")],
    [Input("product-id-input", "value"),
     Input("interval-component", "n_intervals")]
)
def update_product_charts(product_id, n):
    if not product_id:
        product_id = 1
    
    price_fig = create_price_history_chart(product_id)
    availability_fig = create_availability_chart(product_id)
    
    return price_fig, availability_fig

@app.callback(
    Output("monitoring-status", "children"),
    [Input("start-monitoring-btn", "n_clicks"),
     Input("stop-monitoring-btn", "n_clicks"),
     Input("run-cycle-btn", "n_clicks")]
)
def handle_monitoring_controls(start_clicks, stop_clicks, run_clicks):
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return ""
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    try:
        if button_id == "start-monitoring-btn":
            response = requests.post(f"{API_BASE_URL}/monitor/start")
            return dbc.Alert("Monitoring started successfully!", color="success")
        
        elif button_id == "stop-monitoring-btn":
            response = requests.post(f"{API_BASE_URL}/monitor/stop")
            return dbc.Alert("Monitoring stopped successfully!", color="warning")
        
        elif button_id == "run-cycle-btn":
            response = requests.post(f"{API_BASE_URL}/monitor/run-cycle")
            return dbc.Alert("Monitoring cycle completed!", color="info")
    
    except Exception as e:
        return dbc.Alert(f"Error: {e}", color="danger")
    
    return ""

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)