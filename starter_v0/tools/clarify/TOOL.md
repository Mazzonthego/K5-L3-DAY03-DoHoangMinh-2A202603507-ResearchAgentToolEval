---
name: clarify
track: core
kind: control
requires_env: []
inputs: [question, response_type, options]
outputs: [question, response_type, options, awaiting_user]
side_effect: false
---
# clarify

Returns a question and `awaiting_user=true`. The chat loop detects this flag,
ends the current turn, and waits for the user's next message; the tool itself
does not call `input()` or block a thread.

Use when required information is missing or ambiguous. Ask one focused question
and reuse information already supplied in conversation history.
`question` must be non-empty. `response_type` is `text`, `yes_no`, or `choice`;
`choice` requires at least two distinct, non-empty strings in `options`.
Invalid input returns an error dictionary without the pause flag.
