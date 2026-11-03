// Turn the model's text into clean, validated fields.
const ticket = $('Support ticket in').first().json.body || {};
const msg = $input.first().json.choices?.[0]?.message || {};
// Reasoning models may leave content empty or wrap thoughts in <think> tags.
const raw = msg.content || msg.reasoning_content || '';

// Pull out the last complete JSON object, ignoring thinking and code fences.
function extractJson(text) {
  const cleaned = text.replace(/<think>[\s\S]*?<\/think>/gi, '').replace(/```json|```/g, '').trim();
  const end = cleaned.lastIndexOf('}');
  for (let start = cleaned.lastIndexOf('{', end); start >= 0; start = cleaned.lastIndexOf('{', start - 1)) {
    try { return JSON.parse(cleaned.slice(start, end + 1)); } catch (e) {}
  }
  throw new Error('no JSON object found');
}

let ai;
try {
  ai = extractJson(raw);
  if (typeof ai.category !== 'string') throw new Error('missing category');
} catch (e) {
  // Never trust a broken answer: send it to a person instead.
  ai = { category: 'other', priority: 'high', sentiment: 'unknown', order_id: null,
         summary: 'Model returned invalid JSON, routed to a human.', draft_reply: '', needs_human: true };
}

const allowed = ['order_status', 'refund_return', 'product_question', 'complaint', 'spam', 'other'];
if (!allowed.includes(ai.category)) ai.category = 'other';
if (!['low', 'medium', 'high'].includes(ai.priority)) ai.priority = 'medium';

// Business rule on top of the model: money and anger always go to a human.
ai.needs_human = Boolean(ai.needs_human) || ['refund_return', 'complaint'].includes(ai.category) || ai.priority === 'high';

return [{ json: {
  ticket_id: ticket.ticket_id || `T-${Date.now()}`,
  customer_email: ticket.email || null,
  subject: ticket.subject || '',
  ...ai,
  processed_at: new Date().toISOString(),
} }];
