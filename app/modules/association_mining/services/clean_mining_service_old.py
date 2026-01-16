import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules
from datetime import datetime, timedelta
import logging
import time
import threading
from app.shared.config.config import config
from app.modules.association_mining.services.scoring_service import ScoringService

logger = logging.getLogger(__name__)

class CleanAssociationMiningService:
    """Clean, simplified association mining service with proper configuration and progress tracking"""
    
    def __init__(self, task_id=None, task_manager=None, algorithm_params=None):
        self.scoring_service = ScoringService()
        self.task_id = task_id
        self.task_manager = task_manager
        
        # Set algorithm parameters with fallbacks to config
        self.algorithm_params = algorithm_params or {}
        self.min_support = self.algorithm_params.get('min_support', config.MIN_SUPPORT)
        self.min_confidence = self.algorithm_params.get('min_confidence', config.MIN_CONFIDENCE)
        self.min_lift = self.algorithm_params.get('min_lift', config.MIN_LIFT)
        self.max_recommendations = self.algorithm_params.get('max_recommendations', config.MAX_RECOMMENDATIONS)
        self.decay_rate = self.algorithm_params.get('decay_rate', config.DECAY_RATE)
        
        logger.info(f"🎯 Mining service initialized with parameters:")
        logger.info(f"   📊 min_support: {self.min_support} {'(CUSTOM)' if self.algorithm_params and 'min_support' in self.algorithm_params else '(DEFAULT)'}")
        logger.info(f"   📊 min_confidence: {self.min_confidence} {'(CUSTOM)' if self.algorithm_params and 'min_confidence' in self.algorithm_params else '(DEFAULT)'}")
        logger.info(f"   📊 min_lift: {self.min_lift} {'(CUSTOM)' if self.algorithm_params and 'min_lift' in self.algorithm_params else '(DEFAULT)'}")
        logger.info(f"   📊 max_recommendations: {self.max_recommendations} {'(CUSTOM)' if self.algorithm_params and 'max_recommendations' in self.algorithm_params else '(DEFAULT)'}")
        logger.info(f"   📊 decay_rate: {self.decay_rate} {'(CUSTOM)' if self.algorithm_params and 'decay_rate' in self.algorithm_params else '(DEFAULT)'}")
        logger.info(f"   🔧 algorithm_params source: {self.algorithm_params}")
    
    def _update_progress(self, progress, message):
        """Update progress if task manager is available"""
        if self.task_manager and self.task_id:
            self.task_manager.update_progress(self.task_id, progress, message)
        logger.info(f"Progress: {progress}% - {message}")
    
    def _calculate_adaptive_support(self, num_items, num_transactions, original_support):
        """Calculate adaptive support based on dataset size"""
        # Check if this is a custom/scheduled job with specific parameters
        is_custom_params = (hasattr(self, 'algorithm_params') and 
                           self.algorithm_params and 
                           'min_support' in self.algorithm_params)
        
        if is_custom_params:
            # User provided custom parameters - respect their choice
            logger.info(f"Using CUSTOM min_support={original_support:.3f} (user-specified, no adaptation)")
            return original_support
        
        # Default behavior for regular mining (adapt based on dataset size)
        if num_items > 800:
            # For large item sets (shouldn't happen with filtering), use higher support
            adaptive_support = max(0.02, 15 / num_transactions)
            logger.warning(f"LARGE DATASET: {num_items} items - using adaptive support {adaptive_support:.3f}")
        elif num_items > 500:
            # Medium item sets - moderate support
            adaptive_support = max(0.01, 8 / num_transactions)
            logger.info(f"Medium dataset: {num_items} items - using adaptive support {adaptive_support:.3f}")
        else:
            # Optimal range (<=500 items) - use original support
            adaptive_support = original_support
            logger.info(f"Optimal dataset size: {num_items} items - using original support {adaptive_support:.3f}")
        
        return adaptive_support
    
    def run_mining_pipeline(self, df_basket, timeout_minutes=20):
        """Run the complete mining pipeline with timeout protection (default 20 minutes for batch processing)"""
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
            
            # Step 3: Mine association rules (NO TIMEOUT - runs until completion or error)
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
        """Create transaction list from weighted basket data"""
        logger.info("Creating transactions")
        
        transactions = []
        for order_id, group in df_weighted.groupby('ORDER_ID'):
            # Use SKU_ID instead of SKU_NAME to ensure IDs are used throughout
            items = group['ARTICLE_ID'].unique().tolist()
            if len(items) > 0:
                transactions.append(items)
        
        logger.info(f"Created {len(transactions)} transactions")
        return transactions
    
    def _mine_rules_with_timeout(self, transactions, timeout_seconds):
        """Mine association rules - runs until completion or error (no timeout)"""
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
            adaptive_support = self._calculate_adaptive_support(num_items, num_transactions, self.min_support)
            
            # Mine frequent itemsets WITHOUT timeout - let it run until completion or error
            logger.info(f"Starting FP-Growth with support={adaptive_support:.3f} (NO TIMEOUT - will run until complete)")
            
            result_container = {'itemsets': None, 'error': None, 'completed': False, 'progress_time': time.time()}
            
            def run_fpgrowth():
                try:
                    logger.info("FP-Growth algorithm started - this may take several minutes for large datasets...")
                    result_container['itemsets'] = fpgrowth(
                        basket_matrix, 
                        min_support=adaptive_support, 
                        use_colnames=True
                    )
                    result_container['completed'] = True
                    logger.info("SUCCESS: FP-Growth completed successfully!")
                except MemoryError as e:
                    result_container['error'] = f"MEMORY ERROR: Not enough memory to process {num_items} items. Try reducing MAX_ITEMS or increasing MIN_ITEM_FREQUENCY."
                    logger.error(f"MEMORY ERROR: {e}")
                    logger.error(f"Dataset too large: {num_items} items x {num_transactions} transactions")
                    logger.error("Solution: Reduce MAX_ITEMS in .env file or increase MIN_ITEM_FREQUENCY")
                except Exception as e:
                    result_container['error'] = str(e)
                    logger.error(f"ERROR: FP-Growth error: {e}")
            
            # Run without timeout - just monitor progress
            fpgrowth_thread = threading.Thread(target=run_fpgrowth)
            fpgrowth_thread.daemon = False  # Non-daemon so it completes
            fpgrowth_thread.start()
            
            # Monitor progress (report every 30 seconds)
            start_monitor = time.time()
            last_log_time = start_monitor
            
            while fpgrowth_thread.is_alive():
                time.sleep(5)
                current_time = time.time()
                elapsed = current_time - start_monitor
                
                # Log progress every 30 seconds
                if current_time - last_log_time >= 30:
                    minutes = int(elapsed // 60)
                    seconds = int(elapsed % 60)
                    logger.info(f"FP-Growth still running... {minutes}m {seconds}s elapsed")
                    last_log_time = current_time
            
            # Thread completed - check results
            total_elapsed = time.time() - start_monitor
            minutes = int(total_elapsed // 60)
            seconds = int(total_elapsed % 60)
            
            if result_container['error']:
                logger.error(f"FP-Growth failed after {minutes}m {seconds}s: {result_container['error']}")
                raise Exception(result_container['error'])
            
            logger.info(f"SUCCESS: FP-Growth completed in {minutes}m {seconds}s")
            
            freq_itemsets = result_container['itemsets']
            
            if freq_itemsets is None or freq_itemsets.empty:
                logger.warning(f"No frequent itemsets found with support={adaptive_support:.3f}")
                logger.warning(f"Try lowering min_support parameter (current: {self.min_support})")
                return pd.DataFrame()
            
            logger.info(f"Found {len(freq_itemsets)} frequent itemsets")
            
            # Generate association rules
            logger.info(f"Generating association rules with min_lift={self.min_lift}")
            rules = association_rules(
                freq_itemsets, 
                metric="lift", 
                min_threshold=self.min_lift
            )
            
            if rules.empty:
                logger.warning("No rules found")
                return pd.DataFrame()
            
            # Filter by confidence
            initial_count = len(rules)
            rules = rules[rules['confidence'] >= self.min_confidence]
            
            logger.info(f"🎯 CONFIDENCE FILTER: {initial_count} -> {len(rules)} rules (confidence >= {self.min_confidence})")
            
            if len(rules) > 0:
                logger.info(f"🎯 FINAL RULES SUMMARY:")
                logger.info(f"   📈 Support range: {rules['support'].min():.3f} - {rules['support'].max():.3f}")
                logger.info(f"   📈 Confidence range: {rules['confidence'].min():.3f} - {rules['confidence'].max():.3f}")
                logger.info(f"   📈 Lift range: {rules['lift'].min():.3f} - {rules['lift'].max():.3f}")
            else:
                logger.warning(f"❌ NO RULES passed confidence filter of {self.min_confidence}!")
            
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
                    # antecedent and consequent are now SKU IDs (not names)
                    # No need for conversion, just use them directly
                    main_item_id = antecedent
                    recommended_item_id = consequent
                    
                    # Get SKU names for reference/logging
                    main_item_name = self.sku_id_to_name.get(antecedent, antecedent)
                    recommended_item_name = self.sku_id_to_name.get(consequent, consequent)
                    
                    recommendations.append({
                        'main_item': main_item_id,          # SKU ID
                        'recommended_item': recommended_item_id,  # SKU ID
                        'main_item_name': main_item_name,       # SKU name for reference
                        'recommended_item_name': recommended_item_name, # SKU name for reference
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
        
        # Keep only top recommendations per item (use custom parameter)
        rec_df = rec_df[rec_df['recommendation_rank'] <= self.max_recommendations]
        
        logger.info(f"🎯 RECOMMENDATIONS FILTER: Using max_recommendations={self.max_recommendations} (per item)")
        logger.info(f"🎯 Created {len(rec_df)} total recommendations for {rec_df['main_item'].nunique()} items")
        return rec_df