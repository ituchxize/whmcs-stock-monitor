# Telegram Setup Guide

## Overview

This guide explains how to set up Telegram notifications for the WHMCS Stock Monitor.

## Creating a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Start a chat and send `/newbot`
3. Follow the prompts to:
   - Choose a name for your bot (e.g., "WHMCS Stock Monitor")
   - Choose a username (must end in 'bot', e.g., "whmcs_stock_monitor_bot")
4. BotFather will provide your **Bot Token** - save this securely

## Getting Your Chat ID

### Method 1: Using the GetUpdates API

1. Send a message to your bot
2. Visit this URL in your browser (replace `YOUR_BOT_TOKEN`):
   ```
   https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates
   ```
3. Look for the `"chat":{"id":` field in the response
4. Copy the chat ID (it will be a number)

### Method 2: Using @userinfobot

1. Search for **@userinfobot** in Telegram
2. Start a chat with the bot
3. Your user ID will be displayed
4. Use this as your chat ID

### Method 3: For Group Chats

1. Add your bot to the group
2. Send a message in the group
3. Use the GetUpdates API method above
4. Look for the group chat ID (it will be a negative number)

## Configuring the Application

Add your Telegram credentials to the `.env` file:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

## Testing the Connection

Test your Telegram bot configuration:

```bash
# This will be implemented in future iterations
python scripts/test_telegram.py
```

## Notification Types

The monitor sends the following types of notifications:

### Restock Notifications

Sent when a product is restocked:

```
🔔 Stock Restocked

Product: VPS Hosting - Basic
Change: +5 units (from 0 to 5)
Time: 2024-01-15 14:30:00 UTC
```

### Purchase Notifications

Sent when a product is purchased:

```
🛒 Stock Decreased

Product: VPS Hosting - Basic
Change: -1 unit (from 5 to 4)
Time: 2024-01-15 14:35:00 UTC
```

### Low Stock Alerts

Sent when stock falls below threshold:

```
⚠️ Low Stock Alert

Product: VPS Hosting - Basic
Current Stock: 2 units
Threshold: 5 units
Time: 2024-01-15 14:40:00 UTC
```

## Customizing Notifications

### Message Format

Notification messages can be customized by modifying the notification service.

### Notification Preferences

Configure which notifications to receive per product:

- `notify_on_restock`: Receive notifications when stock increases
- `notify_on_purchase`: Receive notifications when stock decreases
- `notify_on_stock_low`: Receive notifications for low stock
- `low_stock_threshold`: Set the threshold for low stock alerts

## Advanced Configuration

### Multiple Chat IDs

To send notifications to multiple chats (future feature):

```env
TELEGRAM_CHAT_ID=123456789,987654321,456789123
```

### Quiet Hours

Configure quiet hours to avoid notifications during specific times (future feature):

```env
TELEGRAM_QUIET_HOURS_START=22:00
TELEGRAM_QUIET_HOURS_END=08:00
TELEGRAM_QUIET_HOURS_TIMEZONE=UTC
```

### Message Threading

Enable message threading for group chats (future feature):

```env
TELEGRAM_USE_THREADS=true
```

## Troubleshooting

### Bot Not Responding

- Verify bot token is correct
- Check bot is not blocked by Telegram
- Ensure bot has not been deleted

### Messages Not Received

- Verify chat ID is correct
- Check you haven't blocked the bot
- For groups, ensure bot has permission to send messages

### Permission Errors

- For groups, bot needs to be added as admin or have send message permissions
- Check privacy settings in group

### Rate Limiting

Telegram has rate limits:
- 30 messages per second per bot
- 20 messages per minute per chat

The application handles rate limiting automatically.

## Security Best Practices

1. **Bot Token**: Keep your bot token secret, never commit to version control
2. **Chat ID**: Only share with trusted users
3. **Bot Permissions**: Use least privilege principle
4. **Regular Audits**: Periodically review bot message history

## Additional Features

### Bot Commands (Future)

The bot will support the following commands:

- `/status` - Get current monitoring status
- `/list` - List all monitored products
- `/pause [product_id]` - Pause monitoring for a product
- `/resume [product_id]` - Resume monitoring for a product
- `/help` - Get help information

### Interactive Buttons (Future)

Notifications will include inline buttons for quick actions:

- View product details
- Pause monitoring
- View history

## Resources

- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
- [BotFather Commands](https://core.telegram.org/bots#6-botfather)
- [python-telegram-bot Library](https://python-telegram-bot.readthedocs.io/)
