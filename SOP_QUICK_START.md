# Dynamic SOP Injection - Quick Start Guide

## What Changed?

Instead of putting detailed tool procedures in the system prompt, they're now stored in the knowledge base and injected dynamically based on what the user is asking about.

## Setup Steps

### 1. Reload the Knowledge Base

**CRITICAL:** You must run this to load the new SOPs:

```bash
python qdrant/vector_load_kb.py
```

This loads the new agent-facing SOPs from `chunks.json` into Qdrant.

### 2. Test the Implementation

```bash
python test_sop_injection.py
```

This verifies:
- Tool detection is working
- SOPs are being injected
- Caching is functioning
- Integration structure is correct

### 3. Test with Real Conversations

Start the app:
```bash
streamlit run app.py
```

Try these test cases:

#### Test Case 1: Partial Return (The Bug We Fixed)
```
You: "I need to return the keyboard from order 123"
```

**Expected behavior:**
1. Agent asks for order details or checks order
2. Agent sees multiple items in order
3. Agent asks: "Which specific item would you like to return?"
4. Agent uses `product_ids` parameter when calling `initiate_return`
5. Only the keyboard is returned, not all items

#### Test Case 2: Full Order Return
```
You: "I want to return everything from order 456"
```

**Expected behavior:**
1. Agent checks order
2. Agent confirms: "You want to return all items?"
3. Agent calls `initiate_return` WITHOUT `product_ids` parameter
4. All items are returned

#### Test Case 3: Order Placement
```
You: "I'd like to buy a wireless mouse"
```

**Expected behavior:**
1. Agent searches products
2. Agent calls `draft_order` first to validate info
3. Agent asks for missing information progressively
4. Agent calls `create_order` only after draft confirms ready

## How to Verify It's Working

### Check Logs

When you chat with the agent, look for these log messages:

```
INFO - Found and cached SOP for initiate_return
INFO - Found and cached SOP for order_status
INFO - Injected 2 SOP(s) into conversation
```

### Check Behavior

The agent should:
- ✅ Ask for specific items when order has multiple products
- ✅ Use `product_ids` parameter for partial returns
- ✅ Check order status before initiating returns
- ✅ Use `draft_order` before `create_order`
- ✅ Follow structured procedures for each tool

## Adding New SOPs

When you add a new tool or need to update procedures:

### 1. Edit `qdrant/chunks.json`

Add a new chunk:
```json
{
    "id": "agent-sop-your-tool-name",
    "audience": "agent",
    "doc_type": "sop",
    "product_id": null,
    "category": null,
    "title": "your_tool_name Tool - Standard Operating Procedure",
    "tags": ["agent", "sop", "your-tool-name"],
    "content": "PROCEDURE: your_tool_name\n\nSTEP 1: ...\nSTEP 2: ..."
}
```

### 2. Update Detection Logic (if needed)

If the tool needs special keyword detection, edit `chatbot/agent.py`:

```python
def _detect_likely_tools(self, user_message: str) -> List[str]:
    # Add your keywords
    if any(word in message_lower for word in ['your', 'keywords']):
        likely_tools.append('your_tool_name')
```

### 3. Reload Knowledge Base

```bash
python qdrant/vector_load_kb.py
```

### 4. Clear SOP Cache (if testing immediately)

The agent caches SOPs per instance. Restart the app to clear cache or:

```python
agent.sop_cache.clear()  # In your code
```

## Troubleshooting

### SOPs Not Being Injected

**Problem:** Logs don't show "Injected X SOP(s)"

**Solutions:**
1. Check knowledge base was reloaded: `python qdrant/vector_load_kb.py`
2. Verify chunk exists in `chunks.json` with correct structure
3. Check `audience='agent'` and `doc_type='sop'`
4. Try exact search: `agent.tools.vector_store.search_by_text("agent-sop-initiate-return")`

### Agent Not Following SOPs

**Problem:** SOPs are injected but agent doesn't follow them

**Solutions:**
1. Make SOP content more explicit and actionable
2. Use imperative language: "MUST", "REQUIRED", "ALWAYS"
3. Include clear examples in SOP
4. Add consequences: "If you don't do X, then Y will happen"
5. Check system prompt isn't conflicting with SOPs

### Wrong SOPs Injected

**Problem:** Irrelevant SOPs are being included

**Solutions:**
1. Refine keywords in `_detect_likely_tools()`
2. Make SOP IDs more specific
3. Add more specific tags to chunks
4. Adjust search limit (currently `limit=1`)

### Performance Issues

**Problem:** Slow response times

**Solutions:**
1. SOP caching is already implemented (check `agent.sop_cache`)
2. Reduce number of SOPs per conversation
3. Keep SOP content concise
4. Consider caching at application level

## Benefits Recap

✅ **Scalable**: Add 100 tools without bloating system prompt
✅ **Maintainable**: Update procedures without code changes
✅ **Token Efficient**: Only relevant SOPs loaded per conversation
✅ **Cached**: SOPs cached after first retrieval
✅ **Auditable**: Logs show which SOPs were used

## Next Steps

1. **Monitor logs** during real usage to see which SOPs are injected
2. **Gather feedback** on agent behavior following SOPs
3. **Iterate on SOP content** based on failures or edge cases
4. **Add metrics** to track SOP effectiveness
5. **Consider A/B testing** different SOP versions

## Files Modified

- `qdrant/chunks.json` - Added 6 new agent SOPs
- `chatbot/prompts.py` - Simplified system prompt to reference KB
- `chatbot/agent.py` - Added dynamic SOP injection logic
- `SOP_IMPLEMENTATION.md` - Detailed documentation
- `test_sop_injection.py` - Test suite for validation

## Questions?

Check the full documentation: `SOP_IMPLEMENTATION.md`
