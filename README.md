# Reddit Approvals Bots

### Code for bots that operate [/r/redditapprovals](https://www.reddit.com/r/redditapprovals)

---

[![Python](https://img.shields.io/badge/Python-3+-blue.svg?style=plastic)](https://www.python.org/downloads/)
[![Praw](https://img.shields.io/badge/Praw-4-blue.svg?style=plastic)](https://github.com/praw-dev/praw)

### Activity.py
* Scans the recent comments for the moderators of [/r/redditrequest](https://www.reddit.com/r/redditrequest).
* Builds a table with the three most recent relevant comments made by each mod.
* Comments are only considered relevant if made in the subreddit of [/r/redditrequest](https://www.reddit.com/r/redditrequest) in the past 30 days.
* Creates a thread on [/r/redditapprovals](https://www.reddit.com/r/redditapprovals).
* Operated daily.

### Approvals.py
* Backend script for database CRUD operations.
* Parses relevant data from each thread submitted to [/r/redditrequest](https://www.reddit.com/r/redditrequest).
* Checks to see if the requester is a moderator of the requested subreddit.
* Stores the date of their request and the date they were made a moderator.
* Calculates the stats for all approvals in the database.
* Stores the results for other scripts to access.
* Operated daily.

### Mailer.py
* Sends a notification to users who submit a request to [/r/redditrequest](https://www.reddit.com/r/redditrequest).
* Informs them of current estimated wait, refers them to [/r/redditapprovals](https://www.reddit.com/r/redditapprovals).
* Records the user in the database to avoid future messages
* Operated perpetually.
