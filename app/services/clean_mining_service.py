import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules
from datetime import datetime, timedelta
import logging
import time
import threading
from app.utils.config import config
from app.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)

class CleanAssociationMiningService:
    """Clean, simplified association mining service with proper configuration and progress tracking"""
    
    def __init__(self, task_id=None, task_manager=None):
        self.scoring_service = ScoringService()
        self.task_id = task_id
        self.task_manager = task_manager
    
    def _update_progress(self, progress, message):
        """Update progress if task manager is available"""
        if self.task_manager and self.task_id:
            self.task_manager.update_progress(self.task_id, progress, message)
        logger.info(f"Progress: {progress}% - {message}")
    
    def _calculate_adaptive_support(self, num_items, num_transactions, original_support):
        """Calculate adaptive support to prevent performance issues"""
        if num_items > 400:
            # For very large item sets, force high support
            adaptive_support = max(0.20, 30 / num_transactions)
            logger.warning(f"PERFORMANCE PROTECTION: {num_items} items - forcing support {adaptive_support:.3f}")
        elif num_items > 200:
            # For medium item sets, use moderate support  
            adaptive_support = max(0.10, 15 / num_transactions)
            logger.warning(f"Performance optimization: {num_items} items - using support {adaptive_support:.3f}")
        elif original_support < 0.02:
            # Never go below 2% for any dataset
            adaptive_support = max(0.02, 5 / num_transactions)
            logger.warning(f"Minimum support protection: using {adaptive_support:.3f} (was {original_support})")
        else:
            adaptive_support = original_support
        
        return adaptive_support
    
    def run_mining_pipeline(self, df_basket, timeout_minutes=5):
        """Run the complete mining pipeline with timeout protection"""
        try:
            start_time = time.time()
            timeout_seconds = timeout_minutes * 60
            
            logger.info(f"Starting clean mining pipeline")
            logger.info(f"Input data shape: {df_basket.shape}")
            
            # Create SKU mapping (name to ID and ID to name)
            self.sku_name_to_id = dict(zip(df_basket['SKU_NAME'], df_basket['ARTICLE_ID']))
            self.sku_id_to_name = dict(zip(df_basket['ARTICLE_ID'], df_basket['SKU_NAME']))
            logger.info(f"Created SKU mapping for {len(self.sku_name_to_id)} unique SKUs")
            
            self._update_progress(10, "Starting mining pipeline")
            
            if df_basket.empty:
                logger.error("Input dataframe is empty")
                return pd.DataFrame()
            
            # Step 1: Apply time weighting
            self._update_progress(20, "Applying time weighting")
            df_weighted = self._apply_time_weighting(df_basket)
            
            # Step 2: Create transactions
            self._update_progress(40, "Creating transactions")
            transactions = self._create_transactions(df_weighted)
            
            if len(transactions) == 0:
                logger.error("No transactions created")
                return pd.DataFrame()
            
            # Step 3: Mine association rules with timeout
            self._update_progress(60, "Mining association rules")
            rules = self._mine_rules_with_timeout(transactions, timeout_seconds - (time.time() - start_time))
            
            if rules.empty:
                logger.warning("No rules found")
                return pd.DataFrame()
            
            # Step 4: Create recommendations
            self._update_progress(90, "Creating recommendations")
            recommendations = self._create_recommendations(rules)
            
            self._update_progress(100, "Mining completed successfully")
            
            total_time = time.time() - start_time
            logger.info(f"Mining completed in {total_time:.2f} seconds")
            logger.info(f"Generated {len(recommendations)} recommendations from {len(rules)} rules")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in mining pipeline: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return pd.DataFrame()
    
    def _apply_time_weighting(self, df_basket):
        """Apply simple exponential time weighting"""
        logger.info("Applying exponential time weighting")
        
        # Convert to datetime
        df_basket['order_date'] = pd.to_datetime(df_basket['order_date'])
        max_date = df_basket['order_date'].max()
        
        # Calculate days ago and time weight
        df_basket['days_ago'] = (max_date - df_basket['order_date']).dt.days
        df_basket['time_weight'] = np.exp(-config.DECAY_RATE * df_basket['days_ago'])
        
        logger.info(f"Time weighting applied - weight range: {df_basket['time_weight'].min():.3f} to {df_basket['time_weight'].max():.3f}")
        return df_basket
    
    def _create_transactions(self, df_weighted):
        """Create transaction list from weighted data"""
        logger.info("Creating transaction list")
        
        transactions = []
        for order_id, group in df_weighted.groupby('ORDER_ID'):
            # Simple approach: just use unique items per order
            items = group['SKU_NAME'].unique().tolist()
            if len(items) > 0:
                transactions.append(items)
        
        logger.info(f"Created {len(transactions)} transactions")
        return transactions
    
    def _mine_rules_with_timeout(self, transactions, timeout_seconds):
        """Mine association rules with timeout protection"""
        try:
            # Create transaction matrix
            logger.info("Creating transaction matrix")
            te = TransactionEncoder()
            onehot = te.fit(transactions).transform(transactions)
            basket_matrix = pd.DataFrame(onehot, columns=te.columns_)
            
            num_items = basket_matrix.shape[1]
            num_transactions = basket_matrix.shape[0]
            
            logger.info(f"Transaction matrix: {basket_matrix.shape}")
            logger.info(f"Matrix density: {(basket_matrix.sum().sum() / (num_transactions * num_items) * 100):.2f}%")
            
            # Calculate adaptive support
            adaptive_support = self._calculate_adaptive_support(num_items, num_transactions, config.MIN_SUPPORT)
            
            # Mine frequent itemsets with timeout
            logger.info(f"Starting FP-Growth with support={adaptive_support:.3f}, timeout={timeout_seconds:.0f}s")
            
            result_container = {'itemsets': None, 'error': None, 'completed': False}
            
            def run_fpgrowth():
                try:
                    result_container['itemsets'] = fpgrowth(
                        basket_matrix, 
                        min_support=adaptive_support, 
                        use_colnames=True
                    )
                    result_container['completed'] = True
                    logger.info("FP-Growth completed successfully")
                except Exception as e:
                    result_container['error'] = e
                    logger.error(f"FP-Growth error: {e}")
            
            # Run with timeout
            fpgrowth_thread = threading.Thread(target=run_fpgrowth)
            fpgrowth_thread.daemon = True
            fpgrowth_thread.start()
            
            # Monitor progress
            start_monitor = time.time()
            while fpgrowth_thread.is_alive() and (time.time() - start_monitor) < timeout_seconds:
                time.sleep(5)
                elapsed = time.time() - start_monitor
                logger.info(f"FP-Growth running... {elapsed:.0f}s elapsed")
            
            if fpgrowth_thread.is_alive():
                logger.error(f"FP-Growth timed out after {timeout_seconds:.0f}s")
                logger.error("Consider using fewer items or higher min_support")
                return pd.DataFrame()
            
            if result_container['error']:
                raise result_container['error']
            
            freq_itemsets = result_container['itemsets']
            
            if freq_itemsets.empty:
                logger.warning(f"No frequent itemsets found with support={adaptive_support:.3f}")
                return pd.DataFrame()
            
            logger.info(f"Found {len(freq_itemsets)} frequent itemsets")
            
            # Generate association rules
            logger.info("Generating association rules")
            rules = association_rules(
                freq_itemsets, 
                metric="lift", 
                min_threshold=config.MIN_LIFT
            )
            
            if rules.empty:
                logger.warning("No rules found")
                return pd.DataFrame()
            
            # Filter by confidence
            initial_count = len(rules)
            rules = rules[rules['confidence'] >= config.MIN_CONFIDENCE]
            
            logger.info(f"Filtered rules: {initial_count} -> {len(rules)} (confidence >= {config.MIN_CONFIDENCE})")
            
            return rules
            
        except Exception as e:
            logger.error(f"Error in rule mining: {e}")
            return pd.DataFrame()
    
    def _create_recommendations(self, rules):
        """Create recommendations from rules"""
        logger.info("Creating recommendations")
        
        recommendations = []
        
        for _, rule in rules.iterrows():
            antecedents = list(rule['antecedents'])
            consequents = list(rule['consequents'])
            
            for antecedent in antecedents:
                for consequent in consequents:
                    # Get SKU IDs from names
                    main_item_id = self.sku_name_to_id.get(antecedent, antecedent)
                    recommended_item_id = self.sku_name_to_id.get(consequent, consequent)
                    
                    recommendations.append({
                        'main_item': main_item_id,          # Now stores SKU ID
                        'recommended_item': recommended_item_id,  # Now stores SKU ID
                        'main_item_name': antecedent,       # Keep name for reference
                        'recommended_item_name': consequent, # Keep name for reference
                        'confidence_score': rule['confidence'],
                        'lift_score': rule['lift'],
                        'support_score': rule['support'],
                        'composite_score': rule['confidence'] * rule['lift'],
                        'temporal_stability': 0.5,  # Default value
                        'temporal_trend': 0.0,      # Default value
                        'temporal_composite_score': rule['confidence'] * rule['lift'],
                        'recommendation_rank': 1
                    })
        
        if not recommendations:
            return pd.DataFrame()
        
        # Convert to DataFrame and add ranking
        rec_df = pd.DataFrame(recommendations)
        
        # Add proper ranking within each main item
        rec_df['recommendation_rank'] = (
            rec_df.groupby('main_item')['composite_score']
            .rank(method='dense', ascending=False)
            .astype(int)
        )
        
        # Keep only top recommendations per item
        rec_df = rec_df[rec_df['recommendation_rank'] <= config.MAX_RECOMMENDATIONS]
        
        logger.info(f"Created {len(rec_df)} recommendations for {rec_df['main_item'].nunique()} items")
        return rec_df