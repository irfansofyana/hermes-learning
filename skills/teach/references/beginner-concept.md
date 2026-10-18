# Reference lesson: combining averages

Original illustrative authoring fixture. Learner: beginner who can add and divide. This is one possible composition, not a required template or topic source.

Weak approach: “Averages are fundamental statistical tools with many applications. In this lesson we will explore their importance.” Followed by a definition, repeated conclusion, and “What is an average?”

The complete payload below starts with a decision, exposes the hidden group sizes, and asks the learner to apply the same reasoning to changed data.

```json
{
  "content": "Two teams report their average delivery time. Team A delivered 2 orders in 10 minutes each. Team B delivered 8 orders in 20 minutes each. What was the average across all 10 orders?\n\nAveraging the two reported numbers gives `(10 + 20) / 2 = 15` minutes. That gives each team equal weight, even though Team B handled four times as many orders.\n\nRecover each team's total time before combining them:\n\n| Team | Orders | Average time | Total time |\n| --- | --- | --- | --- |\n| A | 2 | 10 minutes | 2 × 10 = 20 minutes |\n| B | 8 | 20 minutes | 8 × 20 = 160 minutes |\n\nThe combined total is `20 + 160 = 180` minutes across `2 + 8 = 10` orders. Divide to get `180 / 10 = 18` minutes per order. This is a weighted average: each reported average contributes according to its number of orders.\n\nThis calculation combines the reported time per order; it does not tell us elapsed wall-clock time if deliveries overlap. If both teams had handled the same number of orders, averaging the two averages would give the correct combined result.",
  "source_ids": [],
  "teaching": {
    "outcome": "Calculate a combined mean from group means and group sizes.",
    "prerequisites": ["Add, multiply and divide whole numbers."],
    "misconception": "Averaging group averages gives each group equal weight; the combined mean must account for how many observations each group contains."
  },
  "practice": {
    "kind": "explanation",
    "prompt": "Team A now handles 6 orders averaging 10 minutes. Team B handles 4 averaging 20 minutes. Find the combined average and explain why it shifts toward Team A's time.",
    "criteria": ["Calculates 6 × 10 + 4 × 20 = 140 total minutes over 10 orders, giving 14 minutes per order.", "Explains that Team A now contributes more observations, so its average receives more weight."],
    "hints": ["Recover the total time for each team first.", "Divide the combined total by the combined number of orders."],
    "explanation": "Team A contributes 60 minutes and Team B contributes 80, so the combined total is 140 minutes. There are 10 orders; the mean is 14 minutes per order. More orders now have the shorter time, which pulls the combined mean toward 10 minutes."
  }
}
```

Reviewer notes: the table performs a calculation that prose would make harder to inspect. The exercise changes the weighting; it does not request a definition already printed in the explanation. The lesson retains a condition about overlapping work because deleting it could change the interpretation of the numbers. Metadata and practice are separate from the narrative for the existing UI.
