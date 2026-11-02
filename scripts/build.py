import json, os, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SYS = """You are the support-triage agent for a Shopify store. Read the customer message and reply with ONLY a JSON object, no prose, with these keys:
category: one of order_status, refund_return, product_question, complaint, spam, other
priority: low, medium or high
sentiment: positive, neutral or negative
order_id: the order number as a string, or null
summary: one sentence for the support team
needs_human: true if a refund, angry customer, legal threat or anything you are unsure about
draft_reply: a short, polite reply to the customer that promises nothing you cannot verify"""
parse_js = open(os.path.join(HERE, 'parse-node.js')).read()
body_expr = "={{ JSON.stringify({ model: 'nvidia/nemotron-3.5-lightning-30b-a3b', temperature: 0.2, max_tokens: 2000, messages: [ { role: 'system', content: " + json.dumps(SYS) + " }, { role: 'user', content: 'Subject: ' + ($json.body.subject || '') + '\\nFrom: ' + ($json.body.email || '') + '\\n\\n' + ($json.body.message || '') } ] }) }}"
slack_expr = "={{ JSON.stringify({ text: ':rotating_light: *' + $json.priority.toUpperCase() + '* ' + $json.category + ' from ' + $json.customer_email + (($json.order_id) ? ' (order #' + $json.order_id + ')' : '') + '\\n' + $json.summary + '\\n*Suggested reply:* ' + $json.draft_reply }) }}"
def nid(): return str(uuid.uuid4())
nodes=[
 {"parameters":{"httpMethod":"POST","path":"support-triage","responseMode":"responseNode","options":{}},
  "id":nid(),"name":"Support ticket in","type":"n8n-nodes-base.webhook","typeVersion":2,"position":[0,300],"webhookId":nid()},
 {"parameters":{"method":"POST","url":"https://integrate.api.nvidia.com/v1/chat/completions","authentication":"genericCredentialType","genericAuthType":"httpHeaderAuth","sendBody":True,"specifyBody":"json","jsonBody":body_expr,"options":{"timeout":90000}},
  "id":nid(),"name":"Classify with LLM","type":"n8n-nodes-base.httpRequest","typeVersion":4.2,"position":[240,300],"retryOnFail":True,"maxTries":3,"waitBetweenTries":2000},
 {"parameters":{"jsCode":parse_js},"id":nid(),"name":"Parse and validate","type":"n8n-nodes-base.code","typeVersion":2,"position":[480,300]},
 {"parameters":{"conditions":{"options":{"caseSensitive":True,"leftValue":"","typeValidation":"loose"},"conditions":[{"id":nid(),"leftValue":"={{ $json.needs_human }}","rightValue":"","operator":{"type":"boolean","operation":"true","singleValue":True}}],"combinator":"and"},"options":{}},
  "id":nid(),"name":"Needs a human?","type":"n8n-nodes-base.if","typeVersion":2,"position":[720,300]},
 {"parameters":{"method":"POST","url":"https://hooks.slack.com/services/REPLACE/WITH/YOURS","sendBody":True,"specifyBody":"json","jsonBody":slack_expr,"options":{}},
  "id":nid(),"name":"Alert team on Slack","type":"n8n-nodes-base.httpRequest","typeVersion":4.2,"position":[960,180],"onError":"continueRegularOutput"},
 {"parameters":{"respondWith":"json","responseBody":"={{ JSON.stringify($('Parse and validate').first().json) }}","options":{}},
  "id":nid(),"name":"Return triage result","type":"n8n-nodes-base.respondToWebhook","typeVersion":1.1,"position":[1200,300]},
]
N=lambda n:{"node":n,"type":"main","index":0}
conn={
 "Support ticket in":{"main":[[N("Classify with LLM")]]},
 "Classify with LLM":{"main":[[N("Parse and validate")]]},
 "Parse and validate":{"main":[[N("Needs a human?")]]},
 "Needs a human?":{"main":[[N("Alert team on Slack")],[N("Return triage result")]]},
 "Alert team on Slack":{"main":[[N("Return triage result")]]},
}
wf={"name":"AI Support Ticket Triage (Shopify)","nodes":nodes,"connections":conn,"active":False,"settings":{"executionOrder":"v1"},"pinData":{}}
json.dump(wf, open(os.path.join(ROOT, 'ai-support-triage.n8n.json'), 'w'), indent=2)
print('wrote ai-support-triage.n8n.json')
