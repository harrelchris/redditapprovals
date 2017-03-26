from time import time, gmtime, strftime
import logging
import sys
import praw

TARGET_SUB = 'redditrequest'
DESTINATION = 'redditapprovals'
REDDIT = praw.Reddit('AUTHENTICATION')
SUBS = set()
logger = logging.getLogger('Activity')
logging.basicConfig(
    filename='log.txt',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s')


def main():
    comments = comment_list()
    thread = build_thread(comments)
    submit_thread(thread)


def comment_list():
    """
    Called by main()
    Builds a list of 5-item tuples with data about recent admin activity

    :return comments: list
    """

    comments = []
    for mod in get_mods():
        for comment in get_comments(mod):
            c_time, s_id = comment
            s_link, requester, s_time = get_submission(s_id)
            comments.append((mod, c_time, s_link, requester, s_time))
    return comments


def build_thread(comments):
    """
    Called by main()
    Creates the body of the thread

    :param comments: list of 5-item tuples
    :return thread body text: string
    """

    header = """
##### All times are UTC
---
Admin|Date of Comment|Thread|Requestor|Date of Request
---|---|---|---|---
"""
    strings = []
    for comment in update_comments(comments):
        strings.append(' | '.join(comment))
    return header + '\n'.join(strings)


def submit_thread(thread_body):
    """
    Called by main()
    Builds and submits the thread
    Distinguishes author as a moderator

    :param thread_body: string
    """

    title = 'Recent Admin Activity'
    try:
        submission = REDDIT.subreddit(DESTINATION).submit(
            title=title,
            selftext=thread_body,
            send_replies=True
        )
    except Exception as error:
        handle_error(error)
    else:
        try:
            submission.mod.distinguish()
            submission.mod.approve()
        except Exception as error:
            handle_error(error)


def get_mods():
    """
    Called by comment_list()
    Generator of strings which are the names of the moderators for the sub

    :yield moderator.name: string
    """

    try:
        mod_gen = REDDIT.subreddit(TARGET_SUB).moderator()
    except Exception as error:
        handle_error(error)
    else:
        avoid = {'request_bot', 'automoderator'}
        for mod in mod_gen:
            if mod.name.lower() in avoid:
                continue
            yield mod.name


def get_comments(mod):
    """
    Called by comment_list()
    Generator of tuples containing the time of the comment and the id of the parent thread

    :param mod: string
    :yield: 2-item tuple
    """

    try:
        comment_gen = REDDIT.redditor(mod).comments.new(limit=None)
    except Exception as error:
        handle_error(error)
    else:
        count = 0
        for comment in comment_gen:
            if count == 3:
                break
            elif comment.subreddit == TARGET_SUB:
                if time() - comment.created_utc > 60 * 60 * 24 * 30:
                    break
                elif comment.submission.id in SUBS:
                    continue
                else:
                    yield comment.created_utc, comment.submission.id
                    SUBS.add(comment.submission.id)
                    count += 1


def get_submission(sub_id):
    """
    Called by comment_list()
    Returns the permalink, author and creation time for a submission

    :param sub_id: string
    :return 3-item tuple: string, string, int
    """

    try:
        sub = REDDIT.submission(sub_id)
    except Exception as error:
        handle_error(error)
    else:
        link = sub.permalink
        requester = sub.author.name if sub.author else None
        dor = sub.created_utc
        return link, requester, dor


def update_comments(comments):
    """
    Called by build_thread()
    Generator of 5-item tuple.
    Sorts the list of tuples and formats strings to be used in the thread body

    :param comments: list of 5-item tuples
    :yield 5-item tuple: 5 strings
    """

    # c[1] = comment date    c[4] = request date    reversed=True will put most recent on top
    comments.sort(key=lambda c: c[1], reverse=True)
    for comment in comments:
        moderator = '/u/{}'.format(comment[0][:8])
        c_time = convert_time(comment[1])
        s_link = '[Thread](http://www.reddit.com{})'.format(comment[2])
        requester = '/u/{}'.format(comment[3][:8]) if comment[3] else '[deleted]'
        s_time = convert_time(comment[1])
        yield moderator, c_time, s_link, requester, s_time


def convert_time(timestamp):
    """
    Called by update_comments()
    Converts a timestamp into a struct_time 9-item tuple
    Converts the tuple into a formatted date/time string

    :param timestamp: int
    :return formatted time: string
    """
    return strftime('%d %b %Y %H:%M:%S', gmtime(timestamp))


def handle_error(error):
    logger.exception(error)
    sys.exit()

if __name__ == '__main__':
    main()
    logger.info('Ran Activity.py')
