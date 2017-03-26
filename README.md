# Reddit Approvals Bots
Code for bots that operate [/r/redditapprovals](https://www.reddit.com/r/redditapprovals)


### Activity.py
* Scans the recent comments for the moderators of [/r/redditrequest](https://www.reddit.com/r/redditrequest).
* Builds a table with the three most recent relevant comments made by each mod.
* Comments are only considered relevant if made in the subreddit of [/r/redditrequest](https://www.reddit.com/r/redditrequest) in the past 30 days.

### Approvals.py
* Backend script for database CRUD operations.
* Parses relevant data from each thread submitted to [/r/redditrequest](https://www.reddit.com/r/redditrequest).
* Checks to see if the requester is a moderator of the requested subreddit.
* Stores the date of their request and the date they were made a moderator.

### Calculate.py
* Backend script for database CRUD operations.
* Calculates the mean and median for all approvals in the database.
* Stores the results for other scripts to access.

### Response.py
* Sends a notification to users who submit a request to [/r/redditrequest](https://www.reddit.com/r/redditrequest).
* Informs them of current estimated wait, refers them to [/r/redditapprovals](https://www.reddit.com/r/redditapprovals), tells them how to be blacklisted
* Records the date of the message in the database
* Does not message blacklisted users or users who made a request in the past 60 days

### Blacklist.py
* Monitors the inbox for blacklist requests
* Stores the user in a blacklist table to avoid further messages

---

#### Database Structure
Table: threads
 
 id | author | created_utc | permalink | subreddit | is_mod | date_of_mod | duration
 ---|---|---|---|---|---|---|---
 
 Table: stats
 
 count | mean | median 
 ---|---|---
 
 Table: messages
 
 user | date | status
 ---|---|---
 
