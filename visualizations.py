import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import os
import logging

from models import SessionLocal, Product, PriceHistory, Competitor
from sqlalchemy import desc, func

logger = logging.getLogger(__name__)

class PriceVisualizationEngine:
    """Generates visualizations and reports for competitor monitoring data"""
    
    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Set style for matplotlib
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def create_price_history_chart(self, product_id: int, days: int = 30) -> str:
        """Create a price history chart for a specific product"""
        db = SessionLocal()
        try:
            # Get product info
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            # Get price history
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            history = db.query(PriceHistory).filter(
                PriceHistory.product_id == product_id,
                PriceHistory.scraped_at >= cutoff_date
            ).order_by(PriceHistory.scraped_at).all()
            
            if not history:
                logger.warning(f"No price history found for product {product_id}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'date': entry.scraped_at,
                'price': entry.price,
                'availability': entry.availability
            } for entry in history])
            
            # Create plotly figure
            fig = go.Figure()
            
            # Add price line
            fig.add_trace(go.Scatter(
                x=df['date'],
                y=df['price'],
                mode='lines+markers',
                name=f'Price ({history[0].currency})',
                line=dict(color='#007bff', width=2),
                marker=dict(size=6)
            ))
            
            # Add availability annotations
            for _, row in df.iterrows():
                if row['availability'] and 'out of stock' in row['availability'].lower():
                    fig.add_vline(
                        x=row['date'],
                        line_dash="dash",
                        line_color="red",
                        annotation_text="Out of Stock",
                        annotation_position="top"
                    )
            
            # Update layout
            fig.update_layout(
                title=f"Price History: {product.name}<br><sub>{product.competitor.name}</sub>",
                xaxis_title="Date",
                yaxis_title=f"Price ({history[0].currency})",
                template="plotly_white",
                height=500,
                showlegend=True
            )
            
            # Add price statistics
            min_price = df['price'].min()
            max_price = df['price'].max()
            avg_price = df['price'].mean()
            current_price = df['price'].iloc[-1]
            
            fig.add_annotation(
                text=f"Current: ${current_price:.2f}<br>"
                     f"Min: ${min_price:.2f}<br>"
                     f"Max: ${max_price:.2f}<br>"
                     f"Avg: ${avg_price:.2f}",
                xref="paper", yref="paper",
                x=1.02, y=1,
                showarrow=False,
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="gray",
                borderwidth=1
            )
            
            # Save chart
            filename = f"price_history_{product_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            logger.info(f"Price history chart saved: {filepath}")
            return filepath
            
        finally:
            db.close()
    
    def create_competitor_comparison_chart(self, product_name_pattern: str) -> str:
        """Create a comparison chart across competitors for similar products"""
        db = SessionLocal()
        try:
            # Find products matching the pattern
            products = db.query(Product).filter(
                Product.name.contains(product_name_pattern),
                Product.is_active == True
            ).all()
            
            if not products:
                logger.warning(f"No products found matching pattern: {product_name_pattern}")
                return None
            
            comparison_data = []
            
            for product in products:
                # Get latest price
                latest_price = db.query(PriceHistory).filter(
                    PriceHistory.product_id == product.id
                ).order_by(desc(PriceHistory.scraped_at)).first()
                
                if latest_price:
                    comparison_data.append({
                        'competitor': product.competitor.name,
                        'product_name': product.name,
                        'price': latest_price.price,
                        'currency': latest_price.currency,
                        'availability': latest_price.availability,
                        'rating': latest_price.rating,
                        'last_updated': latest_price.scraped_at
                    })
            
            if not comparison_data:
                logger.warning("No price data found for comparison")
                return None
            
            df = pd.DataFrame(comparison_data)
            
            # Create comparison chart
            fig = px.bar(
                df,
                x='competitor',
                y='price',
                title=f'Price Comparison: {product_name_pattern}',
                labels={'price': f'Price ({df.iloc[0]["currency"]})', 'competitor': 'Competitor'},
                text='price'
            )
            
            # Customize chart
            fig.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
            fig.update_layout(
                template="plotly_white",
                height=500,
                showlegend=False
            )
            
            # Add rating information if available
            if df['rating'].notna().any():
                fig.add_trace(go.Scatter(
                    x=df['competitor'],
                    y=df['rating'] * df['price'].max() / 5,  # Scale rating to price range
                    mode='markers',
                    name='Rating (scaled)',
                    marker=dict(
                        size=df['rating'] * 5,
                        color='orange',
                        symbol='star'
                    ),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    yaxis2=dict(
                        title='Rating',
                        overlaying='y',
                        side='right',
                        range=[0, 5]
                    )
                )
            
            # Save chart
            filename = f"competitor_comparison_{product_name_pattern.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            logger.info(f"Competitor comparison chart saved: {filepath}")
            return filepath
            
        finally:
            db.close()
    
    def create_price_trend_analysis(self, days: int = 30) -> str:
        """Create a comprehensive price trend analysis across all products"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all price history within the timeframe
            query = db.query(
                PriceHistory.scraped_at,
                PriceHistory.price,
                Product.name.label('product_name'),
                Competitor.name.label('competitor_name')
            ).join(Product).join(Competitor).filter(
                PriceHistory.scraped_at >= cutoff_date,
                Product.is_active == True
            ).order_by(PriceHistory.scraped_at)
            
            results = query.all()
            
            if not results:
                logger.warning("No price data found for trend analysis")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'date': result.scraped_at,
                'price': result.price,
                'product': result.product_name,
                'competitor': result.competitor_name
            } for result in results])
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'Price Trends by Product',
                    'Average Price by Competitor',
                    'Price Volatility',
                    'Daily Price Changes'
                ),
                specs=[[{"secondary_y": False}, {"secondary_y": False}],
                       [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # 1. Price trends by product
            for product in df['product'].unique():
                product_data = df[df['product'] == product]
                fig.add_trace(
                    go.Scatter(
                        x=product_data['date'],
                        y=product_data['price'],
                        name=product[:30] + "..." if len(product) > 30 else product,
                        mode='lines',
                        showlegend=False
                    ),
                    row=1, col=1
                )
            
            # 2. Average price by competitor
            competitor_avg = df.groupby('competitor')['price'].mean().reset_index()
            fig.add_trace(
                go.Bar(
                    x=competitor_avg['competitor'],
                    y=competitor_avg['price'],
                    name='Avg Price',
                    showlegend=False
                ),
                row=1, col=2
            )
            
            # 3. Price volatility (standard deviation)
            volatility = df.groupby('product')['price'].std().reset_index()
            volatility = volatility.sort_values('price', ascending=False).head(10)
            fig.add_trace(
                go.Bar(
                    x=volatility['product'],
                    y=volatility['price'],
                    name='Price Volatility',
                    showlegend=False
                ),
                row=2, col=1
            )
            
            # 4. Daily price changes
            df['date_only'] = df['date'].dt.date
            daily_changes = df.groupby('date_only').agg({
                'price': ['count', 'mean', 'std']
            }).reset_index()
            daily_changes.columns = ['date', 'count', 'mean_price', 'price_std']
            
            fig.add_trace(
                go.Scatter(
                    x=daily_changes['date'],
                    y=daily_changes['mean_price'],
                    mode='lines+markers',
                    name='Daily Avg Price',
                    showlegend=False
                ),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                height=800,
                title_text=f"Price Trend Analysis - Last {days} Days",
                template="plotly_white"
            )
            
            # Save chart
            filename = f"price_trend_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            logger.info(f"Price trend analysis saved: {filepath}")
            return filepath
            
        finally:
            db.close()
    
    def create_monitoring_dashboard(self) -> str:
        """Create a comprehensive monitoring dashboard"""
        db = SessionLocal()
        try:
            # Get basic statistics
            total_competitors = db.query(Competitor).filter(Competitor.is_active == True).count()
            total_products = db.query(Product).filter(Product.is_active == True).count()
            total_price_entries = db.query(PriceHistory).count()
            
            # Get recent activity
            last_24h = datetime.utcnow() - timedelta(days=1)
            recent_entries = db.query(PriceHistory).filter(
                PriceHistory.scraped_at >= last_24h
            ).count()
            
            # Get latest prices by competitor
            latest_prices = db.query(
                Competitor.name.label('competitor'),
                func.count(Product.id).label('product_count'),
                func.avg(PriceHistory.price).label('avg_price')
            ).join(Product).join(PriceHistory).group_by(Competitor.name).all()
            
            # Create dashboard
            fig = make_subplots(
                rows=3, cols=2,
                subplot_titles=(
                    'System Overview',
                    'Products by Competitor',
                    'Average Prices by Competitor',
                    'Recent Activity (24h)',
                    'Price Distribution',
                    'Monitoring Status'
                ),
                specs=[
                    [{"type": "indicator"}, {"type": "pie"}],
                    [{"type": "bar"}, {"type": "bar"}],
                    [{"type": "histogram"}, {"type": "indicator"}]
                ]
            )
            
            # 1. System Overview (Indicators)
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=total_competitors,
                    title={"text": "Competitors"},
                    domain={'x': [0, 0.5], 'y': [0.7, 1]}
                ),
                row=1, col=1
            )
            
            # 2. Products by competitor (Pie chart)
            if latest_prices:
                competitor_names = [p.competitor for p in latest_prices]
                product_counts = [p.product_count for p in latest_prices]
                
                fig.add_trace(
                    go.Pie(
                        labels=competitor_names,
                        values=product_counts,
                        showlegend=True
                    ),
                    row=1, col=2
                )
            
            # 3. Average prices by competitor (Bar chart)
            if latest_prices:
                avg_prices = [p.avg_price for p in latest_prices]
                fig.add_trace(
                    go.Bar(
                        x=competitor_names,
                        y=avg_prices,
                        showlegend=False
                    ),
                    row=2, col=1
                )
            
            # 4. Recent activity
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=recent_entries,
                    title={"text": "Price Updates (24h)"},
                    domain={'x': [0.5, 1], 'y': [0.35, 0.65]}
                ),
                row=2, col=2
            )
            
            # 5. Price distribution
            all_prices = db.query(PriceHistory.price).all()
            if all_prices:
                prices = [p.price for p in all_prices]
                fig.add_trace(
                    go.Histogram(
                        x=prices,
                        showlegend=False,
                        nbinsx=20
                    ),
                    row=3, col=1
                )
            
            # 6. Monitoring status
            success_rate = (recent_entries / total_products * 100) if total_products > 0 else 0
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=success_rate,
                    title={"text": "Success Rate %"},
                    gauge={
                        'axis': {'range': [None, 100]},
                        'bar': {'color': "darkgreen"},
                        'steps': [
                            {'range': [0, 50], 'color': "lightgray"},
                            {'range': [50, 80], 'color': "yellow"},
                            {'range': [80, 100], 'color': "green"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': 90
                        }
                    },
                    domain={'x': [0.5, 1], 'y': [0, 0.3]}
                ),
                row=3, col=2
            )
            
            # Update layout
            fig.update_layout(
                height=1000,
                title_text="Competitor Monitoring Dashboard",
                template="plotly_white"
            )
            
            # Save dashboard
            filename = f"monitoring_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            filepath = os.path.join(self.output_dir, filename)
            fig.write_html(filepath)
            
            logger.info(f"Monitoring dashboard saved: {filepath}")
            return filepath
            
        finally:
            db.close()
    
    def generate_summary_report(self, days: int = 7) -> Dict[str, any]:
        """Generate a comprehensive summary report"""
        db = SessionLocal()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Basic statistics
            report = {
                'generated_at': datetime.utcnow(),
                'period_days': days,
                'total_competitors': db.query(Competitor).filter(Competitor.is_active == True).count(),
                'total_products': db.query(Product).filter(Product.is_active == True).count(),
                'total_price_entries': db.query(PriceHistory).filter(
                    PriceHistory.scraped_at >= cutoff_date
                ).count()
            }
            
            # Price change analysis
            products_with_changes = []
            products = db.query(Product).filter(Product.is_active == True).all()
            
            for product in products:
                # Get first and last price in the period
                first_price = db.query(PriceHistory).filter(
                    PriceHistory.product_id == product.id,
                    PriceHistory.scraped_at >= cutoff_date
                ).order_by(PriceHistory.scraped_at).first()
                
                last_price = db.query(PriceHistory).filter(
                    PriceHistory.product_id == product.id,
                    PriceHistory.scraped_at >= cutoff_date
                ).order_by(desc(PriceHistory.scraped_at)).first()
                
                if first_price and last_price and first_price.id != last_price.id:
                    change = last_price.price - first_price.price
                    change_pct = (change / first_price.price) * 100
                    
                    products_with_changes.append({
                        'product_name': product.name,
                        'competitor': product.competitor.name,
                        'first_price': first_price.price,
                        'last_price': last_price.price,
                        'change': change,
                        'change_percentage': change_pct
                    })
            
            # Sort by biggest changes
            products_with_changes.sort(key=lambda x: abs(x['change_percentage']), reverse=True)
            
            report['price_changes'] = {
                'total_products_with_changes': len(products_with_changes),
                'biggest_increases': [p for p in products_with_changes if p['change'] > 0][:5],
                'biggest_decreases': [p for p in products_with_changes if p['change'] < 0][:5]
            }
            
            # Competitor performance
            competitor_stats = []
            competitors = db.query(Competitor).filter(Competitor.is_active == True).all()
            
            for competitor in competitors:
                product_count = db.query(Product).filter(
                    Product.competitor_id == competitor.id,
                    Product.is_active == True
                ).count()
                
                avg_price = db.query(func.avg(PriceHistory.price)).join(Product).filter(
                    Product.competitor_id == competitor.id,
                    PriceHistory.scraped_at >= cutoff_date
                ).scalar()
                
                competitor_stats.append({
                    'name': competitor.name,
                    'product_count': product_count,
                    'average_price': float(avg_price) if avg_price else 0
                })
            
            report['competitor_stats'] = competitor_stats
            
            return report
            
        finally:
            db.close()

# Global visualization engine instance
viz_engine = PriceVisualizationEngine()