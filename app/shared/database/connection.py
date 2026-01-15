import pymysql
import pandas as pd
from app.shared.config.config import config
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, custom_config=None):
        self.connection = None
        self.cursor = None
        self.custom_config = custom_config
        
        # Set configuration - use custom config if provided, otherwise use default
        if custom_config:
            self.db_host = custom_config.get('host', config.DB_HOST)
            self.db_port = custom_config.get('port', config.DB_PORT)
            self.db_user = custom_config.get('user', config.DB_USER)
            self.db_password = custom_config.get('password', config.DB_PASSWORD)
            self.db_name = custom_config.get('database', config.DB_NAME)
            self.order_table = custom_config.get('order_table', config.ORDER_TABLE)
            self.sku_master_table = custom_config.get('sku_master_table', config.SKU_MASTER_TABLE)
            self.recommendations_table = custom_config.get('recommendations_table', config.RECOMMENDATIONS_TABLE)
            logger.info(f"DatabaseConnection initialized with custom configuration - table: {self.recommendations_table}")
        else:
            self.db_host = config.DB_HOST
            self.db_port = config.DB_PORT
            self.db_user = config.DB_USER
            self.db_password = config.DB_PASSWORD
            self.db_name = config.DB_NAME
            self.order_table = config.ORDER_TABLE
            self.sku_master_table = config.SKU_MASTER_TABLE
            self.recommendations_table = config.RECOMMENDATIONS_TABLE
            logger.info(f"DatabaseConnection initialized with default configuration - table: {self.recommendations_table}")
    
    def connect(self):
        """Establish database connection"""
        try:
            logger.info(f"Attempting to connect to MySQL at {self.db_host}:{self.db_port} as user '{self.db_user}'")
            self.connection = pymysql.connect(
                host=self.db_host,
                port=self.db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.Cursor
            )
            self.cursor = self.connection.cursor()
            logger.info(f"✓ Database connection established to {self.db_host}:{self.db_port}")
            return True
        except pymysql.MySQLError as e:
            logger.error(f"✗ Error connecting to database {self.db_host}:{self.db_port}: {e}")
            logger.error(f"Connection details - Host: {self.db_host}, Port: {self.db_port}, User: {self.db_user}, Database: {self.db_name}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    

    #// ...existing code...
    def fetch_order_data(self, days_back=None, max_items=None, min_item_frequency=None):
        """
        Fetch order data with smart filtering for performance.

        Args:
            days_back: Number of days to look back from the latest date in database
            max_items: Maximum number of items to include (top N most frequent)
            min_item_frequency: Minimum number of orders an item must appear in
        """
        try:
            # Import config for default values
            from app.shared.config.config import config
            max_items = max_items or config.MAX_ITEMS
            min_item_frequency = min_item_frequency or config.MIN_ITEM_FREQUENCY

            # First, find the latest date available in the database
            latest_date_query = f"SELECT MAX(DATE(INSERTED_TIMESTAMP)) as max_date FROM {self.order_table}"
            latest_date_df = pd.read_sql(latest_date_query, self.connection)
            max_date = latest_date_df['max_date'].iloc[0]

            if pd.isna(max_date) or max_date is None:
                logger.warning("No order dates found in the order table; aborting fetch.")
                return pd.DataFrame()

            if days_back:
                from datetime import timedelta
                start_date = max_date - timedelta(days=days_back)
                logger.info(f"Latest date in database: {max_date}")
                logger.info(f"Looking back {days_back} days from {max_date} (from {start_date} to {max_date})")
            else:
                logger.info(f"Latest date in database: {max_date} (no date filtering)")

            # Determine whether to include all SKUs (use large sentinel like >=10000 to mean "all")
            include_all_skus = (max_items is None) or (int(max_items) >= 10000)

            # Build frequency query
            base_where = "WHERE s.SKU_NAME IS NOT NULL"
            if days_back:
                # use BETWEEN to be explicit and bounded by max_date
                base_where += f" AND DATE(o.INSERTED_TIMESTAMP) BETWEEN DATE_SUB('{max_date}', INTERVAL {days_back} DAY) AND '{max_date}'"

            if include_all_skus:
                logger.info(f"Including ALL unique SKUs with minimum {min_item_frequency} orders (no top-N limit)...")
                freq_query = f"""
                SELECT
                    o.ARTICLE_ID,
                    COUNT(DISTINCT o.ORDER_ID) as order_count,
                    COUNT(*) as total_quantity
                FROM {self.order_table} o
                JOIN {self.sku_master_table} s ON o.ARTICLE_ID = s.SKU_ID
                {base_where}
                GROUP BY o.ARTICLE_ID
                HAVING order_count >= {min_item_frequency}
                ORDER BY order_count DESC, total_quantity DESC
                """
            else:
                logger.info(f"Finding top {max_items} items with minimum {min_item_frequency} orders...")
                freq_query = f"""
                SELECT
                    o.ARTICLE_ID,
                    COUNT(DISTINCT o.ORDER_ID) as order_count,
                    COUNT(*) as total_quantity
                FROM {self.order_table} o
                JOIN {self.sku_master_table} s ON o.ARTICLE_ID = s.SKU_ID
                {base_where}
                GROUP BY o.ARTICLE_ID
                HAVING order_count >= {min_item_frequency}
                ORDER BY order_count DESC, total_quantity DESC
                LIMIT {int(max_items)}
                """

            top_items_df = pd.read_sql(freq_query, self.connection)

            if top_items_df.empty:
                logger.warning("No items found matching criteria (after frequency query).")
                return pd.DataFrame()

            top_article_ids = top_items_df['ARTICLE_ID'].astype(str).tolist()

            # log frequency range safely
            logger.info(f"Selected {len(top_article_ids)} items (appeared in {min_item_frequency}+ orders)")
            logger.info(f"Frequency range: {top_items_df['order_count'].min()} to {top_items_df['order_count'].max()} orders")

            # Step 2: Fetch order data for only these top items
            # Use a join with a subquery to avoid massive IN(...) lists for large lists
            # Build a temporary table of selected IDs in SQL using VALUES if list is small, otherwise use IN
            article_ids_str = ','.join([f"'{aid}'" for aid in top_article_ids[:10000]])  # safety cap
            query = f"""
            SELECT 
                o.ORDER_ID,
                o.ARTICLE_ID,
                s.SKU_NAME,
                o.INSERTED_TIMESTAMP,
                DATEDIFF('{max_date}', DATE(o.INSERTED_TIMESTAMP)) as days_ago
            FROM {self.order_table} o
            JOIN {self.sku_master_table} s ON o.ARTICLE_ID = s.SKU_ID
            WHERE s.SKU_NAME IS NOT NULL
              AND o.ARTICLE_ID IN ({article_ids_str})
            """

            if days_back:
                query += f" AND DATE(o.INSERTED_TIMESTAMP) BETWEEN DATE_SUB('{max_date}', INTERVAL {days_back} DAY) AND '{max_date}'"

            query += " ORDER BY o.INSERTED_TIMESTAMP DESC"

            df = pd.read_sql(query, self.connection)

            if df.empty:
                logger.warning("No order records fetched for selected SKUs and date range.")
                return pd.DataFrame()

            # Create order_date from INSERTED_TIMESTAMP
            df['order_date'] = pd.to_datetime(df['INSERTED_TIMESTAMP']).dt.date

            unique_items = df['ARTICLE_ID'].nunique()
            unique_orders = df['ORDER_ID'].nunique()
            logger.info(f"Fetched {len(df)} order records")
            logger.info(f"Items: {unique_items} | Orders: {unique_orders} | Avg items per order: {len(df)/unique_orders:.1f}")

            return df

        except Exception as e:
            logger.exception(f"Error fetching order data: {e}")
            return pd.DataFrame()
#// ...existing code...
    
    def save_recommendations(self, recommendations_df):
        """Save recommendations to database using your schema:
        PARENT_ARTICLE_ID, CHILD_ARTICLE_ID, PROXIMITY_SCORE"""
        try:
            initial_generated_count = len(recommendations_df)
            logger.info(f"Attempting to save {initial_generated_count} recommendations")
            
            # Ensure the recommendations table exists
            self._ensure_recommendations_table_exists()
            
            # Filter out invalid rules before saving
            recommendations_df = self._filter_invalid_rules(recommendations_df)
            
            if len(recommendations_df) == 0:
                logger.warning(f"No valid recommendations to save after filtering (Generated: {initial_generated_count}, Valid: 0, Written to DB: 0)")
                return {
                    "total_generated": initial_generated_count,
                    "valid_after_filtering": 0,
                    "total_written": 0,
                    "new_inserts": 0,
                    "updated_existing": 0,
                    "skipped_existing_higher": 0,
                    "decayed_not_in_current": 0,
                    "target_table": self.recommendations_table
                }
            
            valid_count = len(recommendations_df)
            logger.info(f"After filtering invalid rules: {valid_count} valid recommendations remain")

            # Canonicalize pairs so each unordered pair {A,B} is stored once
            # Use a stable ordering on SKU IDs to decide (parent, child).
            if 'main_item' in recommendations_df.columns and 'recommended_item' in recommendations_df.columns:
                try:
                    # Build canonical parent/child for each row
                    canonical = recommendations_df.apply(
                        lambda r: tuple(sorted((str(r['main_item']), str(r['recommended_item'])))),
                        axis=1
                    )
                    recommendations_df['__parent'] = [p for p, _ in canonical]
                    recommendations_df['__child'] = [c for _, c in canonical]

                    # For each unordered pair, keep the row with highest composite_score
                    if 'composite_score' in recommendations_df.columns:
                        recommendations_df = (
                            recommendations_df
                            .sort_values('composite_score', ascending=False)
                            .drop_duplicates(subset=['__parent', '__child'], keep='first')
                        )

                    # Replace main/recommended with canonical orientation
                    recommendations_df['main_item'] = recommendations_df['__parent']
                    recommendations_df['recommended_item'] = recommendations_df['__child']

                    # Drop helper columns
                    recommendations_df = recommendations_df.drop(columns=['__parent', '__child'])

                    logger.info("Canonicalized pairs: storing a single row per unordered pair (x-y == y-x)")
                except Exception as e:
                    logger.error(f"Error canonicalizing pairs; proceeding without deduplication: {e}")

            # No longer clearing existing recommendations - using upsert instead
            # This preserves existing rules and only updates when we get better scores
            
            # Sort recommendations by composite_score descending (highest scores first)
            recommendations_df_sorted = recommendations_df.sort_values('composite_score', ascending=False).reset_index(drop=True)
            logger.info(f"Sorted recommendations by score (highest first)")
            
            # Normalize scores to range 0.001 - 0.999
            scores = recommendations_df_sorted['composite_score'].astype(float)
            min_score = scores.min()
            max_score = scores.max()
            
            # Avoid division by zero if all scores are the same
            if max_score == min_score:
                normalized_scores = [0.5] * len(scores)  # Use middle value
                logger.info(f"All scores identical ({min_score}), using normalized score 0.5")
            else:
                # Normalize to 0.001 - 0.999 range
                normalized_scores = (0.001 + (scores - min_score) / (max_score - min_score) * 0.998).tolist()
                logger.info(f"Normalized scores: {min_score:.3f}-{max_score:.3f} to 0.001-0.999")
            
            # Upsert recommendations - insert new or update existing with higher score
            # Using INSERT ... ON DUPLICATE KEY UPDATE with GREATEST to keep higher scores
            insert_query = f"""
            INSERT INTO {self.recommendations_table} 
            (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID, PROXIMITY_SCORE)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                PROXIMITY_SCORE = GREATEST(VALUES(PROXIMITY_SCORE), PROXIMITY_SCORE)
            """
            
            inserted_count = 0
            updated_count = 0
            skipped_count = 0
            
            for idx, (_, row) in enumerate(recommendations_df_sorted.iterrows()):
                try:
                    self.cursor.execute(insert_query, (
                        row['main_item'],              # PARENT_ARTICLE_ID - now using SKU ID instead of name
                        row['recommended_item'],       # CHILD_ARTICLE_ID - now using SKU ID instead of name
                        float(normalized_scores[idx])  # NORMALIZED PROXIMITY_SCORE (0.001-0.999)
                    ))
                    # rowcount: 1 = new insert, 2 = update occurred, 0 = no change (existing score was higher)
                    if self.cursor.rowcount == 1:
                        inserted_count += 1
                    elif self.cursor.rowcount == 2:
                        updated_count += 1
                    else:
                        skipped_count += 1
                except Exception as e:
                    logger.error(f"Error inserting row: {e}")
                    continue
            
            self.connection.commit()
            
            # Calculate total written to DB (new inserts + updates)
            total_written = inserted_count + updated_count
            
            # Apply decay to rules NOT in the current generation
            # This ensures rules that stop appearing gradually fade out
            decayed_count = self._apply_score_decay(recommendations_df_sorted, decay_factor=0.8)
            
            # Create summary statistics dictionary
            summary_stats = {
                "total_generated": initial_generated_count,
                "valid_after_filtering": valid_count,
                "total_written": total_written,
                "new_inserts": inserted_count,
                "updated_existing": updated_count,
                "skipped_existing_higher": skipped_count,
                "decayed_not_in_current": decayed_count,
                "target_table": self.recommendations_table
            }
            
            logger.info("=" * 80)
            logger.info(f"RULE GENERATION SUMMARY:")
            logger.info(f"  Total Rules Generated: {initial_generated_count}")
            logger.info(f"  Valid Rules (after filtering): {valid_count}")
            logger.info(f"  Rules Written to Database: {total_written}")
            logger.info(f"    - New Inserts: {inserted_count}")
            logger.info(f"    - Updated Existing: {updated_count}")
            logger.info(f"    - Skipped (existing score was higher): {skipped_count}")
            logger.info(f"  Rules Decayed (not in current generation): {decayed_count}")
            logger.info(f"  Target Table: {self.recommendations_table}")
            logger.info("=" * 80)
            
            return summary_stats
            
        except pymysql.MySQLError as e:
            logger.error(f"Error saving recommendations: {e}")
            return False

    def get_recommendations(self, item_name, limit=10):
        """Get recommendations for a specific item using your schema
        
        Args:
            item_name: Can be either SKU_NAME or SKU_ID (we'll check both)
            limit: Maximum number of recommendations to return
        
        Returns:
            List of recommendations with SKU names (human-readable)
        """
        try:
            # Ensure the recommendations table exists
            self._ensure_recommendations_table_exists()
            
            # First, try to find the SKU_ID for the given item_name
            # Check if item_name is already a SKU_ID or if we need to look it up by name
            sku_id_query = f"""
            SELECT SKU_ID FROM {self.sku_master_table}
            WHERE SKU_ID = %s OR SKU_NAME = %s
            LIMIT 1
            """
            self.cursor.execute(sku_id_query, (item_name, item_name))
            sku_result = self.cursor.fetchone()
            
            if not sku_result:
                logger.warning(f"SKU not found: {item_name}")
                return []
            
            parent_sku_id = sku_result[0]

            # Now get recommendations treating pairs as undirected:
            # - If the item is stored as PARENT_ARTICLE_ID, recommend CHILD_ARTICLE_ID
            # - If the item is stored as CHILD_ARTICLE_ID, recommend PARENT_ARTICLE_ID
            query = f"""
            SELECT 
                CASE 
                    WHEN r.PARENT_ARTICLE_ID = %s THEN other_sku.SKU_NAME
                    ELSE other_sku.SKU_NAME
                END as recommended_item_name,
                r.PROXIMITY_SCORE,
                r.SCORE_ID,
                CASE 
                    WHEN r.PARENT_ARTICLE_ID = %s THEN r.CHILD_ARTICLE_ID
                    ELSE r.PARENT_ARTICLE_ID
                END as recommended_item_id
            FROM {self.recommendations_table} r
            INNER JOIN {self.sku_master_table} other_sku 
                ON other_sku.SKU_ID = CASE 
                    WHEN r.PARENT_ARTICLE_ID = %s THEN r.CHILD_ARTICLE_ID
                    ELSE r.PARENT_ARTICLE_ID
                END
            WHERE r.PARENT_ARTICLE_ID = %s OR r.CHILD_ARTICLE_ID = %s
            ORDER BY r.PROXIMITY_SCORE DESC 
            LIMIT %s
            """

            # Same ID used in multiple positions in the query
            self.cursor.execute(query, (
                parent_sku_id,  # CASE display (not strictly needed but kept for clarity)
                parent_sku_id,
                parent_sku_id,
                parent_sku_id,
                parent_sku_id,
                limit,
            ))
            results = self.cursor.fetchall()

            return [
                {
                    "recommended_item": row[0],  # SKU_NAME (human-readable)
                    "score": row[1],            # PROXIMITY_SCORE
                    "rank": i + 1,              # Generate rank based on order
                    "recommended_item_id": row[3]  # SKU_ID (for reference)
                }
                for i, row in enumerate(results)
            ]
            
        except pymysql.MySQLError as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

    def _apply_score_decay(self, current_recommendations_df, decay_factor=0.8):
        """
        Apply score decay to rules that are NOT in the current generation.
        This ensures rules that stop appearing gradually fade out over time.
        
        Args:
            current_recommendations_df: DataFrame with currently generated rules
            decay_factor: Multiplier for decay (default 0.8 = 20% reduction)
        
        Returns:
            Number of rules that were decayed
        """
        try:
            # Build set of current rule pairs (parent, child)
            current_rules = set(
                zip(
                    current_recommendations_df['main_item'],
                    current_recommendations_df['recommended_item']
                )
            )
            
            # Convert to SQL-friendly format
            current_rules_conditions = []
            for parent, child in current_rules:
                current_rules_conditions.append(f"(PARENT_ARTICLE_ID = '{parent}' AND CHILD_ARTICLE_ID = '{child}')")
            
            if not current_rules_conditions:
                logger.info("No current rules to compare against for decay")
                return 0
            
            # Build NOT IN condition - decay all rules NOT in current generation
            not_in_condition = " AND NOT (" + " OR ".join(current_rules_conditions) + ")"
            
            # Update query to decay scores
            decay_query = f"""
            UPDATE {self.recommendations_table}
            SET PROXIMITY_SCORE = PROXIMITY_SCORE * {decay_factor}
            WHERE PROXIMITY_SCORE > 0.001
            {not_in_condition}
            """
            
            self.cursor.execute(decay_query)
            decayed_count = self.cursor.rowcount
            self.connection.commit()
            
            logger.info(f"Applied {decay_factor}x decay to {decayed_count} rules not in current generation")
            return decayed_count
            
        except Exception as e:
            logger.error(f"Error applying score decay: {e}")
            logger.exception("Full traceback:")
            return 0

    # def _filter_invalid_rules(self, recommendations_df):
    #     """
    #     Filter out invalid rules based on business logic:
    #     1. Remove rules where either SKU has MIN_SEGMENT_SIZE = 1
    #     2. Remove rules where one SKU is food (CATEGORY_ID=35) and other is non-food (CATEGORY_ID=1)
    #     """
    #     try:
    #         if len(recommendations_df) == 0:
    #             return recommendations_df
            
    #         initial_count = len(recommendations_df)
            
    #         # Get all unique SKU IDs from the recommendations
    #         all_sku_ids = set(recommendations_df['main_item'].unique()) | set(recommendations_df['recommended_item'].unique())
    #         sku_ids_str = ','.join([f"'{sku_id}'" for sku_id in all_sku_ids])
            
    #         # Fetch SKU metadata from sku_master table
    #         sku_metadata_query = f"""
    #         SELECT 
    #             SKU_ID,
    #             MIN_SEGMENT_SIZE,
    #             CATEGORY
    #         FROM {self.sku_master_table}
    #         WHERE SKU_ID IN ({sku_ids_str})
    #         """
            
    #         sku_metadata_df = pd.read_sql(sku_metadata_query, self.connection)
            
    #         # Create lookup dictionaries
    #         min_segment_size_lookup = dict(zip(sku_metadata_df['SKU_ID'], sku_metadata_df['MIN_SEGMENT_SIZE']))
    #         category_id_lookup = dict(zip(sku_metadata_df['SKU_ID'], sku_metadata_df['CATEGORY']))
            
    #         # Filter 1: Remove rules where either SKU has MIN_SEGMENT_SIZE = 1
    #         def is_valid_segment_size(row):
    #             parent_segment = min_segment_size_lookup.get(row['main_item'], None)
    #             child_segment = min_segment_size_lookup.get(row['recommended_item'], None)
                
    #             # If either has MIN_SEGMENT_SIZE = 1, reject the rule
    #             if parent_segment == 1 or child_segment == 1:
    #                 return False
    #             return True
            
    #         # Filter 2: Remove rules where one is food (35) and other is non-food (1)
    #         def is_valid_category_mix(row):
    #             parent_category = category_id_lookup.get(row['main_item'], None)
    #             child_category = category_id_lookup.get(row['recommended_item'], None)
                
    #             # Check if one is food (35) and the other is non-food (1)
    #             if (parent_category == 35 and child_category == 1) or (parent_category == 1 and child_category == 35):
    #                 return False
    #             return True
            
    #         # Apply both filters
    #         valid_mask = recommendations_df.apply(lambda row: is_valid_segment_size(row) and is_valid_category_mix(row), axis=1)
    #         filtered_df = recommendations_df[valid_mask].copy()
            
    #         removed_count = initial_count - len(filtered_df)
    #         logger.info(f"Rule validation: {initial_count} total rules -> {len(filtered_df)} valid rules (removed {removed_count} invalid rules)")
            
    #         # Log some details about what was filtered
    #         segment_invalid = recommendations_df[~recommendations_df.apply(is_valid_segment_size, axis=1)]
    #         category_invalid = recommendations_df[~recommendations_df.apply(is_valid_category_mix, axis=1)]
            
    #         logger.info(f"  - Removed {len(segment_invalid)} rules due to MIN_SEGMENT_SIZE = 1")
    #         logger.info(f"  - Removed {len(category_invalid)} rules due to food/non-food category mismatch")
            
    #         return filtered_df
            
    #     except Exception as e:
    #         logger.error(f"Error filtering invalid rules: {e}")
    #         logger.exception("Full traceback:")
    #         # Return original dataframe if filtering fails
    #         return recommendations_df
    def _filter_invalid_rules(self, recommendations_df):
        """
        Filter out invalid rules based on business logic:
        1. Remove rules where either SKU has MIN_SEGMENT_SIZE = 1
        2. Keep only rules where both SKUs have the SAME CATEGORY
        """
        try:
            if recommendations_df.empty:
                return recommendations_df

            initial_count = len(recommendations_df)

            # Step 1: Collect all unique SKUs
            all_sku_ids = pd.unique(
                recommendations_df[['main_item', 'recommended_item']].values.ravel()
            )
            sku_ids_str = ",".join([f"'{sku}'" for sku in all_sku_ids])

            # Step 2: Pull SKU metadata
            sku_metadata_query = f"""
                SELECT SKU_ID, MIN_SEGMENT_SIZE, CATEGORY
                FROM {self.sku_master_table}
                WHERE SKU_ID IN ({sku_ids_str})
            """

            sku_df = pd.read_sql(sku_metadata_query, self.connection)
            # sku_df["MIN_SEGMENT_SIZE"] = sku_df["MIN_SEGMENT_SIZE"].astype(int)
            # sku_df["CATEGORY"] = sku_df["CATEGORY"].astype(int)

            # Step 3: Merge metadata for both main_item and recommended_item
            merged = recommendations_df \
                .merge(sku_df.rename(columns={
                    "SKU_ID": "main_item",
                    "MIN_SEGMENT_SIZE": "main_segment",
                    "CATEGORY": "main_category"
                }), on="main_item", how="left") \
                .merge(sku_df.rename(columns={
                    "SKU_ID": "recommended_item",
                    "MIN_SEGMENT_SIZE": "child_segment",
                    "CATEGORY": "child_category"
                }), on="recommended_item", how="left")

            # Step 4: Business rules

            # Rule 1: Neither SKU should have MIN_SEGMENT_SIZE = 1
            mask_segment = (merged["main_segment"] != 1) & (merged["child_segment"] != 1)

            # Rule 2: Both SKUs must be same category (NEW requirement)
            mask_same_category = merged["main_category"] == merged["child_category"]

            # Combined mask
            valid_mask = mask_segment & mask_same_category

            filtered_df = merged[valid_mask][recommendations_df.columns].copy()

            # Logging
            removed = initial_count - len(filtered_df)
            logger.info(f"Rule validation: {initial_count} total → {len(filtered_df)} valid (removed {removed})")

            logger.info(f"  - Removed {(~mask_segment).sum()} due to MIN_SEGMENT_SIZE = 1")
            logger.info(f"  - Removed {(~mask_same_category).sum()} due to category mismatch")

            return filtered_df

        except Exception as e:
            logger.error(f"Error filtering invalid rules: {e}")
            logger.exception("Full traceback:")
            return recommendations_df


    def _ensure_recommendations_table_exists(self):
        """Ensure the recommendations table exists with SKU ID schema"""
        try:
            logger.info(f"Creating/ensuring recommendations table exists: {self.recommendations_table}")
            
            # Create table with SKU ID schema if it doesn't exist
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {self.recommendations_table} (
                SCORE_ID BIGINT NOT NULL AUTO_INCREMENT,
                PARENT_ARTICLE_ID VARCHAR(200) NOT NULL,
                CHILD_ARTICLE_ID VARCHAR(200) NOT NULL,
                PROXIMITY_SCORE DECIMAL(10,3) NULL,
                PRIMARY KEY (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID),
                KEY SCORE_ID_INDEX (SCORE_ID)
            )
            """
            self.cursor.execute(create_table_query)
            logger.info(f"Table {self.recommendations_table} ready with SKU ID schema")
        except pymysql.MySQLError as e:
            logger.error(f"Error creating recommendations table: {e}")
            raise