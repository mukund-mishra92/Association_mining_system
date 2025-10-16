import mysql.connector
from mysql.connector import Error
import pandas as pd
from app.utils.config import config
import logging

logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=config.DB_HOST,
                user=config.DB_USER,
                password=config.DB_PASSWORD,
                database=config.DB_NAME
            )
            self.cursor = self.connection.cursor()
            logger.info("Database connection established")
            return True
        except Error as e:
            logger.error(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        logger.info("Database connection closed")
    
    def fetch_order_data(self, days_back=None):
        """Fetch order data from database"""
        try:
            # Fixed query to fetch both SKU IDs and names
            query = f"""
            SELECT 
                o.ORDER_ID,
                o.ARTICLE_ID,
                s.SKU_NAME,
                o.INSERTED_TIMESTAMP,
                DATEDIFF(CURDATE(), DATE(o.INSERTED_TIMESTAMP)) as days_ago
            FROM {config.ORDER_TABLE} o
            JOIN {config.SKU_MASTER_TABLE} s ON o.ARTICLE_ID = s.SKU_ID
            WHERE s.SKU_NAME IS NOT NULL
            """
            
            if days_back:
                query += f" AND o.INSERTED_TIMESTAMP >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)"
            
            query += " ORDER BY o.INSERTED_TIMESTAMP DESC"
            
            df = pd.read_sql(query, self.connection)
            
            # Create order_date from INSERTED_TIMESTAMP (same as your code)
            df['order_date'] = pd.to_datetime(df['INSERTED_TIMESTAMP']).dt.date
            
            logger.info(f"Fetched {len(df)} order records")
            return df
        
        except Error as e:
            logger.error(f"Error fetching order data: {e}")
            return None
    
    def save_recommendations(self, recommendations_df):
        """Save recommendations to database using your schema:
        PARENT_ARTICLE_ID, CHILD_ARTICLE_ID, PROXIMITY_SCORE"""
        try:
            logger.info(f"Attempting to save {len(recommendations_df)} recommendations")
            
            # Ensure the recommendations table exists
            self._ensure_recommendations_table_exists()
            
            # Clear existing recommendations
            self.cursor.execute(f"DELETE FROM {config.RECOMMENDATIONS_TABLE}")
            logger.info("Cleared existing recommendations")
            
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
                logger.info(f"Normalized scores: {min_score:.3f}-{max_score:.3f} → 0.001-0.999")
            
            # Insert new recommendations using your simplified schema with duplicate handling
            insert_query = f"""
            INSERT IGNORE INTO {config.RECOMMENDATIONS_TABLE} 
            (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID, PROXIMITY_SCORE)
            VALUES (%s, %s, %s)
            """
            
            inserted_count = 0
            for idx, (_, row) in enumerate(recommendations_df_sorted.iterrows()):
                try:
                    self.cursor.execute(insert_query, (
                        row['main_item'],              # PARENT_ARTICLE_ID - now using SKU ID instead of name
                        row['recommended_item'],       # CHILD_ARTICLE_ID - now using SKU ID instead of name
                        float(normalized_scores[idx])  # NORMALIZED PROXIMITY_SCORE (0.001-0.999)
                    ))
                    if self.cursor.rowcount > 0:  # Only count actual insertions
                        inserted_count += 1
                except Exception as e:
                    logger.error(f"Error inserting row: {e}")
                    continue
            
            self.connection.commit()
            logger.info(f"Successfully saved {inserted_count} recommendations to database")
            return True
            
        except Error as e:
            logger.error(f"Error saving recommendations: {e}")
            return False

    def get_recommendations(self, item_name, limit=10):
        """Get recommendations for a specific item using your schema"""
        try:
            # Ensure the recommendations table exists
            self._ensure_recommendations_table_exists()
            
            query = f"""
            SELECT CHILD_ARTICLE_ID, PROXIMITY_SCORE, SCORE_ID
            FROM {config.RECOMMENDATIONS_TABLE} 
            WHERE PARENT_ARTICLE_ID = %s 
            ORDER BY PROXIMITY_SCORE DESC 
            LIMIT %s
            """
            
            self.cursor.execute(query, (item_name, limit))
            results = self.cursor.fetchall()
            
            return [
                {
                    "recommended_item": row[0],  # CHILD_ARTICLE_ID
                    "score": row[1],            # PROXIMITY_SCORE
                    "rank": i + 1               # Generate rank based on order
                }
                for i, row in enumerate(results)
            ]
            
        except Error as e:
            logger.error(f"Error getting recommendations: {e}")
            return []

    def _ensure_recommendations_table_exists(self):
        """Ensure the recommendations table exists with SKU ID schema"""
        try:
            # Drop existing table to ensure correct schema
            drop_table_query = f"DROP TABLE IF EXISTS {config.RECOMMENDATIONS_TABLE}"
            self.cursor.execute(drop_table_query)
            logger.info(f"Dropped existing table {config.RECOMMENDATIONS_TABLE}")
            
            # Create table with SKU ID schema
            create_table_query = f"""
            CREATE TABLE {config.RECOMMENDATIONS_TABLE} (
                SCORE_ID BIGINT NOT NULL AUTO_INCREMENT,
                PARENT_ARTICLE_ID VARCHAR(200) NOT NULL,
                CHILD_ARTICLE_ID VARCHAR(200) NOT NULL,
                PROXIMITY_SCORE DECIMAL(10,3) NULL,
                PRIMARY KEY (PARENT_ARTICLE_ID, CHILD_ARTICLE_ID),
                KEY SCORE_ID_INDEX (SCORE_ID)
            )
            """
            self.cursor.execute(create_table_query)
            logger.info(f"Created table {config.RECOMMENDATIONS_TABLE} with SKU ID schema")
        except Error as e:
            logger.error(f"Error creating recommendations table: {e}")
            raise