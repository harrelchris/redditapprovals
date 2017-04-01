import logging
import sqlite3
import sys
import praw

TARGET_SUB = 'pylet'
REDDIT = praw.Reddit('AUTHENTICATION')
CONN = sqlite3.connect('approvals.db')
CUR = CONN.cursor()
LOGGER = logging.getLogger('Mailer')
logging.basicConfig(
    filename='log.txt',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s')
MESSAGE = """
The current backlog for /r/redditrequest moderators is approximately {} days.

Please visit /r/redditapprovals for more information.

---

^^This ^^is ^^a ^^bot. ^^You ^^will ^^never ^^be ^^messaged ^^about ^^this ^^again.
""".format([s for s in CONN.execute('SELECT * FROM stats')][0][0])


def main():
    generator = REDDIT.subreddit(TARGET_SUB).stream.submissions()
    try:
        for submission in generator:
            handle(submission.author.name.lower())
    except Exception as error:
        LOGGER.exception(error)
        sys.exit()


def handle(author):
    if author in {n[0] for n in CONN.execute('SELECT user FROM blacklist')}:
        return None
    else:
        try:
            REDDIT.redditor(author).message('Estimated Wait Time', MESSAGE)
        except Exception as error:
            LOGGER.exception(error)
            sys.exit()
        else:
            CONN.execute('INSERT INTO blacklist VALUES (?)', (author,))
            CONN.commit()


def build_db():
    CONN.execute('CREATE TABLE IF NOT EXISTS blacklist (user)')
    try:
        mod_gen = REDDIT.subreddit(TARGET_SUB).moderator()
    except Exception as error:
        LOGGER.exception(error)
        sys.exit()
    else:
        existing = {n[0] for n in CONN.execute('SELECT user FROM blacklist')}
        for mod in mod_gen:
            if mod in existing:
                continue
            CONN.execute('INSERT INTO blacklist VALUES (?)', (mod.name.lower(),))
        CONN.commit()


if __name__ == '__main__':
    build_db()
    main()
