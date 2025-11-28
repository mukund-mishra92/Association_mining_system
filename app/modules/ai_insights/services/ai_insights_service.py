"""
AI Insights Service - Core Intelligence Engine
Provides advanced analytics for order data and inventory optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pymysql
import logging
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

class AIInsightsService:
    def __init__(self, db_config: Dict[str, Any]):
        """Initialize AI Insights Service with database configuration"""
        self.db_config = {
            'host': db_config.get('host', 'localhost'),
            'port': db_config.get('port', 3306),
            'user': db_config.get('user', 'root'),
            'password': db_config.get('password', ''),
            'database': db_config.get('database', 'neo'),
        }
        self.order_table = db_config.get('order_table', 'wms_to_wcs_order_line_request_data')
        self.sku_table = db_config.get('sku_master_table', 'sku_master')
        self.logger = logging.getLogger(__name__)

    def get_connection(self):
        """Get database connection"""
        return pymysql.connect(**self.db_config)
    
    def _flatten_dict(self, d):
        """Flatten dictionary with tuple keys for JSON serialization"""
        if isinstance(d, dict):
            return {str(k): (float(v) if isinstance(v, (np.integer, np.floating)) else v) for k, v in d.items()}
        return d

    def analyze_order_patterns(self, days_back: int = 90, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Comprehensive order pattern analysis
        """
        try:
            connection = self.get_connection()
            
            # Handle date range parameters
            if start_date and end_date:
                # Use custom date range
                cutoff_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_analysis_date = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                # First, get the date range available in the data
                date_range_query = f"""
                SELECT 
                    MIN(INSERTED_TIMESTAMP) as earliest_date,
                    MAX(INSERTED_TIMESTAMP) as latest_date
                FROM {self.order_table}
                """
                df_range = pd.read_sql(date_range_query, connection)
                
                if not df_range.empty:
                    latest_date = df_range.iloc[0]['latest_date']
                    earliest_date = df_range.iloc[0]['earliest_date']
                    # Use data range from the latest available date backwards
                    cutoff_date = latest_date - timedelta(days=days_back)
                    end_analysis_date = latest_date
                else:
                    # Fallback to current date if no data found
                    latest_date = datetime.now()
                    earliest_date = datetime.now() - timedelta(days=365)
                    cutoff_date = datetime.now() - timedelta(days=days_back)
                    end_analysis_date = datetime.now()
            
            # Build query with appropriate date range
            if start_date and end_date:
                query = f"""
                SELECT 
                    DATE(INSERTED_TIMESTAMP) as order_day,
                    HOUR(INSERTED_TIMESTAMP) as order_hour,
                    DAYOFWEEK(INSERTED_TIMESTAMP) as day_of_week,
                    WEEK(INSERTED_TIMESTAMP) as week_number,
                    MONTH(INSERTED_TIMESTAMP) as month_number,
                    ARTICLE_ID as sku_id,
                    QUANTITY as quantity,
                    INSERTED_TIMESTAMP as order_date,
                    CASE 
                        WHEN DAYOFWEEK(INSERTED_TIMESTAMP) IN (1,7) THEN 'Weekend'
                        ELSE 'Weekday'
                    END as day_type
                FROM {self.order_table}
                WHERE INSERTED_TIMESTAMP >= %s AND INSERTED_TIMESTAMP <= %s
                ORDER BY INSERTED_TIMESTAMP
                """
                df = pd.read_sql(query, connection, params=[cutoff_date, end_analysis_date])
            else:
                query = f"""
                SELECT 
                    DATE(INSERTED_TIMESTAMP) as order_day,
                    HOUR(INSERTED_TIMESTAMP) as order_hour,
                    DAYOFWEEK(INSERTED_TIMESTAMP) as day_of_week,
                    WEEK(INSERTED_TIMESTAMP) as week_number,
                    MONTH(INSERTED_TIMESTAMP) as month_number,
                    ARTICLE_ID as sku_id,
                    QUANTITY as quantity,
                    INSERTED_TIMESTAMP as order_date,
                    CASE 
                        WHEN DAYOFWEEK(INSERTED_TIMESTAMP) IN (1,7) THEN 'Weekend'
                        ELSE 'Weekday'
                    END as day_type
                FROM {self.order_table}
                WHERE INSERTED_TIMESTAMP >= %s
                ORDER BY INSERTED_TIMESTAMP
                """
                df = pd.read_sql(query, connection, params=[cutoff_date])
            connection.close()
            
            if df.empty:
                return {"error": "No order data found for analysis"}
            
            # Convert order_date to datetime
            df['order_date'] = pd.to_datetime(df['order_date'])
            
            # 1. Daily Order Patterns
            daily_patterns = self._analyze_daily_patterns(df)
            
            # 2. Hourly Distribution
            hourly_patterns = self._analyze_hourly_patterns(df)
            
            # 3. Weekly Trends
            weekly_trends = self._analyze_weekly_trends(df)
            
            # 4. SKU Performance Analysis
            sku_analysis = self._analyze_sku_performance(df)
            
            # 5. Seasonal Analysis
            seasonal_analysis = self._analyze_seasonal_patterns(df)
            
            # 6. Order Volume Predictions
            volume_predictions = self._predict_order_volumes(df)
            
            # Calculate analysis period details
            if start_date and end_date:
                actual_end_date = end_analysis_date
                analysis_days = (end_analysis_date - cutoff_date).days
            else:
                actual_end_date = end_analysis_date  # This is set in both branches above
                analysis_days = days_back
            
            return {
                "analysis_period": {
                    "start_date": cutoff_date.strftime('%Y-%m-%d'),
                    "end_date": actual_end_date.strftime('%Y-%m-%d'),
                    "actual_days": (actual_end_date - cutoff_date).days,
                    "total_days": analysis_days,
                    "total_orders": len(df),
                    "unique_skus": df['sku_id'].nunique()
                },
                "daily_patterns": daily_patterns,
                "hourly_patterns": hourly_patterns,
                "weekly_trends": weekly_trends,
                "sku_analysis": sku_analysis,
                "seasonal_analysis": seasonal_analysis,
                "volume_predictions": volume_predictions
            }
            
        except Exception as e:
            self.logger.error(f"Error in order pattern analysis: {str(e)}")
            return {"error": str(e)}

    def _analyze_daily_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze daily order patterns"""
        daily_stats = df.groupby('order_day').agg({
            'sku_id': 'count',
            'quantity': ['sum', 'mean', 'std']
        }).round(2)
        
        daily_stats.columns = ['order_count', 'total_quantity', 'avg_quantity', 'std_quantity']
        daily_stats = daily_stats.reset_index()
        
        # Find peak and low days
        peak_day = daily_stats.loc[daily_stats['order_count'].idxmax()]
        low_day = daily_stats.loc[daily_stats['order_count'].idxmin()]
        
        # Day of week analysis
        dow_analysis = df.groupby('day_of_week').agg({
            'sku_id': 'count',
            'quantity': 'sum'
        }).round(2)
        
        dow_names = {1: 'Sunday', 2: 'Monday', 3: 'Tuesday', 4: 'Wednesday', 
                     5: 'Thursday', 6: 'Friday', 7: 'Saturday'}
        dow_analysis.index = dow_analysis.index.map(dow_names)
        
        # Weekend vs Weekday comparison
        day_type_comparison = df.groupby('day_type').agg({
            'sku_id': 'count',
            'quantity': ['sum', 'mean']
        }).round(2)
        
        return {
            "daily_statistics": daily_stats.to_dict('records'),
            "peak_day": {
                "date": str(peak_day['order_day']),
                "order_count": int(peak_day['order_count']),
                "total_quantity": float(peak_day['total_quantity'])
            },
            "lowest_day": {
                "date": str(low_day['order_day']),
                "order_count": int(low_day['order_count']),
                "total_quantity": float(low_day['total_quantity'])
            },
            "day_of_week_analysis": {str(k): v for k, v in dow_analysis.to_dict('index').items()},
            "weekend_vs_weekday": {str(k): self._flatten_dict(v) for k, v in day_type_comparison.to_dict('index').items()},
            "insights": self._generate_daily_insights(daily_stats, dow_analysis, day_type_comparison)
        }

    def _analyze_hourly_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze hourly order distribution"""
        hourly_stats = df.groupby('order_hour').agg({
            'sku_id': 'count',
            'quantity': ['sum', 'mean']
        }).round(2)
        
        hourly_stats.columns = ['order_count', 'total_quantity', 'avg_quantity']
        hourly_stats = hourly_stats.reset_index()
        
        # Find peak hours
        peak_hour = hourly_stats.loc[hourly_stats['order_count'].idxmax()]
        low_hour = hourly_stats.loc[hourly_stats['order_count'].idxmin()]
        
        # Categorize hours
        def categorize_hour(hour):
            if 6 <= hour < 12:
                return 'Morning'
            elif 12 <= hour < 17:
                return 'Afternoon'
            elif 17 <= hour < 22:
                return 'Evening'
            else:
                return 'Night'
        
        df['hour_category'] = df['order_hour'].apply(categorize_hour)
        hour_category_stats = df.groupby('hour_category').agg({
            'sku_id': 'count',
            'quantity': 'sum'
        }).round(2)
        
        return {
            "hourly_distribution": hourly_stats.to_dict('records'),
            "peak_hour": {
                "hour": int(peak_hour['order_hour']),
                "order_count": int(peak_hour['order_count']),
                "total_quantity": float(peak_hour['total_quantity'])
            },
            "lowest_hour": {
                "hour": int(low_hour['order_hour']),
                "order_count": int(low_hour['order_count']),
                "total_quantity": float(low_hour['total_quantity'])
            },
            "time_period_analysis": hour_category_stats.to_dict('index'),
            "insights": self._generate_hourly_insights(hourly_stats, hour_category_stats)
        }

    def _analyze_weekly_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze weekly trends and patterns"""
        weekly_stats = df.groupby('week_number').agg({
            'sku_id': 'count',
            'quantity': ['sum', 'mean']
        }).round(2)
        
        weekly_stats.columns = ['order_count', 'total_quantity', 'avg_quantity']
        weekly_stats = weekly_stats.reset_index()
        
        # Calculate week-over-week growth
        weekly_stats['order_growth'] = weekly_stats['order_count'].pct_change() * 100
        weekly_stats['quantity_growth'] = weekly_stats['total_quantity'].pct_change() * 100
        
        # Trend analysis
        weeks = weekly_stats['week_number'].values
        orders = weekly_stats['order_count'].values
        
        if len(weeks) > 1:
            order_trend = stats.linregress(weeks, orders)
            trend_direction = 'increasing' if order_trend.slope > 0 else 'decreasing'
        else:
            order_trend = None
            trend_direction = 'insufficient_data'
        
        return {
            "weekly_statistics": weekly_stats.fillna(0).to_dict('records'),
            "trend_analysis": {
                "direction": trend_direction,
                "slope": float(order_trend.slope) if order_trend else 0,
                "correlation": float(order_trend.rvalue) if order_trend else 0,
                "significance": float(order_trend.pvalue) if order_trend else 1
            },
            "insights": self._generate_weekly_insights(weekly_stats, trend_direction)
        }

    def _analyze_sku_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze SKU performance and categorization"""
        sku_stats = df.groupby('sku_id').agg({
            'quantity': ['sum', 'count', 'mean', 'std'],
            'order_day': ['min', 'max']
        }).round(2)
        
        sku_stats.columns = ['total_quantity', 'order_frequency', 'avg_quantity', 
                            'quantity_std', 'first_order', 'last_order']
        sku_stats = sku_stats.reset_index()
        
        # Calculate additional metrics
        sku_stats['coefficient_variation'] = (sku_stats['quantity_std'] / sku_stats['avg_quantity']).fillna(0)
        
        # ABC Analysis
        sku_stats = sku_stats.sort_values('total_quantity', ascending=False)
        sku_stats['cumulative_quantity'] = sku_stats['total_quantity'].cumsum()
        total_quantity = sku_stats['total_quantity'].sum()
        sku_stats['cumulative_percentage'] = (sku_stats['cumulative_quantity'] / total_quantity) * 100
        
        # ABC Classification
        def classify_abc(cum_pct):
            if cum_pct <= 80:
                return 'A'
            elif cum_pct <= 95:
                return 'B'
            else:
                return 'C'
        
        sku_stats['abc_category'] = sku_stats['cumulative_percentage'].apply(classify_abc)
        
        # Category analysis
        abc_analysis = sku_stats.groupby('abc_category').agg({
            'sku_id': 'count',
            'total_quantity': 'sum'
        })
        abc_analysis['percentage_of_skus'] = (abc_analysis['sku_id'] / len(sku_stats)) * 100
        abc_analysis['percentage_of_quantity'] = (abc_analysis['total_quantity'] / total_quantity) * 100
        
        # Top performers
        top_skus = sku_stats.head(10)[['sku_id', 'total_quantity', 'order_frequency', 'abc_category']].to_dict('records')
        
        return {
            "sku_statistics": {
                "total_skus": len(sku_stats),
                "active_skus": len(sku_stats),
                "avg_quantity_per_sku": float(sku_stats['total_quantity'].mean()),
                "avg_orders_per_sku": float(sku_stats['order_frequency'].mean())
            },
            "abc_analysis": abc_analysis.round(2).to_dict('index'),
            "top_performing_skus": top_skus,
            "variability_analysis": {
                "high_variability_skus": len(sku_stats[sku_stats['coefficient_variation'] > 1]),
                "stable_skus": len(sku_stats[sku_stats['coefficient_variation'] <= 0.5])
            },
            "insights": self._generate_sku_insights(sku_stats, abc_analysis)
        }

    def _analyze_seasonal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze seasonal patterns and trends"""
        monthly_stats = df.groupby('month_number').agg({
            'sku_id': 'count',
            'quantity': ['sum', 'mean']
        }).round(2)
        
        monthly_stats.columns = ['order_count', 'total_quantity', 'avg_quantity']
        monthly_stats = monthly_stats.reset_index()
        
        month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April',
                      5: 'May', 6: 'June', 7: 'July', 8: 'August',
                      9: 'September', 10: 'October', 11: 'November', 12: 'December'}
        
        monthly_stats['month_name'] = monthly_stats['month_number'].map(month_names)
        
        # Find peak and low seasons
        if not monthly_stats.empty:
            peak_month = monthly_stats.loc[monthly_stats['total_quantity'].idxmax()]
            low_month = monthly_stats.loc[monthly_stats['total_quantity'].idxmin()]
        else:
            peak_month = low_month = None
        
        return {
            "monthly_analysis": monthly_stats.to_dict('records'),
            "peak_season": {
                "month": peak_month['month_name'] if peak_month is not None else 'N/A',
                "total_quantity": float(peak_month['total_quantity']) if peak_month is not None else 0
            } if peak_month is not None else None,
            "low_season": {
                "month": low_month['month_name'] if low_month is not None else 'N/A',
                "total_quantity": float(low_month['total_quantity']) if low_month is not None else 0
            } if low_month is not None else None,
            "insights": self._generate_seasonal_insights(monthly_stats)
        }

    def _predict_order_volumes(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Simple order volume prediction"""
        daily_volumes = df.groupby('order_day')['sku_id'].count()
        
        if len(daily_volumes) < 7:
            return {"error": "Insufficient data for prediction"}
        
        # Simple moving average prediction
        recent_avg = daily_volumes.tail(7).mean()
        overall_avg = daily_volumes.mean()
        
        # Trend calculation
        days = np.arange(len(daily_volumes))
        volumes = daily_volumes.values
        
        if len(days) > 1:
            trend = stats.linregress(days, volumes)
            next_day_prediction = trend.intercept + trend.slope * len(days)
        else:
            next_day_prediction = recent_avg
        
        return {
            "recent_7_day_average": float(recent_avg),
            "overall_average": float(overall_avg),
            "predicted_next_day": max(0, float(next_day_prediction)),
            "trend_slope": float(trend.slope) if len(days) > 1 else 0,
            "confidence": "low" if len(daily_volumes) < 30 else "medium"
        }

    def _generate_daily_insights(self, daily_stats: pd.DataFrame, dow_analysis: pd.DataFrame, 
                                day_type_comparison: pd.DataFrame) -> List[str]:
        """Generate actionable insights from daily patterns"""
        insights = []
        
        # Order volume insights
        avg_orders = daily_stats['order_count'].mean()
        std_orders = daily_stats['order_count'].std()
        
        if std_orders > avg_orders * 0.3:
            insights.append("High variability in daily order volumes detected. Consider capacity planning for peak days.")
        
        # Weekend vs weekday insights
        if 'Weekend' in day_type_comparison.index and 'Weekday' in day_type_comparison.index:
            weekend_orders = day_type_comparison.loc['Weekend', ('sku_id', 'count')]
            weekday_orders = day_type_comparison.loc['Weekday', ('sku_id', 'count')]
            
            if weekend_orders > weekday_orders * 1.2:
                insights.append("Weekend orders significantly higher than weekdays. Consider weekend-specific staffing.")
            elif weekday_orders > weekend_orders * 2:
                insights.append("Weekday orders dominate. Weekend operations could be optimized or reduced.")
        
        return insights

    def _generate_hourly_insights(self, hourly_stats: pd.DataFrame, 
                                 hour_category_stats: pd.DataFrame) -> List[str]:
        """Generate insights from hourly patterns"""
        insights = []
        
        # Peak hour insights
        peak_orders = hourly_stats['order_count'].max()
        avg_orders = hourly_stats['order_count'].mean()
        
        if peak_orders > avg_orders * 2:
            peak_hour = hourly_stats.loc[hourly_stats['order_count'].idxmax(), 'order_hour']
            insights.append(f"Peak hour ({peak_hour}:00) has {peak_orders:.0f} orders, significantly above average. Consider resource allocation.")
        
        # Time period insights
        if 'Morning' in hour_category_stats.index:
            morning_orders = hour_category_stats.loc['Morning', 'sku_id']
            total_orders = hour_category_stats['sku_id'].sum()
            
            if morning_orders / total_orders > 0.4:
                insights.append("Morning hours show high order concentration. Early shift optimization recommended.")
        
        return insights

    def _generate_weekly_insights(self, weekly_stats: pd.DataFrame, trend_direction: str) -> List[str]:
        """Generate insights from weekly trends"""
        insights = []
        
        if trend_direction == 'increasing':
            insights.append("Order volumes showing upward trend. Consider scaling operations and inventory.")
        elif trend_direction == 'decreasing':
            insights.append("Order volumes declining. Review market conditions and operational efficiency.")
        
        # Growth volatility
        if 'order_growth' in weekly_stats.columns:
            growth_std = weekly_stats['order_growth'].std()
            if growth_std > 20:
                insights.append("High week-to-week volatility detected. Implement demand smoothing strategies.")
        
        return insights

    def _generate_sku_insights(self, sku_stats: pd.DataFrame, abc_analysis: pd.DataFrame) -> List[str]:
        """Generate insights from SKU performance"""
        insights = []
        
        # ABC Analysis insights
        if 'A' in abc_analysis.index:
            a_category_skus = abc_analysis.loc['A', 'sku_id']
            total_skus = abc_analysis['sku_id'].sum()
            a_percentage = (a_category_skus / total_skus) * 100
            
            insights.append(f"Category A SKUs ({a_category_skus} items, {a_percentage:.1f}%) drive 80% of volume. Focus inventory management here.")
        
        # Variability insights
        high_var_count = len(sku_stats[sku_stats['coefficient_variation'] > 1])
        if high_var_count > 0:
            insights.append(f"{high_var_count} SKUs show high demand variability. Consider safety stock adjustments.")
        
        return insights

    def _generate_seasonal_insights(self, monthly_stats: pd.DataFrame) -> List[str]:
        """Generate insights from seasonal patterns"""
        insights = []
        
        if len(monthly_stats) >= 3:
            max_month = monthly_stats['total_quantity'].max()
            min_month = monthly_stats['total_quantity'].min()
            
            if max_month > min_month * 2:
                insights.append("Significant seasonal variation detected. Implement seasonal inventory planning.")
        
        return insights