# Class Generation Logic - Full Explanation

## Overview
The `generate_class_tree()` function generates a tree of classes for a game, where each base class (Warrior, Priest, Mage, Thief, Wanderer) gets 50 generated classes connected in a hierarchical tree structure.

## Main Loop Condition
```python
while not all_bases_have_enough() and iteration < max_iterations:
```

**Key Issue**: The loop continues until `all_bases_have_enough()` returns True, which checks if each base class has 50 classes. However, `classes_generated` is incremented but never used in the loop condition - only `all_bases_have_enough()` matters.

## Step-by-Step Generation Process

### 1. Base Class Selection (Lines 119-170)

**Priority Order:**
1. **Minimum Requirements First**: If any base class needs minimum requirements (1 Common, 1 Uncommon, 2 Higher tier direct children), those are prioritized using round-robin.
2. **Weighted Distribution**: After requirements are met, base classes are selected using weighted selection based on how many classes they still need.

**Problem Area**: The `classes_per_base` calculation (lines 130-134) counts from `generated_classes` list, but this happens INSIDE the loop, so it's recalculated every iteration. This is inefficient but should work.

### 2. Generation Type Decision (Lines 186-269)

**Three Types of Generation:**

#### A. Minimum Requirements (Lines 188-208)
- **When**: `needs_common`, `needs_uncommon`, or `needs_higher` is True
- **What**: Forces a direct child (level 1) of the base class with specific rarity
- **Sets**: `must_be_direct_child = True`, `target_rarity = <specific>`

#### B. Common Path Extension (Lines 217-269)
- **When**: `needs_common_path` is True (Common path has < 10 classes)
- **What**: Extends the Common-only path with probability 60-75% (depending on completion)
- **Sets**: `build_common_path_this_iteration = True`, `common_path_parent`, `common_path_level`

#### C. Normal Generation (Lines 271-429)
- **When**: Minimum requirements met AND not building Common path
- **What**: Selects a parent from existing classes, calculates level/rarity naturally
- **Parent Selection**: Weighted selection favoring lower levels, with 2-3x boost for Common path nodes

### 3. Parent and Level Determination (Lines 271-429)

**Three Paths:**

#### Path A: Direct Child (Lines 272-276)
- `must_be_direct_child = True`
- `level = 1`, `rarity = target_rarity`, `parent_class = base_class_key`

#### Path B: Common Path (Lines 277-282)
- `build_common_path_this_iteration = True`
- Uses pre-calculated `common_path_parent` and `common_path_level`
- `rarity = "Common"` (forced)

#### Path C: Normal Generation (Lines 283-429)
- Selects parent from `class_tree_by_base[base_class_key]`
- Calculates level: `parent_level + 1` (or +2 with 20% chance)
- Enforces rarity progression: child rarity >= parent rarity
- Special rule: After Unique rarity, child MUST be strictly higher

### 4. Class Generation (Lines 460-614)

**Process:**
1. Generate class using `generate_class()` (line 480)
2. **Skip if duplicate ID** (lines 483-486) - `continue` (doesn't increment `classes_generated`)
3. **Skip if already has parent** (lines 489-492) - `continue` (doesn't increment `classes_generated`)
4. Override rarity/level with calculated values (lines 496-497)
5. Set `base_class` attribute (line 527)
6. Add to `generated_classes` list (lines 542-545)
7. Add to `class_tree_by_base` (lines 562-567)
8. Update direct children counts if applicable (lines 571-579)
9. Add to Common path if applicable (lines 586-608)
10. **Increment `classes_generated`** (line 610)

## Critical Issues Identified

### Issue 1: Loop Condition Mismatch
- **Line 116**: Loop condition is `not all_bases_have_enough()`
- **Line 610**: `classes_generated` is incremented
- **Problem**: `classes_generated` is never checked in the loop condition, only `all_bases_have_enough()`. This means the loop could theoretically run forever if `all_bases_have_enough()` never returns True.

### Issue 2: Skip Conditions Don't Increment Counter
- **Lines 483-486, 489-492**: When duplicates or existing parents are found, the code does `continue` without incrementing `classes_generated`
- **Problem**: This is correct behavior, but it means many iterations might be "wasted" on skips, potentially hitting `max_iterations` before reaching 50 per base.

### Issue 3: `classes_per_base` Recalculation
- **Lines 130-134**: `classes_per_base` is recalculated every iteration
- **Problem**: This is inefficient but shouldn't cause the issue. However, it counts from `generated_classes` which should be accurate.

### Issue 4: Base Class Selection After Requirements Met
- **Lines 142-170**: After requirements are met, base class selection uses weighted selection
- **Potential Issue**: If one base class keeps getting selected (due to randomness), others might not reach 50. The weighted selection should help, but might not be aggressive enough.

### Issue 5: Common Path Probability
- **Lines 228, 246**: Common path extension uses probability (70% start, 60-75% extend)
- **Problem**: This means Common path building is not guaranteed, which could slow down generation for that base class.

## Expected Behavior

1. **First Phase**: Generate minimum requirements (4 classes per base = 20 total)
2. **Second Phase**: Generate remaining classes (46 per base = 230 total) using weighted selection
3. **Total**: 250 classes (50 per base × 5 bases)

## Actual Behavior (Based on User Report)

- Only 12-15 classes per base class are being generated
- This suggests the loop is stopping early or classes are being skipped too often

## Potential Root Causes

1. **Max Iterations Hit**: `max_iterations = num_classes * 10 = 2500`. If many classes are skipped, we might hit this limit before reaching 50 per base.

2. **Duplicate Generation**: If `generate_class()` is producing duplicate IDs frequently, many iterations are wasted.

3. **Parent Conflicts**: If classes are being marked as "already has parent" incorrectly, they're being skipped.

4. **Base Class Selection**: If the weighted selection isn't working correctly, some base classes might be getting more classes than others, and the loop might exit early if one base reaches 50 while others don't.

5. **Exception Handling**: If exceptions are being thrown and caught (line 612), those iterations are lost.

## Recommendations for Debugging

1. **Add Logging**: Log when classes are skipped and why (duplicate, existing parent, exception)
2. **Track Skip Counts**: Count how many iterations result in skips vs successful generations
3. **Verify `all_bases_have_enough()`**: Add logging to show the count per base class each iteration
4. **Check Exception Rate**: See if exceptions are being thrown frequently
5. **Verify Base Class Assignment**: Ensure `class_data["base_class"]` is being set correctly (line 527)

## Suggested Fixes

1. **Increase Max Iterations**: Change from `num_classes * 10` to `num_classes * 20` or higher
2. **Make Common Path Guaranteed**: Instead of probability-based, make Common path extension guaranteed when incomplete
3. **More Aggressive Base Selection**: When a base class is far below target, give it 100% selection chance
4. **Fix Loop Condition**: Consider using `classes_generated` as a secondary check or remove it entirely if not needed
5. **Add Progress Logging**: Log every 10 iterations to see what's happening

