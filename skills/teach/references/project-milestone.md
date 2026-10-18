# Reference lesson: reject invalid purchases

Original illustrative authoring fixture. Earlier milestone in a small purchase-only log:

```python
purchases = [{'label': 'tea', 'cents': 300}, {'label': 'paper', 'cents': 500}]

def summarize(purchases):
    return sum(row['cents'] for row in purchases)
```

Assumptions supplied by the project: rows have a label and an integer number of cents. Purchases must have a positive amount. Refunds are outside this log's scope. No persistence, currency conversion or general accounting behavior is promised.

Weak approach: replace the log with a database-backed accounting service, rename its fields, and give a long list of future features. That abandons the prior milestone rather than extending it.

```json
{
  "content": "Our purchase-only log currently adds every amount. A row with `cents = 0` should be reported for correction instead of joining the total. We'll keep `purchases` and its existing row shape, and extend `summarize` to return the total plus rejected rows.\n\n```python\ndef summarize(purchases):\n    total = 0\n    rejected = []\n    for row in purchases:\n        if row['cents'] <= 0:\n            rejected.append(row)\n            continue\n        total += row['cents']\n    return total, rejected\n```\n\nThe early `continue` skips addition for that row while allowing later purchases to be checked. The return shape changes from one integer to a pair; update the existing caller to unpack it:\n\n```python\ntotal, rejected = summarize(purchases)\nprint(total)\nprint(rejected)\n```\n\nTo inspect the behavior, try these illustrative inputs:\n\n```python\npurchases = [\n    {'label': 'tea', 'cents': 300},\n    {'label': 'unknown', 'cents': 0},\n    {'label': 'paper', 'cents': 500},\n]\n```\n\nExpected trace: tea adds 300, unknown joins `rejected` without changing the total, and paper adds 500. The function should return `(800, [{'label': 'unknown', 'cents': 0}])`. This is predicted behavior, not an executed test result.\n\nThis milestone checks the amount rule for the existing row contract. Missing keys or non-integer amounts still need separate handling if the project later accepts raw user input. Negative amounts are invalid for this purchase-only log; a future refund feature would need its own rule.",
  "source_ids": [],
  "teaching": {
    "outcome": "Extend the existing purchase summary to exclude and report nonpositive amounts.",
    "prerequisites": ["Read the earlier summarize function and Python lists, dictionaries and loops."],
    "misconception": "Rejecting one row should not stop the whole summary; continue skips that row and keeps processing later purchases."
  },
  "practice": {
    "kind": "project",
    "prompt": "Use the same summarize interface with these rows: snack at -50 cents, notebook at 250 cents, and empty at 0 cents. Give the expected total and rejected rows, then show how the caller can print the rejected count. You may predict the result without running code.",
    "criteria": ["Keeps only notebook in the total, giving 250 cents.", "Reports snack and empty as the two rejected rows in their original order.", "Unpacks total, rejected and uses len(rejected), respecting the changed return interface."],
    "hints": ["Trace the <= 0 decision separately for each row.", "The function now returns two values; unpack them before counting rejected rows."],
    "explanation": "The -50 and 0 amounts both satisfy <= 0, so rejected contains the snack row followed by the empty row. Only notebook contributes to total, giving 250 cents. The caller can use `total, rejected = summarize(purchases)` followed by `print(len(rejected))`, whose expected output is 2."
  }
}
```

Reviewer notes: the lesson preserves the project's domain and data names, explains a changed caller contract, gives an inspectable expected result, and bounds its claims. The exercise adds negative and zero amounts without introducing unneeded infrastructure. For a real supplied project, cite the actual approved earlier material rather than copying this fictional log.
