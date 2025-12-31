# ntfy.sh Push Notifications Setup

Get critical notifications on your phone when the Jean Claude coordinator escalates questions! 📱

## Coordinator Pattern

Jean Claude uses a **coordinator pattern** for agent communication:

1. **Agent → Coordinator (Claude Code)** - Agents send questions to the main Claude Code instance
2. **Coordinator Triages** - Claude Code answers most questions on your behalf
3. **Coordinator → Human (You)** - Only escalates to you via ntfy when truly needed

This means you only get pinged for critical decisions, not routine agent questions!

## Quick Start (5 minutes)

### 1. Install ntfy App on Your Phone

**iOS:** https://apps.apple.com/us/app/ntfy/id1625396347
**Android:** https://play.google.com/store/apps/details?id=io.heckel.ntfy
**Web:** https://ntfy.sh/app

### 2. Choose Unique Topic Names (Two Topics)

You need **two topics** for bidirectional communication:
1. **Escalation topic**: Jean Claude sends critical questions to you
2. **Response topic**: You send answers back to Jean Claude

Your topics are like private channels. Make them unique and hard to guess:

✅ Good: `jean-claude-laboeuf-escalations-x9k2p` and `jean-claude-laboeuf-responses-a8f3e`
✅ Good: `jc-to-human-8f4a3b2e` and `human-to-jc-9d5b2c1f`
❌ Bad: `jean-claude` (too common, others might use it)
❌ Bad: `test` (definitely taken)

**Pro tip:** Generate random ones:
```bash
echo "Escalation: jean-claude-escalate-$(openssl rand -hex 6)"
echo "Response:   jean-claude-respond-$(openssl rand -hex 6)"
```

### 3. Subscribe in the ntfy App

1. Open the ntfy app on your phone
2. Tap the **"+"** button
3. Enter your **escalation topic** (e.g., `jean-claude-escalate-x9k2p`)
4. Tap "Subscribe"
5. Repeat for your **response topic** (e.g., `jean-claude-respond-a8f3e`)

You're now listening for escalations AND able to send responses!

### 4. Configure Jean Claude

Set **both** environment variables in your shell:

```bash
# Add to your ~/.zshrc or ~/.bashrc
export JEAN_CLAUDE_NTFY_TOPIC="your-escalation-topic"
export JEAN_CLAUDE_NTFY_RESPONSE_TOPIC="your-response-topic"

# Then reload your shell
source ~/.zshrc  # or source ~/.bashrc
```

**OR** set them just for the current session:
```bash
export JEAN_CLAUDE_NTFY_TOPIC="jean-claude-escalate-x9k2p"
export JEAN_CLAUDE_NTFY_RESPONSE_TOPIC="jean-claude-respond-a8f3e"
```

### 5. Test It!

```bash
uv run python test_ntfy_notifications.py
```

You should get TWO push notifications on your phone within ~10 seconds! 🎉

## What Notifications You'll Get

### 🤖 Coordinator Escalation (Priority 5 - MAX)
- Sent when the coordinator (Claude Code) needs your decision
- Only for critical questions that require human judgment
- Tags: 🤖 ⚠️ 🆘
- Includes the agent's question and why it needs your input

**Examples of escalations:**
- Business/product decisions
- Security or privacy questions
- Multiple valid approaches (need your preference)
- Coordinator is uncertain about the correct solution

**What coordinator handles automatically:**
- Code implementation questions
- Test failure diagnosis
- Project convention guidance
- Straightforward technical decisions

## How to Respond to Escalated Questions

### Option 1: Respond from Your Phone 📱 (NEW!)

When you get a "🤖 Coordinator Escalation" notification:

1. **Open the ntfy app** on your phone
2. **Find the response topic** (e.g., `jean-claude-respond-a8f3e`)
3. **Tap to send a message** in this format:
   ```
   {workflow-id}: Your response here
   ```

   Example:
   ```
   coordinator-test-001: Use Redis for caching - we have it in production
   ```

4. **Send the message**
5. **Jean Claude polls the topic** every 2 seconds and writes your response to OUTBOX
6. **Agent receives it** and continues!

**Format details:**
- Must include workflow ID (shown in escalation message)
- Colon separates workflow ID from response
- Response can be multiple sentences

### Option 2: Respond from Terminal (Classic)

If you prefer terminal or have complex responses:

1. **SSH to your machine** or open a terminal
2. **Navigate to your project directory**
3. **Write your response** to OUTBOX:
   ```bash
   echo '{
     "from_agent": "user",
     "to_agent": "coder-agent",
     "type": "response",
     "subject": "Re: Your question",
     "body": "Your answer here",
     "priority": "NORMAL",
     "awaiting_response": false,
     "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'"
   }' | jq '.' > agents/{workflow-id}/OUTBOX/response-$(date +%s).json
   ```

4. **Agent receives it** within 2 seconds and continues!

**Note:** Most agent questions are handled automatically by the coordinator.
You only get notified for critical decisions!

## Privacy & Security

- **No account needed** - topic names are the security mechanism
- **Choose unpredictable topics** - anyone who knows your topic can subscribe
- **Messages are public** - don't use ntfy.sh for sensitive data
- **Use .env files** - don't commit your topic to git

Add to `.gitignore`:
```
.env
.env.local
```

Add to `.env`:
```bash
JEAN_CLAUDE_NTFY_TOPIC=your-secret-topic-here
```

Load it:
```bash
source .env
```

## Advanced: Custom ntfy Server

Running your own ntfy server? Set the base URL:

```bash
export JEAN_CLAUDE_NTFY_URL="https://ntfy.your-domain.com"
```

(Currently not implemented - future enhancement)

## Troubleshooting

**Not receiving notifications?**

1. Check you're subscribed to the right topic in the app
2. Verify environment variable is set: `echo $JEAN_CLAUDE_NTFY_TOPIC`
3. Test with curl:
   ```bash
   curl -d "Test from command line" https://ntfy.sh/your-topic-name
   ```
4. Check app notification permissions in iOS/Android settings

**Notifications going to Notification Center instead of popping up?**

- iOS: Settings → Notifications → ntfy → Set to "Immediate Delivery"
- Android: App settings → Notifications → Set to "High Importance"

## Why ntfy.sh?

- **Free and open source** - no vendor lock-in
- **Works everywhere** - iOS, Android, Web, CLI
- **No registration** - just pick a topic and go
- **Simple** - single HTTP POST, no OAuth
- **Self-hostable** - run your own server if you want

Perfect for human-in-the-loop AI workflows! 🤖🔔
