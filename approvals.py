from time import sleep, time
import statistics as sts
import logging
import sqlite3
import praw
import prawcore

reddit = praw.Reddit('AUTHENTICATION')
conn = sqlite3.connect('approvals.db')
cur = conn.cursor()
logger = logging.getLogger('Approvals')
logging.basicConfig(
    filename='log.txt',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s')
cutoff = time() - 60 * 60 * 24 * 30


def main():
    logger.info('Start')
    conn.execute('DELETE FROM threads WHERE created_utc < ?', (cutoff,))
    store_requests()
    check_mod_status()
    calculate_stats()
    logger.info('Complete')


def store_requests():
    """
    Generates id column from db
    Gathers all threads from /r/redditrequests
    Adds new thread to the database and commits once
    """

    ids = {_id[0] for _id in conn.execute('SELECT id FROM threads')}
    for request in request_gen():
        _id, author, created_utc, permalink, subreddit = request
        if _id in ids:
            continue
        cur.execute('INSERT INTO threads VALUES (?,?,?,?,?,?,?,?)', (
            _id, author, created_utc, permalink, subreddit, 0, 0, 0))
    conn.commit()


def request_gen():
    """
    Generates threads from /r/redditrequests
    Yields necessary data from threads that have not been deleted
    """

    try:
        generator = reddit.subreddit('redditrequest').new(limit=None)
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
            if created_utc < cutoff:
                continue
            yield _id, author, created_utc, permalink, subreddit


def sub_from_url(url):
    """
    Parses the requested subreddit from the url
    Example URL: https://www.reddit.com/r/redditrequest/
    """

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
    """
    Generates all entries from the db where is_mod == False
    Checks each entry to see if the requester has been made a mod
    If they are now a mod, the database is updated
    """

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
    """
    Generates all moderators of the subreddit in question
    Return True if the author is a mod and they were made a mod after their request
    They may have been made a mod by an existing mod. Doesn't mean admin approval.
    """

    try:
        mod_gen = reddit.subreddit(subreddit).moderator()
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
    """
    Updates the db to indicate when the person was made a moderator
    Calculates the duration between the request being made and the
    person being made a moderator
    """

    if isinstance(date_of_mod, str):
        duration = 0
    else:
        duration = date_of_mod - created_utc
    cur.execute('UPDATE threads SET is_mod=?, date_of_mod=?, duration=? WHERE id=?', (
        status, date_of_mod, duration, _id
    ))


def calculate_stats():
    """
    Refresh table
    Get all durations and convert float
    Calc mean, median and divide results by num of seconds/day
    Store the values
    """

    cur.execute('DROP TABLE IF EXISTS stats')
    cur.execute('CREATE TABLE IF NOT EXISTS stats(mean, median, stdev, var, min, max, count)')
    dur = [float(d[0]) for d in conn.execute('SELECT duration FROM threads WHERE is_mod=1')]
    count = len(dur)

    days = [(d // (60 * 60 * 24)) for d in dur]
    var = int(sts.variance(days))
    stdev = '{:.3}'.format(var ** .5)

    values = [sts.mean(dur), sts.median(dur), min(dur), max(dur)]
    mean, median, _min, _max = [int(d // (60 * 60 * 24)) for d in values]

    cur.execute('INSERT INTO stats VALUES (?,?,?,?,?,?,?)', (
         mean, median, stdev, var, _min, _max, count))
    conn.commit()


if __name__ == '__main__':
    main()
