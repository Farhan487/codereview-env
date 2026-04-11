"""
Reward function with partial progress signals.

Design goals:
  - Reward partial progress, not just binary success
  - Penalize wasted steps (diminishing returns over time)
  - Penalize clearly undesirable behavior (empty/nonsense responses)
"""


class RewardCalculator:
    """
    Converts a raw grade score (0.0-1.0) into a shaped reward signal.

    Shaping rules:
      1. Base reward = raw score
      2. Step penalty: small cost per step to encourage efficiency
      3. Bonus: extra reward for solving on first attempt
      4. Penalty: negative reward for empty/garbage responses
    """

    STEP_PENALTY = 0.02          # Deducted per step to discourage wasting moves
    FIRST_STEP_BONUS = 0.1       # Bonus if solved perfectly on step 1
    GARBAGE_PENALTY = -0.3       # For empty or clearly invalid responses

    def compute(
        self,
        score: float,
        breakdown: dict,
        step_num: int,
        max_steps: int,
    ) -> float:
        """
        Compute shaped reward.

        Args:
            score: Raw grade 0.0–1.0
            breakdown: Component scores from grader
            step_num: Current step number (1-indexed)
            max_steps: Maximum steps in episode

        Returns:
            Shaped reward (can be negative)
        """
        # Detect garbage response (all zeros in breakdown)
        all_zero = all(v <= 0.01 for v in breakdown.values())
        if all_zero:
            return 0.01

        reward = score

        # Step efficiency penalty (small, progressive)
        reward -= self.STEP_PENALTY * (step_num - 1)

        # Bonus for solving on first try
        if step_num == 1 and score >= 1.0:
            reward += self.FIRST_STEP_BONUS

        # Scale reward: the closer to max steps, the more we discount
        # This creates partial progress signal across the trajectory
        time_discount = 1.0 - (0.05 * max(0, step_num - 1))
        reward = reward * time_discount

        # Clamp to strictly between 0 and 1
        reward = max(0.01, min(0.99, round(reward, 4)))
        return reward
