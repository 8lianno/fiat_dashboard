import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
from loguru import logger
from pathlib import Path
import json
import uuid
from fpdf import FPDF
import tempfile
import os

# Configure logging
logger.remove()
logger.add(
    "logs/finest_{time}.log",
    rotation="500 MB",
    retention="30 days",
    compression="zip",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

class TransactionLogger:
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.transaction_log = self.log_dir / "transactions.jsonl"
        
    def log_transaction(self, transaction):
        log_entry = {
            "timestamp": datetime.now(pytz.UTC).isoformat(),
            "transaction_id": str(uuid.uuid4()),
            "data": transaction,
        }
        with open(self.transaction_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        logger.info(f"Logged transaction {log_entry['transaction_id']}")

# Initialize logger
transaction_logger = TransactionLogger()

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'FINEST FIAT Payment Analytics Report', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def export_plotly_fig_as_image(fig, filename):
    fig.write_image(filename, format="png", engine="kaleido")
    return filename

def generate_pdf_report(df, figures, metrics):
    pdf = PDF()
    pdf.add_page()
    
    # Add title and date
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'Report Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'L')
    pdf.ln(10)
    
    # Add summary metrics
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Summary Metrics', 0, 1, 'L')
    pdf.set_font('Arial', '', 12)
    for metric_name, metric_value in metrics.items():
        pdf.cell(0, 10, f'{metric_name}: {metric_value}', 0, 1, 'L')
    pdf.ln(10)
    
    # Add charts
    for title, fig in figures.items():
        pdf.add_page()
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, title, 0, 1, 'L')
        
        # Save plotly figure as temporary image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img_path = export_plotly_fig_as_image(fig, tmp.name)
            pdf.image(img_path, x=10, y=pdf.get_y(), w=190)
            os.unlink(img_path)  # Clean up temporary file
        
        pdf.ln(140)  # Space for the next chart
    
    # Save PDF
    report_path = f"reports/payment_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    os.makedirs('reports', exist_ok=True)
    pdf.output(report_path)
    return report_path

# Set page config
st.set_page_config(page_title="FINEST FIAT Payment Analytics", layout="wide")

# Title
st.title("FINEST FIAT Payment Analytics")
st.markdown("Comprehensive payment analytics dashboard with real-time insights")

# File uploader
uploaded_file = st.file_uploader("Upload transaction data (CSV)", type="csv")

if uploaded_file is not None:
    try:
        # Load data
        df = pd.read_csv(uploaded_file)
        
        # Rename columns to simpler names
        df = df.rename(columns={
            'Cost & %': 'Fee_Percentage',
            'Net Profit & %': 'Net_Profit_Percentage',
            'P&L': 'Profit_Loss'
        })
        
        # Convert date
        df['request_time'] = pd.to_datetime(df['request_time'])
        
        # Calculate fee amount
        df['Fee'] = df['Amount'] * (df['Fee_Percentage'] / 100)
        
        # Log the upload
        transaction_logger.log_transaction({
            "action": "file_upload",
            "filename": uploaded_file.name,
            "rows": len(df)
        })
        
        # Add tabs for different analysis views
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Regional Analysis", "Method Analysis", "Channel Optimization"])
        
        with tab1:
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Volume", f"${df['Amount'].sum():,.2f}")
            with col2:
                st.metric("Total Transactions", f"{len(df):,}")
            with col3:
                st.metric("Average Transaction", f"${df['Amount'].mean():,.2f}")
            with col4:
                st.metric("Total Fees", f"${df['Fee'].sum():,.2f}")
            
            # Time series chart
            st.subheader("Transaction Volume Over Time")
            daily_volume = df.groupby(df['request_time'].dt.date).agg({
                'Amount': 'sum',
                'Fee': 'sum',
                'Profit_Loss': 'sum'
            }).reset_index()
            
            fig = px.line(daily_volume, x='request_time', y=['Amount', 'Fee', 'Profit_Loss'],
                         title='Daily Metrics',
                         labels={'value': 'Amount ($)', 'variable': 'Metric'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Channel analysis
            st.subheader("Channel Analysis")
            channel_metrics = df.groupby('Channel').agg({
                'Amount': ['sum', 'count', 'mean'],
                'Fee': ['sum', 'mean'],
                'Profit_Loss': ['sum', 'mean']
            }).round(2)
            
            # Rename columns for better readability
            channel_metrics.columns = [
                'Total Volume', 'Transaction Count', 'Avg Transaction',
                'Total Fees', 'Avg Fee',
                'Total P&L', 'Avg P&L'
            ]
            st.dataframe(channel_metrics)
            
            # Fee distribution
            st.subheader("Fee Analysis by Channel")
            col1, col2 = st.columns(2)
            
            with col1:
                fig_fee = px.box(df, x='Channel', y='Fee_Percentage',
                               title='Fee Percentage Distribution')
                st.plotly_chart(fig_fee, use_container_width=True)
            
            with col2:
                fig_pl = px.bar(df.groupby('Channel')['Profit_Loss'].sum().reset_index(),
                              x='Channel', y='Profit_Loss',
                              title='Profit/Loss by Channel')
                st.plotly_chart(fig_pl, use_container_width=True)
        
        with tab2:
            st.subheader("Regional Performance Analysis")
            
            # Regional volume distribution
            region_metrics = df.groupby('Country').agg({
                'Amount': ['sum', 'count', 'mean'],
                'Fee': ['sum', 'mean'],
                'Profit_Loss': ['sum', 'mean']
            }).round(2)
            
            # Calculate success rate and efficiency metrics
            region_metrics['Success_Rate'] = (df[df['Profit_Loss'] > 0].groupby('Country').size() / 
                                           df.groupby('Country').size() * 100).round(2)
            
            # Display regional metrics
            st.dataframe(region_metrics)
            
            # Regional comparison charts
            col1, col2 = st.columns(2)
            with col1:
                fig_region = px.treemap(df, 
                                      path=['Country', 'Channel'],
                                      values='Amount',
                                      title='Transaction Volume by Region and Channel')
                st.plotly_chart(fig_region, use_container_width=True)
            
            with col2:
                fig_region_fees = px.scatter(df, 
                                           x='Amount', 
                                           y='Fee_Percentage',
                                           color='Country',
                                           size='Amount',
                                           title='Fee Structure by Region')
                st.plotly_chart(fig_region_fees, use_container_width=True)
        
        with tab3:
            st.subheader("Payment Method Analysis")
            
            # Method performance metrics
            method_metrics = df.groupby('Method').agg({
                'Amount': ['sum', 'count', 'mean'],
                'Fee': ['sum', 'mean'],
                'Profit_Loss': ['sum', 'mean']
            }).round(2)
            
            # Calculate method efficiency score
            method_metrics['Efficiency_Score'] = (
                (method_metrics[('Profit_Loss', 'sum')] / method_metrics[('Amount', 'sum')]) * 100
            ).round(2)
            
            st.dataframe(method_metrics)
            
            # Method comparison visualizations
            col1, col2 = st.columns(2)
            with col1:
                fig_method = px.sunburst(df,
                                       path=['Method', 'Channel'],
                                       values='Amount',
                                       title='Transaction Distribution by Method')
                st.plotly_chart(fig_method, use_container_width=True)
            
            with col2:
                method_time = df.groupby([df['request_time'].dt.date, 'Method'])['Amount'].sum().reset_index()
                fig_method_trend = px.line(method_time,
                                         x='request_time',
                                         y='Amount',
                                         color='Method',
                                         title='Method Performance Over Time')
                st.plotly_chart(fig_method_trend, use_container_width=True)
        
        with tab4:
            st.subheader("Channel Optimization Insights")
            
            # Calculate channel efficiency metrics
            channel_efficiency = df.groupby('Channel').agg({
                'Amount': 'sum',
                'Fee': 'sum',
                'Profit_Loss': 'sum'
            }).reset_index()
            
            channel_efficiency['Fee_Ratio'] = (channel_efficiency['Fee'] / channel_efficiency['Amount'] * 100).round(2)
            channel_efficiency['Profit_Ratio'] = (channel_efficiency['Profit_Loss'] / channel_efficiency['Amount'] * 100).round(2)
            channel_efficiency['Efficiency_Score'] = (
                channel_efficiency['Profit_Ratio'] - channel_efficiency['Fee_Ratio']
            ).round(2)
            
            # Display channel recommendations
            st.dataframe(channel_efficiency)
            
            # Best performing channels
            st.subheader("Top Performing Channels")
            best_channels = channel_efficiency.nlargest(3, 'Efficiency_Score')
            for _, channel in best_channels.iterrows():
                st.info(f"""
                Channel: {channel['Channel']}
                - Efficiency Score: {channel['Efficiency_Score']}%
                - Fee Ratio: {channel['Fee_Ratio']}%
                - Profit Ratio: {channel['Profit_Ratio']}%
                - Total Volume: ${channel['Amount']:,.2f}
                """)
            
            # Channel optimization visualizations
            col1, col2 = st.columns(2)
            with col1:
                fig_efficiency = px.scatter(channel_efficiency,
                                          x='Fee_Ratio',
                                          y='Profit_Ratio',
                                          size='Amount',
                                          text='Channel',
                                          title='Channel Efficiency Matrix')
                fig_efficiency.add_hline(y=0, line_dash="dash", line_color="red")
                fig_efficiency.add_vline(x=0, line_dash="dash", line_color="red")
                st.plotly_chart(fig_efficiency, use_container_width=True)
            
            with col2:
                # Channel success rate by country
                channel_country = df.pivot_table(
                    values='Amount',
                    index='Channel',
                    columns='Country',
                    aggfunc='sum',
                    fill_value=0
                )
                fig_heat = px.imshow(channel_country,
                                   title='Channel Performance by Country',
                                   aspect='auto')
                st.plotly_chart(fig_heat, use_container_width=True)
            
            # Recommendations based on data
            st.subheader("Channel Optimization Recommendations")
            
            # Find best channel for each country
            best_by_country = df.groupby(['Country', 'Channel'])['Profit_Loss'].sum().reset_index()
            best_by_country = best_by_country.loc[best_by_country.groupby('Country')['Profit_Loss'].idxmax()]
            
            st.write("Best Performing Channels by Country:")
            for _, row in best_by_country.iterrows():
                st.success(f"{row['Country']}: {row['Channel']} (Profit: ${row['Profit_Loss']:,.2f})")
        
        # Add export button
        if st.button("Export Report as PDF"):
            with st.spinner("Generating PDF report..."):
                # Collect metrics
                metrics = {
                    "Total Volume": f"${df['Amount'].sum():,.2f}",
                    "Total Transactions": f"{len(df):,}",
                    "Average Transaction": f"${df['Amount'].mean():,.2f}",
                    "Total Fees": f"${df['Fee'].sum():,.2f}"
                }
                
                # Collect figures
                figures = {
                    "Daily Transaction Volume": fig,
                    "Channel Analysis": fig_pl,
                    "Regional Performance": fig_region,
                    "Fee Distribution": fig_fee,
                    "Method Performance": fig_method,
                    "Channel Efficiency": fig_efficiency,
                    "Channel Country Performance": fig_heat
                }
                
                # Generate PDF
                report_path = generate_pdf_report(df, figures, metrics)
                
                # Provide download link
                with open(report_path, "rb") as f:
                    st.download_button(
                        label="Download PDF Report",
                        data=f.read(),
                        file_name=os.path.basename(report_path),
                        mime="application/pdf"
                    )
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        st.error(f"Error processing file: {str(e)}")
else:
    st.info("""Please upload a CSV file with the following columns:
    - Type (Deposit/Withdrawal)
    - Country
    - Channel
    - Method
    - Amount
    - Cost & % (Fee percentage)
    - Net Profit & %
    - P&L (Profit/Loss)
    - request_time
    """)
