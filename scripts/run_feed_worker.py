from rq import Worker, Connection
from crunevo.tasks import redis_conn, task_queue

if __name__ == "__main__":
    with Connection(redis_conn):
        worker = Worker([task_queue.name])
        worker.work()
