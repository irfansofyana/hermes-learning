# Reference lesson: finding the first match

Original illustrative authoring fixture. Learner: familiar with Python lists, loops and zero-based indexing. Code and traces describe expected behavior; no execution occurred.

Weak approach: paste a function, paraphrase each line, then ask the learner to paste it back. That leaves the early return and absent-target behavior unexplained.

```json
{
  "content": "Suppose a list contains the same name twice, and you need the first position. Return as soon as you find a match:\n\n```python\ndef first_match(items, target):\n    for index, item in enumerate(items):\n        if item == target:\n            return index\n    return None\n```\n\n`enumerate` supplies each position and value. Trace `first_match(['oak', 'pine', 'oak'], 'oak')`: the first iteration has `index = 0` and `item = 'oak'`. The comparison succeeds, so `return 0` ends the whole function. The loop never reaches the second `'oak'`.\n\nNow trace `first_match(['oak', 'pine', 'oak'], 'pine')`:\n\n| index | item | Equal to target? | Next action |\n| --- | --- | --- | --- |\n| 0 | oak | No | Continue the loop |\n| 1 | pine | Yes | Return 1 and end the function |\n\n`return None` sits after the loop. The function reaches it only if no iteration returned a position. This also handles an empty list because the loop then has no iterations.\n\nA valid first position is `0`, which Python treats as false in a condition. Check `result is not None` when deciding whether a match exists; `if result` would misclassify a match at the front.",
  "source_ids": [],
  "teaching": {
    "outcome": "Predict the return value of a first-match search, including index zero and absent targets.",
    "prerequisites": ["Read Python for loops, lists and zero-based indexes."],
    "misconception": "A return inside a loop ends the function, not just the current iteration."
  },
  "practice": {
    "kind": "code",
    "prompt": "For items = ['elm', 'ash'], a caller stores first_match(items, 'maple') in result, then uses `if result is not None: print(items[result])`. Predict result and whether anything prints. Explain the control flow; you do not need to execute it.",
    "criteria": ["Identifies that the function returns None after both comparisons fail.", "Explains that the caller's condition is false, so it does not index the list or print a match."],
    "hints": ["Does either loop iteration reach return index?", "Trace the line after the loop, then the caller's condition."],
    "explanation": "Neither 'elm' nor 'ash' equals 'maple'. The loop finishes and returns None. The caller checks None is not None, which is false, so it neither indexes items nor prints anything."
  }
}
```

Reviewer notes: focus on decisions and state changes rather than narrating syntax the learner already knows. The example demonstrates early return, and the exercise asks about the other exit path. Keep `None`, index zero and truthiness distinctions intact during prose editing. A diagram would add little to this short trace, so none is required.
