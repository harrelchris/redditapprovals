from time import gmtime, strftime, time
import logging
import sqlite3
import praw

reddit = praw.Reddit('AUTHENTICATION')
conn = sqlite3.connect('approvals.db')
logger = logging.getLogger('Activity')
logging.basicConfig(
    filename='log.txt',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s')
target_sub = 'redditrequest'
subs = set()


def main():
    logger.info('Start')
    comments = comment_list()
    thread = build_thread(comments)
    submit_thread(thread)
    logger.info('Complete')


def comment_list():
    """
    Builds a list of 5-item tuples with data about recent admin activity
    """

    comments = []
    for mod in get_mods():
        for comment in get_comments(mod):
            c_time, s_id = comment
            s_link, requester, s_time = get_submission(s_id)
            comments.append((mod, c_time, s_link, requester, s_time))
    return comments


def get_mods():
    """
    Generator of strings which are the names of the moderators for the sub
    """

    try:
        mod_gen = reddit.subreddit(target_sub).moderator()
    except Exception as error:
        logger.exception(error)
    else:
        avoid = {'request_bot', 'automoderator'}
        for mod in mod_gen:
            if mod.name.lower() in avoid:
                continue
            yield mod.name


def get_comments(mod):
    """
    Generator of tuples containing the time of the comment and the id of the parent thread
    """

    try:
        comment_gen = reddit.redditor(mod).comments.new(limit=None)
    except Exception as error:
        logger.exception(error)
    else:
        count = 0
        for comment in comment_gen:
            if count == 3:
                break
            elif time() - comment.created_utc > 60 * 60 * 24 * 30:
                break
            elif comment.subreddit != target_sub:
                continue
            elif comment.submission.id in subs:
                continue
            else:
                yield comment.created_utc, comment.submission.id
                subs.add(comment.submission.id)
                count += 1


def get_submission(sub_id):
    """
    Returns the permalink, author and creation time for a submission
    """

    try:
        sub = reddit.submission(sub_id)
    except Exception as error:
        logger.exception(error)
    else:
        link = sub.permalink
        requester = sub.author.name if sub.author else None
        dor = sub.created_utc
        return link, requester, dor


def build_thread(comments):
    """
    Creates the body of the thread
    """

    stats = [row for row in conn.execute('SELECT * FROM stats')][0]
    header = """
##### Stats for approvals in the past 30 days
^^Updated ^^weekly ^^| ^^Measured ^^in ^^days ^^| ^^Some ^^approved ^^by ^^current ^^mods

Mean | Median | SD | Var | Min | Max | Quantity
---|---|---|---|---|---|---|---
 {} | {} | {} | {} | {} | {} | {}

---
##### Recent Comments
---
Admin|Comment Date|Thread|Requester|Request Date
---|---|---|---|---
""".format(*stats)
    strings = []
    comments.sort(key=lambda c: c[1], reverse=True)
    for comment in comments:
        strings.append(' | '.join(update_comments(comment)))  # TODO might need to be a list comprehension
    return header + '\n'.join(strings)


def update_comments(comment):
    """
    Modifies strings to be used in the thread body
    """

    moderator = '[{}](/u/{})'.format(comment[0][:8], comment[0])
    c_time = strftime('%d %b %Y', gmtime(comment[1]))
    s_link = '[Thread](http://www.reddit.com{})'.format(comment[2])
    requester = '[deleted]'
    if comment[3]:
        requester = '[{}](/u/{})'.format(comment[3][:8], comment[3])
    s_time = strftime('%d %b %Y', gmtime(comment[4]))
    return moderator, c_time, s_link, requester, s_time


def submit_thread(thread_body):
    """
    Builds and submits the thread
    Distinguishes author as a moderator
    """

    try:
        submission = reddit.subreddit('redditapprovals').submit(
            title='Recent Admin Activity',
            selftext=thread_body,
            send_replies=True
        )
    except Exception as error:
        logger.exception(error)
    else:
        try:
            submission.mod.distinguish()
            submission.mod.approve()
        except Exception as error:
            logger.exception(error)
        else:
            return


if __name__ == '__main__':
    main()
