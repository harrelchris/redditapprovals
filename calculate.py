import statistics as sts
import sqlite3
import logging

logger = logging.getLogger('Activity')
logging.basicConfig(
    filename='log.txt',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s')
conn = sqlite3.connect('approvals.db')
c = conn.cursor()


def main():
    """
    Refresh table
    Get all durations and convert float
    Calc mean, median and divide results by num of seconds/day
    Store the values
    """

    c.execute('DROP TABLE IF EXISTS stats')
    c.execute('CREATE TABLE IF NOT EXISTS stats(count, mean, median)')
    durations = [float(d[0]) for d in conn.execute('SELECT duration FROM threads WHERE is_mod=1')]
    count = len(durations)
    values = sts.mean(durations), sts.median(durations)
    mean, median = [int(d // (60 * 60 * 24)) for d in values]
    c.execute('INSERT INTO stats VALUES (?,?,?)', (count, mean, median))
    conn.commit()

if __name__ == '__main__':
    main()
    logger.info('Ran Calculate')
