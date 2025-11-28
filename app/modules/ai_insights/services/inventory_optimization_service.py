"""
Inventory Optimization Service
Advanced algorithms for inventory management and optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pymysql
import logging
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

class InventoryOptimizationService:
    def __init__(self, db_config: Dict[str, Any]):
        """Initialize Inventory Optimization Service"""
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

    def comprehensive_inventory_analysis(self, days_back: int = 90, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """
        Comprehensive inventory optimization analysis
        """
        try:
            # Get inventory and order data
            inventory_data = self._get_inventory_data(days_back, start_date, end_date)
            
            if inventory_data.empty:
                return {"error": "No inventory data found for analysis"}
            
            # Perform various analyses with error handling
            abc_analysis = {}
            try:
                abc_analysis = self._perform_abc_analysis(inventory_data)
            except Exception as e:
                self.logger.error(f"ABC analysis failed: {str(e)}")
                abc_analysis = {"error": "ABC analysis failed"}
            
            xyz_analysis = {}
            try:
                xyz_analysis = self._perform_xyz_analysis(inventory_data)
            except Exception as e:
                self.logger.error(f"XYZ analysis failed: {str(e)}")
                xyz_analysis = {"error": "XYZ analysis failed"}
            
            safety_stock = {}
            try:
                safety_stock = self._calculate_safety_stock(inventory_data)
            except Exception as e:
                self.logger.error(f"Safety stock calculation failed: {str(e)}")
                safety_stock = {"error": "Safety stock calculation failed"}
            
            reorder_points = {}
            try:
                reorder_points = self._calculate_reorder_points(inventory_data)
            except Exception as e:
                self.logger.error(f"Reorder points calculation failed: {str(e)}")
                reorder_points = {"error": "Reorder points calculation failed"}
            
            turnover_analysis = {}
            try:
                turnover_analysis = self._analyze_inventory_turnover(inventory_data)
            except Exception as e:
                self.logger.error(f"Turnover analysis failed: {str(e)}")
                turnover_analysis = {"error": "Turnover analysis failed"}
            
            slow_moving = {}
            try:
                slow_moving = self._identify_slow_moving_items(inventory_data)
            except Exception as e:
                self.logger.error(f"Slow moving analysis failed: {str(e)}")
                slow_moving = {"error": "Slow moving analysis failed"}
            
            optimization_opportunities = {}
            try:
                optimization_opportunities = self._identify_optimization_opportunities(inventory_data)
            except Exception as e:
                self.logger.error(f"Optimization opportunities analysis failed: {str(e)}")
                optimization_opportunities = {"error": "Optimization opportunities analysis failed"}
            
            return {
                "analysis_summary": {
                    "total_skus_analyzed": len(inventory_data),
                    "analysis_period_days": days_back,
                    "total_order_volume": float(inventory_data['total_quantity'].sum()),
                    "average_daily_demand": float(inventory_data['daily_avg_demand'].mean())
                },
                "abc_analysis": abc_analysis,
                "xyz_analysis": xyz_analysis,
                "safety_stock_recommendations": safety_stock,
                "reorder_point_recommendations": reorder_points,
                "turnover_analysis": turnover_analysis,
                "slow_moving_analysis": slow_moving,
                "optimization_opportunities": optimization_opportunities
            }
            
        except Exception as e:
            self.logger.error(f"Error in inventory analysis: {str(e)}")
            return {"error": str(e)}

    def _get_inventory_data(self, days_back: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get comprehensive inventory and demand data"""
        connection = self.get_connection()
        
        # Handle date range parameters
        if start_date and end_date:
            # Use custom date range
            cutoff_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_analysis_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            query = f"""
            SELECT 
                o.ARTICLE_ID as sku_id,
                COUNT(DISTINCT DATE(o.INSERTED_TIMESTAMP)) as active_days,
                SUM(o.QUANTITY) as total_quantity,
                AVG(o.QUANTITY) as avg_order_quantity,
                STDDEV(o.QUANTITY) as std_order_quantity,
                COUNT(*) as order_frequency,
                MIN(o.INSERTED_TIMESTAMP) as first_order_date,
                MAX(o.INSERTED_TIMESTAMP) as last_order_date,
                DATEDIFF(MAX(o.INSERTED_TIMESTAMP), MIN(o.INSERTED_TIMESTAMP)) + 1 as order_span_days,
                100.0 as current_stock,
                10.0 as unit_cost,
                'General' as category,
                'Default' as supplier_id
            FROM {self.order_table} o
            WHERE o.INSERTED_TIMESTAMP >= %s AND o.INSERTED_TIMESTAMP <= %s
            GROUP BY o.ARTICLE_ID
            HAVING COUNT(*) >= 2
            ORDER BY total_quantity DESC
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
                o.ARTICLE_ID as sku_id,
                COUNT(DISTINCT DATE(o.INSERTED_TIMESTAMP)) as active_days,
                SUM(o.QUANTITY) as total_quantity,
                AVG(o.QUANTITY) as avg_order_quantity,
                STDDEV(o.QUANTITY) as std_order_quantity,
                COUNT(*) as order_frequency,
                MIN(o.INSERTED_TIMESTAMP) as first_order_date,
                MAX(o.INSERTED_TIMESTAMP) as last_order_date,
                DATEDIFF(MAX(o.INSERTED_TIMESTAMP), MIN(o.INSERTED_TIMESTAMP)) + 1 as order_span_days,
                100.0 as current_stock,
                10.0 as unit_cost,
                'General' as category,
                'Default' as supplier_id
            FROM {self.order_table} o
            WHERE o.INSERTED_TIMESTAMP >= %s
            GROUP BY o.ARTICLE_ID
            HAVING COUNT(*) >= 2
            ORDER BY total_quantity DESC
            """
            df = pd.read_sql(query, connection, params=[cutoff_date])
        connection.close()
        
        if not df.empty:
            # Calculate additional metrics
            df['daily_avg_demand'] = df['total_quantity'] / df['active_days']
            df['demand_variability'] = df['std_order_quantity'] / df['avg_order_quantity']
            df['demand_variability'] = df['demand_variability'].fillna(0)
            df['current_stock'] = df['current_stock'].fillna(0)
            df['unit_cost'] = df['unit_cost'].fillna(0)
            
            # Calculate days of supply
            df['days_of_supply'] = np.where(
                df['daily_avg_demand'] > 0,
                df['current_stock'] / df['daily_avg_demand'],
                0
            )
        
        return df

    def _perform_abc_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform ABC analysis based on order value/volume"""
        # Sort by total quantity (or value if cost is available)
        df_sorted = df.copy()
        
        # Use value if unit cost is available, otherwise use quantity
        if 'unit_cost' in df.columns and df['unit_cost'].sum() > 0:
            df_sorted['analysis_value'] = df_sorted['total_quantity'] * df_sorted['unit_cost']
            analysis_metric = 'value'
        else:
            df_sorted['analysis_value'] = df_sorted['total_quantity']
            analysis_metric = 'quantity'
        
        df_sorted = df_sorted.sort_values('analysis_value', ascending=False)
        
        # Calculate cumulative percentages
        df_sorted['cumulative_value'] = df_sorted['analysis_value'].cumsum()
        total_value = df_sorted['analysis_value'].sum()
        df_sorted['cumulative_percentage'] = (df_sorted['cumulative_value'] / total_value) * 100
        
        # ABC Classification
        def classify_abc(cum_pct):
            if cum_pct <= 80:
                return 'A'
            elif cum_pct <= 95:
                return 'B'
            else:
                return 'C'
        
        df_sorted['abc_category'] = df_sorted['cumulative_percentage'].apply(classify_abc)
        
        # Category statistics
        abc_stats = df_sorted.groupby('abc_category').agg({
            'sku_id': 'count',
            'analysis_value': 'sum',
            'daily_avg_demand': 'mean',
            'current_stock': 'sum'
        })
        
        abc_stats['percentage_of_items'] = (abc_stats['sku_id'] / len(df_sorted)) * 100
        abc_stats['percentage_of_value'] = (abc_stats['analysis_value'] / total_value) * 100
        
        # Top items in each category
        top_items = {}
        for category in ['A', 'B', 'C']:
            category_items = df_sorted[df_sorted['abc_category'] == category].head(5)
            top_items[category] = category_items[['sku_id', 'analysis_value', 'daily_avg_demand']].to_dict('records')
        
        return {
            "analysis_metric": analysis_metric,
            "category_statistics": abc_stats.round(2).to_dict('index'),
            "top_items_by_category": top_items,
            "recommendations": self._generate_abc_recommendations(abc_stats)
        }

    def _perform_xyz_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform XYZ analysis based on demand variability"""
        # Calculate coefficient of variation for demand variability
        df_xyz = df.copy()
        
        # XYZ Classification based on demand variability
        def classify_xyz(variability):
            if pd.isna(variability) or variability <= 0.5:
                return 'X'  # Low variability
            elif variability <= 1.0:
                return 'Y'  # Medium variability
            else:
                return 'Z'  # High variability
        
        df_xyz['xyz_category'] = df_xyz['demand_variability'].apply(classify_xyz)
        
        # Category statistics
        xyz_stats = df_xyz.groupby('xyz_category').agg({
            'sku_id': 'count',
            'demand_variability': 'mean',
            'daily_avg_demand': 'mean',
            'current_stock': 'sum'
        })
        
        xyz_stats['percentage_of_items'] = (xyz_stats['sku_id'] / len(df_xyz)) * 100
        
        # Combined ABC-XYZ analysis (only if abc_category exists)
        combined_analysis = {}
        if 'abc_category' in df_xyz.columns:
            try:
                combined_analysis = df_xyz.groupby(['abc_category', 'xyz_category']).agg({
                    'sku_id': 'count'
                }).unstack(fill_value=0)
            except Exception:
                # If groupby fails, continue without combined analysis
                combined_analysis = {}
        
        return {
            "xyz_statistics": xyz_stats.round(2).to_dict('index'),
            "combined_abc_xyz": combined_analysis.to_dict('index'),
            "recommendations": self._generate_xyz_recommendations(xyz_stats, combined_analysis)
        }

    def _calculate_safety_stock(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate safety stock recommendations"""
        safety_stock_recommendations = []
        
        for _, item in df.iterrows():
            # Basic safety stock calculation using standard deviation
            daily_demand = item['daily_avg_demand']
            demand_std = item.get('std_order_quantity', 0) or 0
            
            # Service level factors (95% service level ≈ 1.65)
            service_level_factor = 1.65
            
            # Lead time assumption (configurable)
            lead_time_days = 7  # Default 1 week
            
            # Safety stock = Z-score * √(Lead Time) * Demand Std Dev
            safety_stock = service_level_factor * np.sqrt(lead_time_days) * demand_std
            
            # Minimum safety stock (1 day of demand)
            min_safety_stock = daily_demand * 1
            safety_stock = max(safety_stock, min_safety_stock)
            
            current_stock = item.get('current_stock', 0) or 0
            recommended_safety_stock = max(0, safety_stock)
            
            safety_stock_recommendations.append({
                'sku_id': item['sku_id'],
                'current_stock': float(current_stock),
                'daily_avg_demand': float(daily_demand),
                'demand_std': float(demand_std),
                'recommended_safety_stock': float(recommended_safety_stock),
                'current_days_of_supply': float(item.get('days_of_supply', 0)),
                'safety_stock_status': 'adequate' if current_stock >= recommended_safety_stock else 'insufficient'
            })
        
        # Summary statistics
        total_items = len(safety_stock_recommendations)
        insufficient_items = len([x for x in safety_stock_recommendations if x['safety_stock_status'] == 'insufficient'])
        
        return {
            "recommendations": safety_stock_recommendations[:50],  # Top 50 for display
            "summary": {
                "total_items_analyzed": total_items,
                "items_with_insufficient_safety_stock": insufficient_items,
                "percentage_insufficient": (insufficient_items / total_items * 100) if total_items > 0 else 0
            }
        }

    def _calculate_reorder_points(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate reorder point recommendations"""
        reorder_recommendations = []
        
        for _, item in df.iterrows():
            daily_demand = item['daily_avg_demand']
            current_stock = item.get('current_stock', 0) or 0
            
            # Lead time assumption
            lead_time_days = 7
            
            # Reorder point = (Daily Demand * Lead Time) + Safety Stock
            lead_time_demand = daily_demand * lead_time_days
            
            # Simple safety stock (50% of lead time demand)
            safety_stock = lead_time_demand * 0.5
            
            reorder_point = lead_time_demand + safety_stock
            
            # Economic Order Quantity (simple approximation)
            # EOQ = √(2 * Annual Demand * Order Cost / Holding Cost)
            annual_demand = daily_demand * 365
            order_cost = 100  # Assumed order cost
            holding_cost_rate = 0.2  # 20% of item value
            item_cost = item.get('unit_cost', 10) or 10  # Default cost
            holding_cost = item_cost * holding_cost_rate
            
            if holding_cost > 0:
                eoq = np.sqrt((2 * annual_demand * order_cost) / holding_cost)
            else:
                eoq = daily_demand * 30  # Default to 30 days supply
            
            reorder_recommendations.append({
                'sku_id': item['sku_id'],
                'current_stock': float(current_stock),
                'daily_avg_demand': float(daily_demand),
                'recommended_reorder_point': float(reorder_point),
                'recommended_order_quantity': float(eoq),
                'lead_time_days': lead_time_days,
                'reorder_status': 'reorder_now' if current_stock <= reorder_point else 'sufficient',
                'days_until_reorder': max(0, (current_stock - reorder_point) / daily_demand) if daily_demand > 0 else 999
            })
        
        # Sort by urgency (items that need reordering first)
        reorder_recommendations.sort(key=lambda x: x['days_until_reorder'])
        
        # Summary
        urgent_reorders = len([x for x in reorder_recommendations if x['reorder_status'] == 'reorder_now'])
        
        return {
            "recommendations": reorder_recommendations[:50],  # Top 50 most urgent
            "summary": {
                "total_items": len(reorder_recommendations),
                "items_needing_reorder": urgent_reorders,
                "percentage_needing_reorder": (urgent_reorders / len(reorder_recommendations) * 100) if reorder_recommendations else 0
            }
        }

    def _analyze_inventory_turnover(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze inventory turnover rates"""
        turnover_analysis = []
        
        for _, item in df.iterrows():
            current_stock = item.get('current_stock', 0) or 0
            total_demand = item['total_quantity']
            analysis_days = item['active_days']
            
            # Calculate turnover rate
            if current_stock > 0 and analysis_days > 0:
                # Annualized turnover
                daily_demand = total_demand / analysis_days
                annual_demand = daily_demand * 365
                turnover_rate = annual_demand / current_stock
            else:
                turnover_rate = 0
            
            # Classify turnover
            if turnover_rate >= 12:
                turnover_category = 'Fast Moving'
            elif turnover_rate >= 4:
                turnover_category = 'Medium Moving'
            elif turnover_rate >= 1:
                turnover_category = 'Slow Moving'
            else:
                turnover_category = 'Very Slow Moving'
            
            turnover_analysis.append({
                'sku_id': item['sku_id'],
                'current_stock': float(current_stock),
                'annual_demand_estimate': float(daily_demand * 365) if analysis_days > 0 else 0,
                'turnover_rate': float(turnover_rate),
                'turnover_category': turnover_category,
                'days_of_supply': float(item.get('days_of_supply', 0))
            })
        
        # Category statistics
        turnover_df = pd.DataFrame(turnover_analysis)
        category_stats = turnover_df.groupby('turnover_category').agg({
            'sku_id': 'count',
            'turnover_rate': 'mean',
            'current_stock': 'sum'
        })
        
        return {
            "turnover_analysis": turnover_analysis[:50],  # Top 50
            "category_statistics": category_stats.round(2).to_dict('index'),
            "recommendations": self._generate_turnover_recommendations(category_stats)
        }

    def _identify_slow_moving_items(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify slow-moving and obsolete inventory"""
        slow_moving = []
        
        for _, item in df.iterrows():
            days_of_supply = item.get('days_of_supply', 0)
            last_order_date = pd.to_datetime(item.get('last_order_date', datetime.now()))
            days_since_last_order = (datetime.now() - last_order_date).days
            
            # Slow moving criteria
            is_slow_moving = (
                days_of_supply > 90 or  # More than 3 months supply
                days_since_last_order > 60  # No orders in 2 months
            )
            
            if is_slow_moving:
                current_stock = item.get('current_stock', 0) or 0
                unit_cost = item.get('unit_cost', 0) or 0
                tied_up_value = current_stock * unit_cost
                
                slow_moving.append({
                    'sku_id': item['sku_id'],
                    'current_stock': float(current_stock),
                    'days_of_supply': float(days_of_supply),
                    'days_since_last_order': days_since_last_order,
                    'tied_up_value': float(tied_up_value),
                    'recommendation': self._get_slow_moving_recommendation(days_of_supply, days_since_last_order)
                })
        
        # Sort by value tied up
        slow_moving.sort(key=lambda x: x['tied_up_value'], reverse=True)
        
        total_tied_up_value = sum(item['tied_up_value'] for item in slow_moving)
        
        return {
            "slow_moving_items": slow_moving[:30],  # Top 30 by value
            "summary": {
                "total_slow_moving_items": len(slow_moving),
                "total_tied_up_value": float(total_tied_up_value),
                "average_days_of_supply": np.mean([item['days_of_supply'] for item in slow_moving]) if slow_moving else 0
            },
            "recommendations": [
                "Consider promotional activities for slow-moving items",
                "Review supplier agreements for high-value slow movers",
                "Implement automated reorder point adjustments",
                "Consider liquidation for items with >180 days supply"
            ]
        }

    def _identify_optimization_opportunities(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify key optimization opportunities"""
        opportunities = []
        
        # Opportunity 1: Overstocked items
        overstocked = df[df['days_of_supply'] > 60]
        if not overstocked.empty:
            overstocked_value = (overstocked['current_stock'] * overstocked['unit_cost']).sum()
            opportunities.append({
                'type': 'Overstocked Items',
                'count': len(overstocked),
                'potential_savings': float(overstocked_value * 0.2),  # 20% carrying cost savings
                'description': f'{len(overstocked)} items with >60 days supply'
            })
        
        # Opportunity 2: Understocked high-demand items
        understocked = df[(df['days_of_supply'] < 7) & (df['daily_avg_demand'] > df['daily_avg_demand'].median())]
        if not understocked.empty:
            lost_sales_risk = (understocked['daily_avg_demand'] * understocked['unit_cost'] * 7).sum()
            opportunities.append({
                'type': 'Understocked High-Demand Items',
                'count': len(understocked),
                'potential_savings': float(lost_sales_risk),
                'description': f'{len(understocked)} high-demand items with <7 days supply'
            })
        
        # Opportunity 3: High variability items needing safety stock
        high_variability = df[df['demand_variability'] > 1.5]
        if not high_variability.empty:
            safety_stock_investment = (high_variability['daily_avg_demand'] * high_variability['unit_cost'] * 14).sum()
            opportunities.append({
                'type': 'Safety Stock Optimization',
                'count': len(high_variability),
                'potential_savings': float(safety_stock_investment * 0.1),  # 10% service level improvement value
                'description': f'{len(high_variability)} items with high demand variability'
            })
        
        total_potential_savings = sum(opp['potential_savings'] for opp in opportunities)
        
        return {
            'opportunities': opportunities,
            'total_potential_savings': float(total_potential_savings),
            'priority_actions': [
                'Focus on Category A items for maximum impact',
                'Implement automated reorder points for high-variability items',
                'Review and adjust safety stock levels quarterly',
                'Set up alerts for items approaching stockout'
            ]
        }

    def _get_slow_moving_recommendation(self, days_of_supply: float, days_since_last_order: int) -> str:
        """Get recommendation for slow-moving items"""
        if days_since_last_order > 120:
            return 'Consider liquidation or write-off'
        elif days_of_supply > 180:
            return 'Aggressive promotion or discount'
        elif days_of_supply > 90:
            return 'Reduce reorder quantity or frequency'
        else:
            return 'Monitor closely'

    def _generate_abc_recommendations(self, abc_stats: pd.DataFrame) -> List[str]:
        """Generate ABC analysis recommendations"""
        recommendations = []
        
        if 'A' in abc_stats.index:
            a_items = abc_stats.loc['A', 'sku_id']
            recommendations.append(f"Focus on {a_items} Category A items - implement tight inventory control")
            recommendations.append("Consider daily/weekly monitoring for Category A items")
        
        if 'C' in abc_stats.index:
            c_items = abc_stats.loc['C', 'sku_id']
            recommendations.append(f"Review {c_items} Category C items for consolidation or elimination")
            recommendations.append("Use simple reorder systems for Category C items")
        
        return recommendations

    def _generate_xyz_recommendations(self, xyz_stats: pd.DataFrame, combined_analysis: pd.DataFrame) -> List[str]:
        """Generate XYZ analysis recommendations"""
        recommendations = []
        
        if 'Z' in xyz_stats.index:
            z_items = xyz_stats.loc['Z', 'sku_id']
            recommendations.append(f"{z_items} items have high demand variability - increase safety stock")
        
        if 'X' in xyz_stats.index:
            x_items = xyz_stats.loc['X', 'sku_id']
            recommendations.append(f"{x_items} items have stable demand - optimize for cost efficiency")
        
        return recommendations

    def _generate_turnover_recommendations(self, category_stats: pd.DataFrame) -> List[str]:
        """Generate turnover analysis recommendations"""
        recommendations = []
        
        if 'Very Slow Moving' in category_stats.index:
            very_slow = category_stats.loc['Very Slow Moving', 'sku_id']
            recommendations.append(f"Review {very_slow} very slow-moving items for discontinuation")
        
        if 'Fast Moving' in category_stats.index:
            fast_moving = category_stats.loc['Fast Moving', 'sku_id']
            recommendations.append(f"Ensure adequate stock levels for {fast_moving} fast-moving items")
        
        return recommendations