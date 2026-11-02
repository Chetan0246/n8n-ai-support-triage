// Turn the model's text into clean, validated fields.
const ticket = $('Support ticket in').first().json.body || {};
const raw = $input.first().json.choices?.[0]?.message?.content || '';

let ai;
try {
  const cleaned = raw.replace(/```json|```/g, '').trim();
  ai = JSON.parse(cleaned.slice(cleaned.indexOf('{'), cleaned.lastIndexOf('}') + 1));
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