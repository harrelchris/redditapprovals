from time import time
import logging
import sqlite3
import praw
import prawcore

CUTOFF = time() - 60 * 60 * 24 * 60
TARGET_SUB = 'redditrequest'
DESTINATION = 'redditapprovals'
REDDIT = praw.Reddit('AUTHENTICATION')
logger = logging.getLogger('Activity')
logging.basicConfig(
    filename='log.txt',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s')
conn = sqlite3.connect('approvals.db')
c = conn.cursor()


def main():
    conn.execute('DELETE FROM threads WHERE created_utc < ?', (CUTOFF,))
    store_requests()
    check_mod_status()


def store_requests():
    """Called by main()
    Generates id column from db
    Gathers all threads from /r/redditrequests
    Adds new thread to the database and commits once"""

    ids = {_id[0] for _id in conn.execute('SELECT id FROM threads')}
    for request in request_gen():
        _id, author, created_utc, permalink, subreddit = request
        if _id in ids:
            continue
        c.execute('INSERT INTO threads VALUES (?,?,?,?,?,?,?,?)', (
            _id, author, created_utc, permalink, subreddit, 0, 0, 0))
    conn.commit()


def request_gen():
    """Called by store_requests()
    Generates threads from /r/redditrequests
    Yields necessary data from threads that have not been deleted"""

    try:
        generator = REDDIT.subreddit(TARGET_SUB).new(limit=None)
    except Exception as error:
        logger.exception(error)
    else:
        for submission in generator:
            if not submission.author:
                continue
            _id = submission.id
            author = submission.author.name
            created_utc = submission.created_utc
            permalink = submission.permalink
            subreddit = sub_from_url(submission.url)
            if not subreddit:
                continue
            if created_utc < CUTOFF:
                continue
            yield _id, author, created_utc, permalink, subreddit


def sub_from_url(url):
    """Called by request_gen()
    Parses the requested subreddit from the url
    Example URL: https://www.reddit.com/r/redditrequest/"""

    if '/r/' not in url:
        return None
    else:
        parts = url.split('/r/')
    if len(parts) < 2:
        return None
    elif '/' in parts[1]:
        return parts[1].split('/')[0]
    else:
        return parts[1]


def check_mod_status():
    """Called by main()
    Generates all entries from the db where is_mod == False
    Checks each entry to see if the requester has been made a mod
    If they are now a mod, the database is updated"""

    query = 'SELECT id, author, created_utc, subreddit FROM threads WHERE is_mod=0'
    not_mods = {row for row in conn.execute(query)}
    for entry in not_mods:
        _id, author, created_utc, subreddit = entry
        created_utc = float(created_utc)
        date_of_mod = is_mod(author, created_utc, subreddit)
        if not date_of_mod:
            continue
        elif date_of_mod == 'Forbidden':  # Private
            update_status(_id, 2, 'Forbidden', 0)
        elif date_of_mod == 'NotFound':  # Banned
            update_status(_id, 2, 'NotFound', 0)
        elif date_of_mod == 'AlreadyMod':
            update_status(_id, 2, 'AlreadyMod', 0)
        else:
            update_status(_id, 1, date_of_mod, created_utc)
    conn.commit()


def is_mod(author, created_utc, subreddit):
    """Called by check_mod_status()
    Generates all moderators of the subreddit in question
    Return True if the author is a mod and they were made a mod after their request
    They may have been made a mod by an existing mod. Doesn't mean admin approval."""

    try:
        mod_gen = REDDIT.subreddit(subreddit).moderator()
    except prawcore.exceptions.Forbidden:
        return 'Forbidden'
    except prawcore.exceptions.NotFound:
        return 'NotFound'
    except Exception as error:
        logger.exception(error)
    else:
        for mod in mod_gen:
            if not mod.name.lower() == author.lower():
                continue
            elif created_utc > mod.date:
                return 'AlreadyMod'
            else:
                return mod.date
        return False


def update_status(_id, status, date_of_mod, created_utc):
    """Called by check_mod_status()
    Updates the db to indicate when the person was made a moderator
    Calculates the duration between the request being made and the
    person being made a moderator"""

    if isinstance(date_of_mod, str):
        duration = 0
    else:
        duration = date_of_mod - created_utc
    c.execute('UPDATE threads SET is_mod=?, date_of_mod=?, duration=? WHERE id=?', (
        status, date_of_mod, duration, _id
    ))


if __name__ == '__main__':
    main()
    logger.info('Ran Approvals.py')
