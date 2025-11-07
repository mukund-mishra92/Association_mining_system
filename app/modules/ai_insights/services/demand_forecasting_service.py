"""
Demand Forecasting Service
Advanced time series analysis and demand prediction algorithms
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import pymysql
import logging
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class DemandForecastingService:
    def __init__(self, db_config: Dict[str, Any]):
        """Initialize Demand Forecasting Service"""
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

    def comprehensive_demand_forecast(self, forecast_days: int = 30, analysis_days: int = 90, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive demand forecasts for inventory planning
        """
        try:
            # Get historical demand data
            demand_data = self._get_demand_data(analysis_days, start_date, end_date)
            
            if demand_data.empty:
                return {"error": "No demand data found for forecasting"}
            
            # Generate forecasts for top SKUs
            sku_forecasts = self._forecast_sku_demand(demand_data, forecast_days)
            
            # Overall demand trends
            overall_forecast = self._forecast_overall_demand(demand_data, forecast_days)
            
            # Seasonal patterns
            seasonal_analysis = self._analyze_seasonal_patterns(demand_data)
            
            # Forecast accuracy assessment
            accuracy_metrics = self._assess_forecast_accuracy(demand_data)
            
            # Risk analysis
            risk_analysis = self._analyze_demand_risks(demand_data, sku_forecasts)
            
            return {
                "forecast_period": {
                    "start_date": datetime.now().strftime('%Y-%m-%d'),
                    "end_date": (datetime.now() + timedelta(days=forecast_days)).strftime('%Y-%m-%d'),
                    "forecast_days": forecast_days,
                    "analysis_period_days": analysis_days
                },
                "sku_forecasts": sku_forecasts,
                "overall_forecast": overall_forecast,
                "seasonal_analysis": seasonal_analysis,
                "accuracy_metrics": accuracy_metrics,
                "risk_analysis": risk_analysis,
                "recommendations": self._generate_forecast_recommendations(sku_forecasts, risk_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error in demand forecasting: {str(e)}")
            return {"error": str(e)}

    def _get_demand_data(self, days_back: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get historical demand data for forecasting"""
        connection = self.get_connection()
        
        # Handle date range parameters
        if start_date and end_date:
            # Use custom date range
            cutoff_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_analysis_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            query = f"""
            SELECT 
                DATE(INSERTED_TIMESTAMP) as order_date,
                ARTICLE_ID as sku_id,
                SUM(QUANTITY) as daily_demand,
                COUNT(*) as order_count
            FROM {self.order_table}
            WHERE INSERTED_TIMESTAMP >= %s AND INSERTED_TIMESTAMP <= %s
            GROUP BY DATE(INSERTED_TIMESTAMP), ARTICLE_ID
            ORDER BY order_date, sku_id
            """
            df = pd.read_sql(query, connection, params=[cutoff_date, end_analysis_date])
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
                # Use data range from the latest available date backwards
                cutoff_date = latest_date - timedelta(days=days_back)
            else:
                # Fallback to current date if no data found
                cutoff_date = datetime.now() - timedelta(days=days_back)
            
            query = f"""
            SELECT 
                DATE(INSERTED_TIMESTAMP) as order_date,
                ARTICLE_ID as sku_id,
                SUM(QUANTITY) as daily_demand,
                COUNT(*) as order_count
            FROM {self.order_table}
            WHERE INSERTED_TIMESTAMP >= %s
            GROUP BY DATE(INSERTED_TIMESTAMP), ARTICLE_ID
            ORDER BY order_date, sku_id
            """
            df = pd.read_sql(query, connection, params=[cutoff_date])
        connection.close()
        
        if not df.empty:
            df['order_date'] = pd.to_datetime(df['order_date'])
            # Add day of week and month for seasonal analysis
            df['day_of_week'] = df['order_date'].dt.dayofweek
            df['month'] = df['order_date'].dt.month
            df['week'] = df['order_date'].dt.isocalendar().week
        
        return df

    def _forecast_sku_demand(self, df: pd.DataFrame, forecast_days: int) -> List[Dict[str, Any]]:
        """Generate demand forecasts for individual SKUs"""
        sku_forecasts = []
        
        # Get top SKUs by total demand
        top_skus = df.groupby('sku_id')['daily_demand'].sum().nlargest(20).index
        
        for sku in top_skus:
            sku_data = df[df['sku_id'] == sku].copy()
            
            if len(sku_data) < 7:  # Need at least 7 data points
                continue
            
            # Create complete date range
            date_range = pd.date_range(
                start=sku_data['order_date'].min(),
                end=sku_data['order_date'].max(),
                freq='D'
            )
            
            # Fill missing dates with zero demand
            sku_ts = sku_data.set_index('order_date').reindex(date_range, fill_value=0)
            sku_ts.index.name = 'date'
            
            # Apply forecasting methods
            forecasts = {}
            
            # 1. Moving Average
            forecasts['moving_average'] = self._moving_average_forecast(sku_ts['daily_demand'], forecast_days)
            
            # 2. Linear Trend
            forecasts['linear_trend'] = self._linear_trend_forecast(sku_ts['daily_demand'], forecast_days)
            
            # 3. Exponential Smoothing
            forecasts['exponential_smoothing'] = self._exponential_smoothing_forecast(sku_ts['daily_demand'], forecast_days)
            
            # 4. Seasonal Naive (if enough data)
            if len(sku_ts) >= 14:  # At least 2 weeks
                forecasts['seasonal_naive'] = self._seasonal_naive_forecast(sku_ts['daily_demand'], forecast_days, 7)
            
            # Ensemble forecast (average of methods)
            valid_forecasts = [f for f in forecasts.values() if f is not None]
            if valid_forecasts:
                ensemble_forecast = np.mean(valid_forecasts, axis=0)
            else:
                ensemble_forecast = np.zeros(forecast_days)
            
            # Calculate forecast statistics
            historical_stats = {
                'mean': float(sku_ts['daily_demand'].mean()),
                'std': float(sku_ts['daily_demand'].std()),
                'max': float(sku_ts['daily_demand'].max()),
                'trend': self._calculate_trend(sku_ts['daily_demand'])
            }
            
            # Forecast confidence intervals
            forecast_std = sku_ts['daily_demand'].std()
            confidence_intervals = self._calculate_confidence_intervals(ensemble_forecast, forecast_std)
            
            sku_forecasts.append({
                'sku_id': sku,
                'historical_stats': historical_stats,
                'forecast_methods': {k: v.tolist() if v is not None else None for k, v in forecasts.items()},
                'ensemble_forecast': ensemble_forecast.tolist(),
                'confidence_intervals': confidence_intervals,
                'forecast_total': float(ensemble_forecast.sum()),
                'average_daily_forecast': float(ensemble_forecast.mean()),
                'forecast_trend': self._calculate_trend(ensemble_forecast),
                'risk_level': self._assess_sku_risk(sku_ts['daily_demand'], ensemble_forecast)
            })
        
        return sku_forecasts

    def _forecast_overall_demand(self, df: pd.DataFrame, forecast_days: int) -> Dict[str, Any]:
        """Generate overall demand forecast across all SKUs"""
        # Aggregate daily demand across all SKUs
        daily_totals = df.groupby('order_date')['daily_demand'].sum().reset_index()
        daily_totals = daily_totals.sort_values('order_date')
        
        if len(daily_totals) < 7:
            return {"error": "Insufficient data for overall forecasting"}
        
        demand_series = daily_totals['daily_demand'].values
        
        # Apply multiple forecasting methods
        ma_forecast = self._moving_average_forecast(demand_series, forecast_days)
        trend_forecast = self._linear_trend_forecast(demand_series, forecast_days)
        exp_forecast = self._exponential_smoothing_forecast(demand_series, forecast_days)
        
        # Ensemble forecast
        ensemble = np.mean([ma_forecast, trend_forecast, exp_forecast], axis=0)
        
        # Generate forecast dates
        forecast_dates = pd.date_range(
            start=datetime.now() + timedelta(days=1),
            periods=forecast_days,
            freq='D'
        )
        
        # Calculate statistics
        historical_mean = float(demand_series.mean())
        historical_std = float(demand_series.std())
        
        return {
            'forecast_dates': [d.strftime('%Y-%m-%d') for d in forecast_dates],
            'forecast_values': ensemble.tolist(),
            'historical_average': historical_mean,
            'forecast_average': float(ensemble.mean()),
            'total_forecast_demand': float(ensemble.sum()),
            'growth_rate': ((ensemble.mean() - historical_mean) / historical_mean * 100) if historical_mean > 0 else 0,
            'confidence_level': self._calculate_overall_confidence(demand_series, ensemble)
        }

    def _analyze_seasonal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze seasonal patterns in demand"""
        if df.empty:
            return {"error": "No data for seasonal analysis"}
        
        # Day of week patterns
        dow_patterns = df.groupby('day_of_week')['daily_demand'].mean()
        dow_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow_analysis = {dow_names[i]: float(dow_patterns.get(i, 0)) for i in range(7)}
        
        # Monthly patterns (if data spans multiple months)
        monthly_patterns = df.groupby('month')['daily_demand'].mean()
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_analysis = {month_names[i-1]: float(monthly_patterns.get(i, 0)) for i in range(1, 13)}
        
        # Weekly patterns
        weekly_patterns = df.groupby('week')['daily_demand'].mean()
        
        # Identify strongest seasonal pattern
        dow_coefficient_variation = dow_patterns.std() / dow_patterns.mean() if dow_patterns.mean() > 0 else 0
        monthly_coefficient_variation = monthly_patterns.std() / monthly_patterns.mean() if monthly_patterns.mean() > 0 else 0
        
        strongest_pattern = 'weekly' if dow_coefficient_variation > monthly_coefficient_variation else 'monthly'
        
        return {
            'day_of_week_patterns': dow_analysis,
            'monthly_patterns': monthly_analysis,
            'strongest_seasonal_pattern': strongest_pattern,
            'seasonality_strength': {
                'weekly': float(dow_coefficient_variation),
                'monthly': float(monthly_coefficient_variation)
            },
            'seasonal_insights': self._generate_seasonal_insights(dow_analysis, monthly_analysis)
        }

    def _assess_forecast_accuracy(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess forecast accuracy using backtesting"""
        if len(df) < 14:  # Need at least 2 weeks of data
            return {"error": "Insufficient data for accuracy assessment"}
        
        # Split data for backtesting (80% train, 20% test)
        split_point = int(len(df) * 0.8)
        
        accuracy_results = {}
        
        # Test accuracy for top SKUs
        top_skus = df.groupby('sku_id')['daily_demand'].sum().nlargest(5).index
        
        for sku in top_skus:
            sku_data = df[df['sku_id'] == sku]['daily_demand'].values
            
            if len(sku_data) < 14:
                continue
            
            train_data = sku_data[:split_point]
            test_data = sku_data[split_point:]
            
            # Generate forecasts using training data
            forecast_length = len(test_data)
            
            ma_forecast = self._moving_average_forecast(train_data, forecast_length)
            trend_forecast = self._linear_trend_forecast(train_data, forecast_length)
            
            # Calculate accuracy metrics
            if len(test_data) == len(ma_forecast):
                ma_mae = mean_absolute_error(test_data, ma_forecast)
                ma_mse = mean_squared_error(test_data, ma_forecast)
                
                trend_mae = mean_absolute_error(test_data, trend_forecast)
                trend_mse = mean_squared_error(test_data, trend_forecast)
                
                accuracy_results[sku] = {
                    'moving_average': {'mae': float(ma_mae), 'rmse': float(np.sqrt(ma_mse))},
                    'linear_trend': {'mae': float(trend_mae), 'rmse': float(np.sqrt(trend_mse))}
                }
        
        # Overall accuracy summary
        if accuracy_results:
            avg_mae = np.mean([v['moving_average']['mae'] for v in accuracy_results.values()])
            avg_rmse = np.mean([v['moving_average']['rmse'] for v in accuracy_results.values()])
            
            accuracy_grade = 'High' if avg_mae < 5 else 'Medium' if avg_mae < 15 else 'Low'
        else:
            avg_mae = avg_rmse = 0
            accuracy_grade = 'Unknown'
        
        return {
            'sku_accuracy_details': accuracy_results,
            'overall_accuracy': {
                'average_mae': float(avg_mae),
                'average_rmse': float(avg_rmse),
                'accuracy_grade': accuracy_grade
            },
            'recommendations': self._generate_accuracy_recommendations(accuracy_grade, avg_mae)
        }

    def _analyze_demand_risks(self, df: pd.DataFrame, sku_forecasts: List[Dict]) -> Dict[str, Any]:
        """Analyze demand forecasting risks and uncertainties"""
        risks = []
        
        # Risk 1: High variability SKUs
        high_variability_skus = []
        for forecast in sku_forecasts:
            if forecast['historical_stats']['std'] > forecast['historical_stats']['mean']:
                high_variability_skus.append({
                    'sku_id': forecast['sku_id'],
                    'coefficient_of_variation': forecast['historical_stats']['std'] / forecast['historical_stats']['mean']
                })
        
        if high_variability_skus:
            risks.append({
                'type': 'High Demand Variability',
                'severity': 'High' if len(high_variability_skus) > 5 else 'Medium',
                'affected_skus': len(high_variability_skus),
                'description': f'{len(high_variability_skus)} SKUs show high demand variability',
                'mitigation': 'Increase safety stock and review forecasting frequency'
            })
        
        # Risk 2: Trending SKUs (potential demand shift)
        trending_skus = []
        for forecast in sku_forecasts:
            if abs(forecast['historical_stats']['trend']) > 0.1:  # Significant trend
                trending_skus.append({
                    'sku_id': forecast['sku_id'],
                    'trend': forecast['historical_stats']['trend']
                })
        
        if trending_skus:
            risks.append({
                'type': 'Demand Trend Changes',
                'severity': 'Medium',
                'affected_skus': len(trending_skus),
                'description': f'{len(trending_skus)} SKUs show significant demand trends',
                'mitigation': 'Monitor closely and adjust forecasts more frequently'
            })
        
        # Risk 3: Low historical data
        low_data_count = sum(1 for f in sku_forecasts if len(f['ensemble_forecast']) < 30)
        if low_data_count > 0:
            risks.append({
                'type': 'Insufficient Historical Data',
                'severity': 'Medium',
                'affected_skus': low_data_count,
                'description': f'{low_data_count} SKUs have limited historical data',
                'mitigation': 'Use conservative forecasts and gather more data'
            })
        
        # Overall risk assessment
        total_risks = len(risks)
        overall_risk = 'High' if total_risks > 2 else 'Medium' if total_risks > 0 else 'Low'
        
        return {
            'identified_risks': risks,
            'overall_risk_level': overall_risk,
            'risk_summary': {
                'total_risk_factors': total_risks,
                'high_severity_risks': len([r for r in risks if r['severity'] == 'High']),
                'affected_sku_percentage': (sum(r['affected_skus'] for r in risks) / len(sku_forecasts) * 100) if sku_forecasts else 0
            }
        }

    # Forecasting method implementations
    def _moving_average_forecast(self, series: np.ndarray, periods: int, window: int = 7) -> np.ndarray:
        """Simple moving average forecast"""
        if len(series) < window:
            return np.full(periods, series.mean()) if len(series) > 0 else np.zeros(periods)
        
        last_values = series[-window:]
        forecast_value = last_values.mean()
        return np.full(periods, forecast_value)

    def _linear_trend_forecast(self, series: np.ndarray, periods: int) -> np.ndarray:
        """Linear trend forecast"""
        if len(series) < 2:
            return np.full(periods, series.mean()) if len(series) > 0 else np.zeros(periods)
        
        x = np.arange(len(series))
        y = series
        
        # Fit linear regression
        slope, intercept = np.polyfit(x, y, 1)
        
        # Generate forecast
        future_x = np.arange(len(series), len(series) + periods)
        forecast = slope * future_x + intercept
        
        # Ensure non-negative forecasts
        return np.maximum(forecast, 0)

    def _exponential_smoothing_forecast(self, series: np.ndarray, periods: int, alpha: float = 0.3) -> np.ndarray:
        """Exponential smoothing forecast"""
        if len(series) == 0:
            return np.zeros(periods)
        
        # Initialize with first value
        smoothed = [series[0]]
        
        # Apply exponential smoothing
        for i in range(1, len(series)):
            smoothed.append(alpha * series[i] + (1 - alpha) * smoothed[-1])
        
        # Forecast is the last smoothed value
        forecast_value = smoothed[-1]
        return np.full(periods, max(forecast_value, 0))

    def _seasonal_naive_forecast(self, series: np.ndarray, periods: int, season_length: int) -> np.ndarray:
        """Seasonal naive forecast"""
        if len(series) < season_length:
            return self._moving_average_forecast(series, periods)
        
        # Use last season as forecast
        last_season = series[-season_length:]
        
        # Repeat seasonal pattern
        forecast = []
        for i in range(periods):
            forecast.append(last_season[i % season_length])
        
        return np.array(forecast)

    def _calculate_trend(self, series: np.ndarray) -> float:
        """Calculate trend direction and strength"""
        if len(series) < 2:
            return 0.0
        
        x = np.arange(len(series))
        slope, _ = np.polyfit(x, series, 1)
        return float(slope)

    def _calculate_confidence_intervals(self, forecast: np.ndarray, std: float, confidence: float = 0.95) -> Dict[str, List[float]]:
        """Calculate confidence intervals for forecasts"""
        z_score = 1.96  # 95% confidence interval
        margin = z_score * std
        
        return {
            'lower_bound': (forecast - margin).tolist(),
            'upper_bound': (forecast + margin).tolist()
        }

    def _assess_sku_risk(self, historical: np.ndarray, forecast: np.ndarray) -> str:
        """Assess risk level for SKU forecast"""
        if len(historical) == 0:
            return 'High'
        
        historical_cv = historical.std() / historical.mean() if historical.mean() > 0 else float('inf')
        
        if historical_cv > 1.5:
            return 'High'
        elif historical_cv > 0.8:
            return 'Medium'
        else:
            return 'Low'

    def _calculate_overall_confidence(self, historical: np.ndarray, forecast: np.ndarray) -> str:
        """Calculate overall confidence in forecast"""
        if len(historical) < 14:
            return 'Low'
        elif len(historical) < 30:
            return 'Medium'
        else:
            return 'High'

    def _generate_seasonal_insights(self, dow_patterns: Dict, monthly_patterns: Dict) -> List[str]:
        """Generate insights from seasonal analysis"""
        insights = []
        
        # Day of week insights
        dow_values = list(dow_patterns.values())
        if max(dow_values) > min(dow_values) * 1.5:
            peak_day = max(dow_patterns, key=dow_patterns.get)
            insights.append(f"Strong weekly pattern detected. {peak_day} shows highest demand.")
        
        # Monthly insights
        monthly_values = [v for v in monthly_patterns.values() if v > 0]
        if len(monthly_values) > 1 and max(monthly_values) > min(monthly_values) * 1.3:
            peak_month = max(monthly_patterns, key=monthly_patterns.get)
            insights.append(f"Seasonal variation detected. {peak_month} shows peak demand.")
        
        return insights

    def _generate_accuracy_recommendations(self, accuracy_grade: str, mae: float) -> List[str]:
        """Generate recommendations based on forecast accuracy"""
        recommendations = []
        
        if accuracy_grade == 'Low':
            recommendations.append("Forecast accuracy is low. Consider collecting more data or using external factors.")
            recommendations.append("Implement safety stock buffers to handle forecast errors.")
        elif accuracy_grade == 'Medium':
            recommendations.append("Moderate forecast accuracy. Review and refine forecasting parameters regularly.")
        else:
            recommendations.append("Good forecast accuracy. Continue monitoring and fine-tuning methods.")
        
        return recommendations

    def _generate_forecast_recommendations(self, sku_forecasts: List[Dict], risk_analysis: Dict) -> List[str]:
        """Generate actionable recommendations from forecast analysis"""
        recommendations = []
        
        # High-risk SKUs
        high_risk_count = len([f for f in sku_forecasts if f['risk_level'] == 'High'])
        if high_risk_count > 0:
            recommendations.append(f"Monitor {high_risk_count} high-risk SKUs closely and consider increasing safety stock.")
        
        # Trending SKUs
        upward_trend_count = len([f for f in sku_forecasts if f['forecast_trend'] > 0.1])
        if upward_trend_count > 0:
            recommendations.append(f"{upward_trend_count} SKUs show upward demand trends. Consider capacity planning.")
        
        # Overall risk level
        if risk_analysis['overall_risk_level'] == 'High':
            recommendations.append("High overall forecasting risk detected. Implement robust contingency planning.")
        
        # General recommendations
        recommendations.extend([
            "Update forecasts weekly for high-volume SKUs",
            "Implement automated alerts for significant demand deviations",
            "Consider external factors (seasonality, promotions, market trends) in planning"
        ])
        
        return recommendations