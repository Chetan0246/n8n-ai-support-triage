# AI Support Ticket Triage (n8n + LLM)

An n8n workflow that reads an incoming customer support message for a Shopify-style store, classifies it with an LLM, pulls out the order number, drafts a reply, and sends anything risky to the team on Slack.

## Flow

```
Webhook (POST /support-triage)
   -> HTTP Request: LLM classify (OpenAI-compatible chat/completions, NVIDIA NIM)
   -> Code: parse + validate JSON, apply business rules
   -> IF needs_human?
        yes -> Slack alert (incoming webhook) -> respond
        no  -> respond with triage JSON
```

Output fields: category (order_status, refund_return, product_question, complaint, spam, other), priority, sentiment, order_id, summary, needs_human, draft_reply.

## Run it in about 15 minutes

1. Start n8n: `npx n8n` (or `docker run -it --rm -p 5678:5678 n8nio/n8n`), open http://localhost:5678.
2. Workflows > Import from file > `ai-support-triage.n8n.json`.
3. Open "Classify with LLM" > Credential > new **Header Auth**: Name `Authorization`, Value `Bearer <your NVIDIA API key>` (free at build.nvidia.com).
4. Optional: put a Slack incoming-webhook URL in "Alert team on Slack". If you skip it, the node fails softly and the flow still answers.
5. Click "Test workflow", then send a ticket:

```bash
curl -X POST http://localhost:5678/webhook-test/support-triage \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"T-1001","email":"priya@example.com","subject":"Where is my order??","message":"Order #4821 was supposed to arrive Friday. It is Monday. Second time this has happened. Fix it or refund me."}'
```

Real result from the model for that ticket:

```json
{
  "ticket_id": "T-1001",
  "customer_email": "priya@example.com",
  "subject": "Where is my order??",
  "category": "complaint",
  "priority": "medium",
  "sentiment": "negative",
  "order_id": "4821",
  "summary": "Customer reports order #4821 delayed past estimated delivery date and expresses frustration over recurring issue.",
  "needs_human": true,
  "draft_reply": "We're looking into order #4821 and will confirm the delivery status shortly. Please let us know if you'd like assistance with a refund or return.",
  "processed_at": "2026-11-03T10:33:14.149Z"
}
```

Or run all three sample tickets (an angry delay, a shipping question, spam): 
```bash
./scripts/send-samples.sh http://localhost:5678/webhook/support-triage
```
The full triage results for all three sample tickets are saved in [`samples/results.json`](samples/results.json).

### Sample Triage Results Summary

| Ticket ID | Subject | Category | Priority | Needs Human | Extracted Order ID |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **T-1001** | *Where is my order??* | `complaint` | `medium` | `true` | `4821` |
| **T-1002** | *Shipping to Canada* | `product_question` | `low` | `false` | `null` |
| **T-1003** | *Rank #1 on Google in 7 days* | `spam` | `low` | `false` | `null` |

## Design choices to talk about in an interview

- **LLM via plain HTTP, OpenAI-compatible.** Swap the URL and model to move between NVIDIA, OpenAI, Groq or a local llama.cpp server with no other changes.
- **Never trust raw model output.** The Code node strips code fences, parses JSON, checks the category against an allow-list, and if parsing fails it routes to a human instead of guessing.
- **Business rules sit on top of the model.** Refunds, complaints and high priority always go to a human, even if the model said otherwise.
- **Reliability.** The LLM call retries 3 times with a 2 s wait; Slack failure doesn't break the response.
- **Reasoning models need room.** Nemotron 3.5 Lightning thinks before answering, so max_tokens is 2000; with 500 the answer came back empty.

## Next steps (good to mention)

- Swap the webhook for a Gmail or Shopify trigger.
- Look up the order in the Shopify Admin API by order_id and put the real tracking status in the draft.
- Log every ticket to Google Sheets or HubSpot; create a Gmail draft for routine tickets.

## Files

- `ai-support-triage.n8n.json`: the workflow to import
- `samples/tickets.json`: three test tickets
- `samples/results.json`: verified triage outputs from all three test tickets
- `scripts/send-samples.sh`: posts the samples to the webhook
- `scripts/parse-node.js`: the Code node's parsing logic on its own
- `scripts/build.py`: regenerates the workflow JSON
