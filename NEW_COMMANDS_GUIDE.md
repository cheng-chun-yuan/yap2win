# New Commands Guide: /leaderboard and /reward

## 🎉 New Features Added!

Your bot now has two new commands that users can use during active events:

### 🏆 `/leaderboard` Command

**What it does:**
- Shows current rankings for active events
- Displays top 10 participants with points
- Shows medals for top 3 (🥇🥈🥉)
- Includes your position if you're not in top 10

**When to use:**
- Only works in groups where bot is listening
- Only shows data when there's an active event
- Perfect for checking your ranking during competitions

**Example output:**
```
🏆 LEADERBOARD

Event Type: Pool
Total Reward: 50,000
Participants: 15

🥇 Alice: 45.2 points
🥈 Bob: 38.7 points
🥉 Charlie: 32.1 points
4. David: 28.9 points
5. Eve: 25.3 points
...
```

### 🏆 `/reward` Command

**What it does:**
- Shows detailed event information
- Displays reward distribution
- Shows time remaining
- Explains how to participate

**When to use:**
- Only works in groups where bot is listening
- Only shows data when there's an active event
- Great for new participants to understand the event

**Example output:**
```
🏆 REWARD EVENT

Type: Pool
Total Reward: 50,000
Participants: 15
Time Remaining: 2d 5h 30m

💰 Pool Distribution
Each participant will receive: 3,333.33

⏰ Event Timeline
Started: 2024-01-15 14:30
Ends: 2024-01-18 20:00

💬 How to Participate
Just chat normally! Your messages will be scored automatically.
Use /leaderboard to see current rankings.
```

## 🎯 How Users Can Use These Commands

### During Active Events:
1. **Check rankings**: `/leaderboard`
2. **See event info**: `/reward`
3. **Monitor progress**: Use both commands regularly

### For Pool Events:
- `/reward` shows how much each person will get
- `/leaderboard` shows who's participating

### For Rank Events:
- `/reward` shows prize distribution (1st, 2nd, 3rd place amounts)
- `/leaderboard` shows current rankings with medals

## 🔧 Technical Features

### Smart Display:
- **Medals for top 3**: 🥇🥈🥉
- **Time formatting**: Shows days, hours, minutes remaining
- **User position**: Shows your rank if not in top 10
- **Participant count**: Shows total participants

### Error Handling:
- **No active event**: "No active events in this group"
- **No participants**: "No participants yet. Start chatting!"
- **Wrong group**: "This command only works in groups where the bot is listening"
- **Event ended**: "Event has ended! Results will be announced soon"

### Privacy Features:
- **Group-only**: Commands only work in groups (not private chat)
- **Listening groups only**: Only works where bot is active
- **Event-specific**: Only shows data for current active events

## 🚀 Ready to Test!

Your bot is now running with the new commands. Users can:

1. **Join a group** where the bot is listening
2. **Wait for an admin** to start a reward event
3. **Start chatting** to earn points
4. **Use `/leaderboard`** to see rankings
5. **Use `/reward`** to see event details

The commands will automatically show relevant information based on the event type (pool vs rank) and current status!

## 📱 User Experience

### Benefits:
- **Real-time updates**: See current rankings anytime
- **Clear information**: Understand event rules and rewards
- **Motivation**: See your position and progress
- **Easy to use**: Simple commands, no complex syntax

### Mobile Friendly:
- **Short commands**: Easy to type on mobile
- **Clear formatting**: Readable on small screens
- **Quick access**: Get info without scrolling through chat

Your users will love being able to check their progress and event information with these simple commands! 🎉 