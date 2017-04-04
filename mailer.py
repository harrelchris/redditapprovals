from time import sleep, time
import logging
import sqlite3
import praw
import prawcore

reddit = praw.Reddit('AUTHENTICATION')
conn = sqlite3.connect('approvals.db')
logger = logging.getLogger('Mailer')
logging.basicConfig(
    filename='log.txt',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s')
target_sub = 'redditrequest'


# TODO Add handling for WARNING: 502 status
def main():
    logger.info('Start')
    sleep(5)
    prime_mods()
    while True:
        try:
            for submission in reddit.subreddit(target_sub).stream.submissions():
                if time() - submission.created_utc > 60 * 60 * 24 * 2:
                    continue
                handle(submission.author.name.lower())
        except prawcore.exceptions.RequestException:
            continue
        except prawcore.exceptions.ServerError:
            continue
        except Exception as error:
            logger.exception(error)
            sleep(30)


def prime_mods():
    try:
        for mod in reddit.subreddit(target_sub).moderator():
            mod = mod.name.lower()
            db = conn.execute('SELECT EXISTS(SELECT 1 FROM blacklist WHERE user=(?) LIMIT 1)',
                              (mod,))
            if db.fetchone()[0]:
                continue
            else:
                conn.execute('INSERT INTO blacklist VALUES (?)', (mod,))
                conn.commit()
    except prawcore.exceptions.RequestException:
        pass
    except prawcore.exceptions.ServerError:
        pass
    except Exception as error:
        logger.exception(error)


def handle(author):
    db = conn.execute('SELECT EXISTS(SELECT 1 FROM blacklist WHERE user=(?) LIMIT 1)',
                      (author,))
    if db.fetchone()[0]:
        return
    else:

        message = """
The current backlog for /r/redditrequest moderators is approximately {} days.

Please visit /r/redditapprovals for more information.

---

^^This ^^is ^^a ^^bot. ^^You ^^will ^^never ^^be ^^messaged ^^about ^^this ^^again.
        """.format([s for s in conn.execute('SELECT * FROM stats')][0][0])

        try:
            reddit.redditor(author).message('Estimated Wait Time', message)
        except prawcore.exceptions.RequestException:
            pass
        except prawcore.exceptions.ServerError:
            pass
        except Exception as error:
            logger.exception(error)
        else:
            conn.execute('INSERT INTO blacklist VALUES (?)', (author,))
            conn.commit()
            return


if __name__ == '__main__':
    main()
