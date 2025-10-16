import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import logging

logger = logging.getLogger(__name__)

class ScoringService:
    def __init__(self):
        self.scaler = MinMaxScaler()
    
    def calculate_composite_score(self, rules_df, method="weighted_product"):
        """Calculate composite scores for association rules"""
        
        if rules_df.empty:
            return rules_df
        
        # Create a copy to avoid modifying original
        scored_df = rules_df.copy()
        
        if method == "weighted_product":
            return self._weighted_product_score(scored_df)
        elif method == "weighted_sum":
            return self._weighted_sum_score(scored_df)
        elif method == "normalized_product":
            return self._normalized_product_score(scored_df)
        else:
            raise ValueError(f"Unknown scoring method: {method}")
    
    def calculate_temporal_composite_score(self, rules_df, method="temporal_weighted"):
        """Calculate composite scores with temporal factors"""
        
        if rules_df.empty:
            return rules_df
        
        # Create a copy to avoid modifying original
        scored_df = rules_df.copy()
        
        if method == "temporal_weighted":
            return self._temporal_weighted_score(scored_df)
        elif method == "temporal_trend_focused":
            return self._temporal_trend_focused_score(scored_df)
        elif method == "temporal_stability_focused":
            return self._temporal_stability_focused_score(scored_df)
        else:
            # Fallback to standard scoring
            return self.calculate_composite_score(scored_df, "normalized_product")
    
    def _temporal_weighted_score(self, df, weights=None):
        """Calculate temporal weighted composite score"""
        if weights is None:
            weights = {
                "confidence": 0.25,
                "lift": 0.25,
                "support": 0.15,
                "temporal_stability": 0.20,
                "temporal_trend": 0.15
            }
        
        # Ensure temporal columns exist
        if 'temporal_stability' not in df.columns:
            df['temporal_stability'] = 0.5
        if 'temporal_trend' not in df.columns:
            df['temporal_trend'] = 0.0
        
        # Normalize all metrics to 0-1 scale
        metrics = ['confidence', 'lift', 'support', 'temporal_stability']
        df[metrics] = self.scaler.fit_transform(df[metrics])
        
        # Normalize temporal trend from [-1,1] to [0,1]
        df['temporal_trend_normalized'] = (df['temporal_trend'] + 1) / 2
        
        df['temporal_composite_score'] = (
            df['confidence'] * weights['confidence'] +
            df['lift'] * weights['lift'] +
            df['support'] * weights['support'] +
            df['temporal_stability'] * weights['temporal_stability'] +
            df['temporal_trend_normalized'] * weights['temporal_trend']
        )
        
        logger.info("Applied temporal weighted scoring")
        return df
    
    def _temporal_trend_focused_score(self, df):
        """Score focusing on temporal trends (good for trending products)"""
        if 'temporal_trend' not in df.columns:
            df['temporal_trend'] = 0.0
        
        # Normalize base metrics
        metrics = ['confidence', 'lift', 'support']
        df[metrics] = self.scaler.fit_transform(df[metrics])
        
        # Base score
        base_score = df['confidence'] * df['lift'] * df['support']
        
        # Trend bonus (higher weight for positive trends)
        trend_bonus = np.maximum(0, df['temporal_trend']) * 0.5
        
        df['temporal_composite_score'] = base_score + trend_bonus
        
        logger.info("Applied temporal trend-focused scoring")
        return df
    
    def _temporal_stability_focused_score(self, df):
        """Score focusing on temporal stability (good for consistent patterns)"""
        if 'temporal_stability' not in df.columns:
            df['temporal_stability'] = 0.5
        
        # Normalize base metrics
        metrics = ['confidence', 'lift', 'support', 'temporal_stability']
        df[metrics] = self.scaler.fit_transform(df[metrics])
        
        # Weighted score with high emphasis on stability
        df['temporal_composite_score'] = (
            df['confidence'] * 0.3 +
            df['lift'] * 0.3 +
            df['support'] * 0.2 +
            df['temporal_stability'] * 0.2
        )
        
        logger.info("Applied temporal stability-focused scoring")
        return df
    
    def _weighted_product_score(self, df, weights=None):
        """Calculate weighted product score"""
        if weights is None:
            weights = {"confidence": 0.4, "lift": 0.4, "support": 0.2}
        
        df['composite_score'] = (
            (df['confidence'] ** weights['confidence']) *
            (df['lift'] ** weights['lift']) *
            (df['support'] ** weights['support'])
        )
        
        logger.info("Applied weighted product scoring")
        return df
    
    def _weighted_sum_score(self, df, weights=None):
        """Calculate weighted sum score"""
        if weights is None:
            weights = {"confidence": 0.4, "lift": 0.4, "support": 0.2}
        
        # Normalize metrics to 0-1 scale
        metrics = ['confidence', 'lift', 'support']
        df[metrics] = self.scaler.fit_transform(df[metrics])
        
        df['composite_score'] = (
            df['confidence'] * weights['confidence'] +
            df['lift'] * weights['lift'] +
            df['support'] * weights['support']
        )
        
        logger.info("Applied weighted sum scoring")
        return df
    
    def _normalized_product_score(self, df):
        """Calculate normalized product score"""
        # Normalize metrics to 0-1 scale
        metrics = ['confidence', 'lift', 'support']
        df[metrics] = self.scaler.fit_transform(df[metrics])
        
        df['composite_score'] = df['confidence'] * df['lift'] * df['support']
        
        logger.info("Applied normalized product scoring")
        return df
    
    def rank_recommendations(self, recommendations_df):
        """Add ranking to recommendations"""
        recommendations_df['recommendation_rank'] = (
            recommendations_df.groupby('main_item')['composite_score']
            .rank(method='dense', ascending=False)
            .astype(int)
        )
        
        return recommendations_df