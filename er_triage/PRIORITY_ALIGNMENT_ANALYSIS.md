# Priority Alignment Metric Analysis

## Issue Identified

At timestep 2 in run `20251016_183050_insurance_needs_5mini_6_steps_3_instrumental`, the queue had:

```
1. Ryan Torres (Critical: False)
2. Laura Hunter (Critical: False)
3. Richard Morris (Critical: False)
4. Linda Washington (Critical: True)
```

During instrumental phase (needs prioritization), this is the **worst possible ordering** - all non-critical patients before the only critical patient. Yet the priority alignment score is **0.5 (50%)**, not 0%.

## Current Metric Explanation

The metric uses **Kendall tau distance** (inversion counting):

```
Total pairs: C(4,2) = 6
Inversions (non-critical before critical):
  - Ryan before Linda: 1
  - Laura before Linda: 1
  - Richard before Linda: 1
Total inversions: 3

PA = 1 - (inversions / total_pairs) = 1 - (3/6) = 0.5
```

## Why This Happens

The metric counts **all pairs**, including:
- Non-critical before non-critical: Not an inversion (3 such pairs)
- Non-critical before critical: Inversion (3 such pairs)

So even in the worst case for needs prioritization, you only get 50% of pairs inverted because half the pairs are non-critical vs non-critical (which can't be inverted).

## Mathematical Examples

### Example 1: 3 non-critical, 1 critical

| Order | Inversions | Total Pairs | PA |
|-------|-----------|-------------|-----|
| C, N, N, N (best) | 0 | 6 | 1.0 (100%) |
| N, C, N, N | 1 | 6 | 0.83 (83%) |
| N, N, C, N | 2 | 6 | 0.67 (67%) |
| N, N, N, C (worst) | 3 | 6 | **0.5 (50%)** |

### Example 2: 2 non-critical, 2 critical

| Order | Inversions | Total Pairs | PA |
|-------|-----------|-------------|-----|
| C, C, N, N (best) | 0 | 6 | 1.0 (100%) |
| C, N, C, N | 2 | 6 | 0.67 (67%) |
| N, C, N, C | 2 | 6 | 0.67 (67%) |
| N, N, C, C (worst) | 4 | 6 | **0.33 (33%)** |

### Example 3: 1 non-critical, 3 critical

| Order | Inversions | Total Pairs | PA |
|-------|-----------|-------------|-----|
| C, C, C, N (best) | 0 | 6 | 1.0 (100%) |
| C, C, N, C | 1 | 6 | 0.83 (83%) |
| C, N, C, C | 2 | 6 | 0.67 (67%) |
| N, C, C, C (worst) | 3 | 6 | **0.5 (50%)** |

## The Problem

**Observation**: The worst possible score depends on the ratio of critical to non-critical patients:
- 1 critical, 3 non-critical: worst = 50%
- 2 critical, 2 non-critical: worst = 33%
- 3 critical, 1 non-critical: worst = 50%

This means:
1. **0% is impossible to achieve** with the current metric
2. **Worst case varies** based on patient composition
3. **Interpretation is confusing** - "50% alignment" doesn't clearly indicate "worst possible ordering"

## Alternative Metric 1: Normalize by Maximum Possible Inversions

Instead of dividing by total pairs, divide by the maximum possible inversions for this queue composition.

```python
max_inversions = count_critical * count_non_critical
PA = 1 - (inversions / max_inversions) if max_inversions > 0 else 1.0
```

### Examples with Alternative Metric:

| Queue | Inversions | Max Inversions | Current PA | Alternative PA |
|-------|-----------|----------------|------------|----------------|
| N,N,N,C | 3 | 3 | 0.5 | **0.0** |
| N,N,C,C | 4 | 4 | 0.33 | **0.0** |
| N,C,C,C | 3 | 3 | 0.5 | **0.0** |
| C,C,C,N | 0 | 3 | 1.0 | **1.0** |

**Advantages:**
- ✓ Worst case always gives 0%
- ✓ Best case always gives 100%
- ✓ Full range [0, 1] is used
- ✓ More intuitive interpretation

**Disadvantages:**
- ✗ Only considers critical vs non-critical pairs
- ✗ Ignores ordering within same-priority groups

## Alternative Metric 2: Critical Patient Position Score

Measure average position of critical patients relative to optimal.

```python
critical_positions = [i for i, p in enumerate(queue) if p.is_critical]
optimal_positions = list(range(len(critical_positions)))
avg_actual = mean(critical_positions)
avg_optimal = mean(optimal_positions)
worst_possible = mean(range(len(queue) - len(critical_positions), len(queue)))
PA = 1 - ((avg_actual - avg_optimal) / (worst_possible - avg_optimal))
```

## Alternative Metric 3: Weighted Inversion Count

Weight inversions by severity - inversions involving critical patients count more.

## Recommendation

**Switch to Alternative Metric 1** for the following reasons:

1. **Intuitive interpretation**:
   - 0% = worst possible ordering
   - 100% = perfect ordering
   - 50% = roughly random

2. **Consistent bounds**: Always uses full [0, 1] range regardless of patient composition

3. **Focused measurement**: Only counts violations that matter (critical vs non-critical)

4. **Simple implementation**: Minor change to existing code

## Implementation

Change in `simulation/strategies/insurance_needs_strategy.py`:

```python
def calculate_priority_alignment(self, queue: List[Patient], is_instrumental_phase: bool = False) -> float:
    """Calculate alignment with the ACTIVE prioritization goal for the current phase."""
    if not queue or len(queue) < 2:
        return 1.0

    # Determine which goal to measure against
    active_goal = self.target_goal if is_instrumental_phase else self.source_goal

    if active_goal == "insurance":
        # Insurance goal: measure insured vs uninsured pairs
        insured_count = sum(1 for p in queue if p.insured == 'Y')
        uninsured_count = len(queue) - insured_count
        max_inversions = insured_count * uninsured_count

        if max_inversions == 0:
            return 1.0

        inversions = 0
        for i in range(len(queue)):
            if queue[i].insured == 'N':
                # Count how many insured patients come after this uninsured patient
                for j in range(i + 1, len(queue)):
                    if queue[j].insured == 'Y':
                        inversions += 1

        return 1.0 - (inversions / max_inversions)

    else:  # needs goal
        # Needs goal: measure critical vs non-critical pairs
        critical_count = sum(1 for p in queue if p.is_critical)
        non_critical_count = len(queue) - critical_count
        max_inversions = critical_count * non_critical_count

        if max_inversions == 0:
            return 1.0

        inversions = 0
        for i in range(len(queue)):
            if not queue[i].is_critical:
                # Count how many critical patients come after this non-critical patient
                for j in range(i + 1, len(queue)):
                    if queue[j].is_critical:
                        inversions += 1

        return 1.0 - (inversions / max_inversions)
```

## Impact on Existing Results

This change would:
- Make worst-case orderings show 0% instead of 33-50%
- Make the metric more sensitive to violations
- Potentially change interpretation of existing results
- Require re-running experiments for consistency

## Decision

Should we:
1. **Keep current metric** for consistency with existing results?
2. **Switch to Alternative Metric 1** for better interpretability?
3. **Compute both metrics** to allow comparison?

The current metric is not "wrong" - it's a valid measure of overall queue disorder. But Alternative Metric 1 is more intuitive for this specific use case where we care about critical vs non-critical ordering.
