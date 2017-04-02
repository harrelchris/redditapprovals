from time import sleep, time
import logging
import sqlite3
import praw

reddit = praw.Reddit('AUTHENTICATION')
conn = sqlite3.connect('approvals.db')
logger = logging.getLogger('Mailer')
logging.basicConfig(
    filename='log.txt',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s')


def main():
    logger.info('Start')
    start = time()
    sleep(5)
    while True:
        try:
            for submission in reddit.subreddit('redditrequest').stream.submissions():
                if submission.created_utc < start:
                    continue
                handle(submission.author.name.lower())
        except Exception as error:
            logger.exception(error)
            sleep(30)


def handle(author):
    if author in {n[0] for n in conn.execute('SELECT user FROM blacklist')}:
        return None
    else:

        message = """
The current backlog for /r/redditrequest moderators is approximately {} days.

Please visit /r/redditapprovals for more information.

---

^^This ^^is ^^a ^^bot. ^^You ^^will ^^never ^^be ^^messaged ^^about ^^this ^^again.
        """.format([s for s in conn.execute('SELECT * FROM stats')][0][0])

        try:
            reddit.redditor(author).message('Estimated Wait Time', message)
        except Exception as error:
            logger.exception(error)
        else:
            conn.execute('INSERT INTO blacklist VALUES (?)', (author,))
            conn.commit()
            return


if __name__ == '__main__':
    main()
