"""
KNN Similarity Engine for Episodic Memory
Finds past trades similar to current setup for risk adjustment.
"""
import numpy as np
from typing import List, Tuple
from sklearn.neighbors import NearestNeighbors
from mind.memory import TradeEpisode

class SimilarityEngine:
    def __init__(self, k: int = 5):
        self.k = k
        self.model = NearestNeighbors(n_neighbors=k, metric='euclidean')

    def find_similar(self, current: TradeEpisode, 
                     candidates: List[TradeEpisode]) -> List[Tuple[TradeEpisode, float]]:
        """
        Returns: List of (episode, distance) tuples, sorted by similarity.
        """
        if len(candidates) < 3:
            return []

        # Build feature matrix
        X = np.array([c.feature_vector() for c in candidates])
        query = current.feature_vector().reshape(1, -1)

        # Fit and query
        self.model.fit(X)
        distances, indices = self.model.kneighbors(query)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            results.append((candidates[idx], float(dist)))

        return results

    def suggest_stake_adjustment(self, similar: List[Tuple[TradeEpisode, float]], 
                                  base_stake: float) -> Tuple[float, str]:
        """
        Suggest stake size based on historical performance of similar setups.
        Returns: (adjusted_stake, reasoning)
        """
        if not similar:
            return base_stake, "No similar history. Using base stake."

        wins = sum(1 for ep, _ in similar if ep.result_status == "WIN")
        total = len(similar)
        win_rate = wins / total if total > 0 else 0

        # Kelly Criterion Lite
        if win_rate > 0.6:
            adjustment = 1.25
            reason = f"Similar setups won {win_rate*100:.0f}%. Increasing stake 25%."
        elif win_rate > 0.45:
            adjustment = 1.0
            reason = f"Similar setups won {win_rate*100:.0f}%. Standard stake."
        elif win_rate > 0.3:
            adjustment = 0.75
            reason = f"Similar setups won {win_rate*100:.0f}%. Reducing stake 25%."
        else:
            adjustment = 0.5
            reason = f"Similar setups won {win_rate*100:.0f}%. Halving stake for protection."

        adjusted = round(base_stake * adjustment, 2)
        return adjusted, reason
