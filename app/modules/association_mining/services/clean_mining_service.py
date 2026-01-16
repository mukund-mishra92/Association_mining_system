import logging
import threading
import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder

from app.modules.association_mining.services.scoring_service import ScoringService
from app.shared.config.config import config

logger = logging.getLogger(__name__)


class CleanAssociationMiningService:
    """Clean association mining service with configuration and progress tracking.

    Performance-focused notes:
      - Use sparse one-hot encoding to reduce memory/CPU.
      - Use max_len=2 in FP-Growth to avoid exploring long itemsets (major speedup).
      - Vectorize recommendation creation (avoid Python loops over rules).
    """

    def __init__(self, task_id=None, task_manager=None, algorithm_params=None):
        self.scoring_service = ScoringService()
        self.task_id = task_id
        self.task_manager = task_manager

        # Algorithm parameters with fallbacks to config
        self.algorithm_params = algorithm_params or {}
        self.min_support = float(self.algorithm_params.get("min_support", config.MIN_SUPPORT))
        self.min_confidence = float(self.algorithm_params.get("min_confidence", config.MIN_CONFIDENCE))
        self.min_lift = float(self.algorithm_params.get("min_lift", config.MIN_LIFT))
        self.max_recommendations = int(self.algorithm_params.get("max_recommendations", config.MAX_RECOMMENDATIONS))
        self.decay_rate = float(self.algorithm_params.get("decay_rate", config.DECAY_RATE))

        # Performance knobs (safe defaults)
        # IMPORTANT: max_len=2 prevents FP-Growth from enumerating long patterns (often the cause of "stuck" jobs)
        self.max_len = int(self.algorithm_params.get("max_len", 2))
        self.use_sparse_matrix = bool(self.algorithm_params.get("use_sparse_matrix", True))

        # Optional: prune rare items before mining (off by default to avoid behavior change)
        # If set (e.g. 5/10/20), items appearing in fewer than this many orders are removed.
        self.min_item_orders = self.algorithm_params.get("min_item_orders", None)
        self.min_item_orders = int(self.min_item_orders) if self.min_item_orders is not None else None

        # Optional: skip time weighting step (time weighting is not used in mining matrix currently)
        self.skip_time_weighting = bool(self.algorithm_params.get("skip_time_weighting", False))

        logger.info("🎯 Mining service initialized with parameters:")
        logger.info(
            f"   📊 min_support: {self.min_support} "
            f"{'(CUSTOM)' if 'min_support' in self.algorithm_params else '(DEFAULT)'}"
        )
        logger.info(
            f"   📊 min_confidence: {self.min_confidence} "
            f"{'(CUSTOM)' if 'min_confidence' in self.algorithm_params else '(DEFAULT)'}"
        )
        logger.info(
            f"   📊 min_lift: {self.min_lift} "
            f"{'(CUSTOM)' if 'min_lift' in self.algorithm_params else '(DEFAULT)'}"
        )
        logger.info(
            f"   📊 max_recommendations: {self.max_recommendations} "
            f"{'(CUSTOM)' if 'max_recommendations' in self.algorithm_params else '(DEFAULT)'}"
        )
        logger.info(
            f"   📊 decay_rate: {self.decay_rate} "
            f"{'(CUSTOM)' if 'decay_rate' in self.algorithm_params else '(DEFAULT)'}"
        )
        logger.info(f"   🔧 max_len: {self.max_len} (limits FP-Growth search space)")
        logger.info(f"   🔧 use_sparse_matrix: {self.use_sparse_matrix}")
        logger.info(f"   🔧 min_item_orders: {self.min_item_orders} (optional pruning)")
        logger.info(f"   🔧 skip_time_weighting: {self.skip_time_weighting}")
        logger.info(f"   🔧 algorithm_params source: {self.algorithm_params}")

        # Will be filled during run
        self.sku_name_to_id = {}
        self.sku_id_to_name = {}

    def _update_progress(self, progress, message):
        """Update progress if task manager is available"""
        if self.task_manager and self.task_id:
            self.task_manager.update_progress(self.task_id, progress, message)
        logger.info(f"Progress: {progress}% - {message}")

    def _calculate_adaptive_support(self, num_items, num_transactions, original_support):
        """Calculate adaptive support based on dataset size

        NOTE: If user explicitly provides min_support, we respect it (no adaptation).
        """
        is_custom_params = bool(self.algorithm_params and "min_support" in self.algorithm_params)
        if is_custom_params:
            logger.info(f"Using CUSTOM min_support={original_support:.3f} (user-specified, no adaptation)")
            return original_support

        if num_items > 800:
            adaptive_support = max(0.02, 15 / max(num_transactions, 1))
            logger.warning(f"LARGE DATASET: {num_items} items - using adaptive support {adaptive_support:.3f}")
        elif num_items > 500:
            adaptive_support = max(0.01, 8 / max(num_transactions, 1))
            logger.info(f"Medium dataset: {num_items} items - using adaptive support {adaptive_support:.3f}")
        else:
            adaptive_support = original_support
            logger.info(f"Optimal dataset size: {num_items} items - using original support {adaptive_support:.3f}")

        return adaptive_support

    def run_mining_pipeline(self, df_basket, timeout_minutes=20):
        """Run the complete mining pipeline.

        NOTE: We keep the signature/flow stable, but optimize critical steps.
        """
        try:
            start_time = time.time()

            logger.info("Starting clean mining pipeline")
            logger.info(f"Input data shape: {df_basket.shape}")

            if df_basket is None or df_basket.empty:
                logger.error("Input dataframe is empty")
                return pd.DataFrame()

            # Create SKU mapping (name to ID and ID to name)
            # Expecting columns: SKU_NAME, ARTICLE_ID
            self.sku_name_to_id = dict(zip(df_basket["SKU_NAME"], df_basket["ARTICLE_ID"]))
            self.sku_id_to_name = dict(zip(df_basket["ARTICLE_ID"], df_basket["SKU_NAME"]))
            logger.info(f"Created SKU mapping for {len(self.sku_name_to_id)} unique SKUs")

            self._update_progress(10, "Starting mining pipeline")

            # Step 1: Optional time weighting
            self._update_progress(20, "Applying time weighting")
            if self.skip_time_weighting:
                df_weighted = df_basket
                logger.info("Skipping time weighting (skip_time_weighting=True)")
            else:
                df_weighted = self._apply_time_weighting(df_basket)

            # Optional: prune rare items to reduce matrix width (major speedup when many SKUs)
            if self.min_item_orders is not None and self.min_item_orders > 1:
                self._update_progress(30, f"Pruning items with < {self.min_item_orders} orders")
                df_weighted = self._prune_rare_items(df_weighted, self.min_item_orders)

                if df_weighted.empty:
                    logger.warning("All items pruned by min_item_orders filter; no data left to mine")
                    return pd.DataFrame()

            # Step 2: Create transactions
            self._update_progress(40, "Creating transactions")
            transactions = self._create_transactions(df_weighted)
            if not transactions:
                logger.error("No transactions created")
                return pd.DataFrame()

            # Step 3: Mine rules
            self._update_progress(60, "Mining association rules")
            rules = self._mine_rules(transactions)
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

    def _apply_time_weighting(self, df_basket: pd.DataFrame) -> pd.DataFrame:
        """Apply exponential time weighting.

        NOTE: The current mining matrix is binary and does not use time_weight directly.
        This is still kept for future weighted mining/scoring and for backward compatibility.
        """
        logger.info("Applying exponential time weighting")

        df = df_basket.copy()
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        max_date = df["order_date"].max()

        # If order_date is missing/unparseable, default to no weighting
        if pd.isna(max_date):
            df["days_ago"] = 0
            df["time_weight"] = 1.0
            logger.warning("order_date missing/unparseable; using time_weight=1.0 for all rows")
            return df

        df["days_ago"] = (max_date - df["order_date"]).dt.days.fillna(0).astype(int)
        df["time_weight"] = np.exp(-self.decay_rate * df["days_ago"])

        logger.info(
            f"Time weighting applied - weight range: {df['time_weight'].min():.3f} to {df['time_weight'].max():.3f}"
        )
        return df

    def _prune_rare_items(self, df_weighted: pd.DataFrame, min_orders: int) -> pd.DataFrame:
        """Remove items that appear in fewer than `min_orders` distinct orders."""
        t0 = time.time()

        # Count distinct orders per SKU ID
        counts = df_weighted.groupby("ARTICLE_ID")["ORDER_ID"].nunique()
        keep_ids = counts[counts >= min_orders].index

        pruned = df_weighted[df_weighted["ARTICLE_ID"].isin(keep_ids)].copy()

        # Keep SKU mappings consistent for items still present
        if not pruned.empty:
            self.sku_id_to_name = dict(zip(pruned["ARTICLE_ID"], pruned["SKU_NAME"]))
            self.sku_name_to_id = dict(zip(pruned["SKU_NAME"], pruned["ARTICLE_ID"]))

        logger.info(
            f"Pruned rare items: {len(counts)} -> {len(keep_ids)} items kept "
            f"(min_item_orders={min_orders}) in {time.time() - t0:.2f}s"
        )
        logger.info(f"Data shape after pruning: {pruned.shape}")
        return pruned

    def _create_transactions(self, df_weighted: pd.DataFrame):
        """Create transaction list from basket data.

        Uses a vectorized groupby to build transactions faster than a Python loop.
        """
        logger.info("Creating transactions")

        t0 = time.time()
        # Each transaction is a list of unique ARTICLE_IDs per ORDER_ID
        grouped = df_weighted.groupby("ORDER_ID")["ARTICLE_ID"].unique()
        transactions = [arr.tolist() for arr in grouped.values if len(arr) > 0]

        logger.info(f"Created {len(transactions)} transactions in {time.time() - t0:.2f}s")
        return transactions

    def _mine_rules(self, transactions):
        """Mine association rules using FP-Growth with performance safeguards."""
        try:
            te = TransactionEncoder()

            t_encode = time.time()
            if self.use_sparse_matrix:
                onehot_sparse = te.fit(transactions).transform(transactions, sparse=True)
                basket_matrix = pd.DataFrame.sparse.from_spmatrix(onehot_sparse, columns=te.columns_)
            else:
                onehot = te.fit(transactions).transform(transactions)
                basket_matrix = pd.DataFrame(onehot, columns=te.columns_, dtype=bool)

            num_items = basket_matrix.shape[1]
            num_transactions = basket_matrix.shape[0]

            logger.info(f"Transaction matrix: {basket_matrix.shape}")

            # Density calculation that works for sparse & dense
            try:
                nonzero = basket_matrix.sparse.to_coo().nnz  # type: ignore[attr-defined]
                density = (nonzero / (num_transactions * num_items)) * 100 if (num_transactions * num_items) else 0
            except Exception:
                density = (basket_matrix.sum().sum() / (num_transactions * num_items) * 100) if (num_transactions * num_items) else 0

            logger.info(f"Matrix density: {density:.2f}%")
            logger.info(f"One-hot encoding completed in {time.time() - t_encode:.2f}s")

            adaptive_support = self._calculate_adaptive_support(num_items, num_transactions, self.min_support)

            # Heartbeat logging while FP-Growth runs (no thread join complexity, just a logger loop)
            stop_event = threading.Event()

            def heartbeat():
                started = time.time()
                last = started
                while not stop_event.is_set():
                    time.sleep(5)
                    now = time.time()
                    if now - last >= 30:
                        elapsed = now - started
                        minutes = int(elapsed // 60)
                        seconds = int(elapsed % 60)
                        logger.info(f"FP-Growth still running... {minutes}m {seconds}s elapsed")
                        last = now

            hb_thread = threading.Thread(target=heartbeat, daemon=True)
            hb_thread.start()

            logger.info(
                f"Starting FP-Growth with support={adaptive_support:.3f}, max_len={self.max_len} "
                f"(NO TIMEOUT - will run until complete)"
            )

            t0 = time.time()
            try:
                freq_itemsets = fpgrowth(
                    basket_matrix,
                    min_support=adaptive_support,
                    use_colnames=True,
                    max_len=self.max_len,
                )
            finally:
                stop_event.set()

            elapsed = time.time() - t0
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            logger.info(f"SUCCESS: FP-Growth completed in {minutes}m {seconds}s")

            if freq_itemsets is None or freq_itemsets.empty:
                logger.warning(f"No frequent itemsets found with support={adaptive_support:.3f}")
                logger.warning(f"Try lowering min_support parameter (current: {self.min_support})")
                return pd.DataFrame()

            logger.info(f"Found {len(freq_itemsets)} frequent itemsets")

            logger.info(f"Generating association rules with min_lift={self.min_lift}")
            rules = association_rules(freq_itemsets, metric="lift", min_threshold=self.min_lift)

            if rules.empty:
                logger.warning("No rules found")
                return pd.DataFrame()

            initial_count = len(rules)
            rules = rules[rules["confidence"] >= self.min_confidence]
            logger.info(
                f"🎯 CONFIDENCE FILTER: {initial_count} -> {len(rules)} rules "
                f"(confidence >= {self.min_confidence})"
            )

            if len(rules) > 0:
                logger.info("🎯 FINAL RULES SUMMARY:")
                logger.info(f"   📈 Support range: {rules['support'].min():.3f} - {rules['support'].max():.3f}")
                logger.info(
                    f"   📈 Confidence range: {rules['confidence'].min():.3f} - {rules['confidence'].max():.3f}"
                )
                logger.info(f"   📈 Lift range: {rules['lift'].min():.3f} - {rules['lift'].max():.3f}")
            else:
                logger.warning(f"❌ NO RULES passed confidence filter of {self.min_confidence}!")

            return rules

        except MemoryError as e:
            logger.error(f"MEMORY ERROR: {e}")
            logger.error(
                "Not enough memory to mine. Try: reduce max_items, increase min_support, enable use_sparse_matrix, "
                "or set min_item_orders to prune rare items."
            )
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error in rule mining: {e}")
            return pd.DataFrame()

    def _create_recommendations(self, rules: pd.DataFrame) -> pd.DataFrame:
        """Create recommendations from rules.

        With max_len=2, rules are {a}->{b} and {b}->{a}. We vectorize extraction for speed.
        """
        logger.info("Creating recommendations")
        if rules is None or rules.empty:
            return pd.DataFrame()

        # Extract single-item antecedent & consequent fast.
        # (Safe given max_len=2; if multi-item slips in, we skip it.)
        def _single_item(fs):
            if fs is None:
                return None
            try:
                if len(fs) != 1:
                    return None
                return next(iter(fs))
            except Exception:
                return None

        t0 = time.time()

        main_items = rules["antecedents"].apply(_single_item)
        rec_items = rules["consequents"].apply(_single_item)

        rec_df = pd.DataFrame(
            {
                "main_item": main_items,
                "recommended_item": rec_items,
                "confidence_score": rules["confidence"].astype(float),
                "lift_score": rules["lift"].astype(float),
                "support_score": rules["support"].astype(float),
            }
        )

        # Drop anything that isn't 1->1 (should be rare with max_len=2)
        rec_df = rec_df.dropna(subset=["main_item", "recommended_item"])

        if rec_df.empty:
            logger.warning("No 1->1 rules available to convert into recommendations")
            return pd.DataFrame()

        # Compute scores
        rec_df["composite_score"] = rec_df["confidence_score"] * rec_df["lift_score"]
        rec_df["temporal_stability"] = 0.5
        rec_df["temporal_trend"] = 0.0
        rec_df["temporal_composite_score"] = rec_df["composite_score"]

        # Add names for reference/logging
        rec_df["main_item_name"] = rec_df["main_item"].map(self.sku_id_to_name).fillna(rec_df["main_item"])
        rec_df["recommended_item_name"] = rec_df["recommended_item"].map(self.sku_id_to_name).fillna(
            rec_df["recommended_item"]
        )

        # Rank within each main item
        rec_df["recommendation_rank"] = (
            rec_df.groupby("main_item")["composite_score"]
            .rank(method="dense", ascending=False)
            .astype(int)
        )

        # Keep only top recommendations per item
        rec_df = rec_df[rec_df["recommendation_rank"] <= self.max_recommendations]

        # Sort for readability
        rec_df = rec_df.sort_values(["main_item", "recommendation_rank", "composite_score"], ascending=[True, True, False])

        logger.info(f"Recommendations built in {time.time() - t0:.2f}s")
        logger.info(f"🎯 RECOMMENDATIONS FILTER: Using max_recommendations={self.max_recommendations} (per item)")
        logger.info(f"🎯 Created {len(rec_df)} total recommendations for {rec_df['main_item'].nunique()} items")

        return rec_df