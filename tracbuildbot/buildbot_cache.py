from datetime import datetime, date
import time
from multiprocessing import Process, Queue, Value

from trac.env import Environment
from trac.db.api import get_column_names

from buildbot_api import BuildbotConnection, BuildbotException
import environmentSetup
from tools import Singleton


last_cached_query = "SELECT MAX(num) FROM buildbot_builds WHERE builder=%s"
save_build_query = "INSERT INTO buildbot_builds (%s) VALUES (%s)"
get_builds_query = """SELECT *,finish-start AS duration FROM buildbot_builds
                      WHERE finish >= %s AND finish <= %s AND builder IN (%s)
                   """

get_builds_query2 = """SELECT *,finish-start AS duration FROM buildbot_builds
                      WHERE finish >= %s AND finish <= %s
                   """


class BuildbotCacheException(BuildbotException):
    pass


class BuildbotCache(Singleton):
    def __init__(self, env):
        self.env = env
        self.connection = BuildbotConnection()
        self.fields = [col.name for col in environmentSetup.table.columns]

    def connect_to(self, address):
        self.connection.connect_to(address)

    def cache(self, builders):
        for builder in builders:
            self.cache_builder(builder)

    def cache_builder(self, builder):
        last_build_num = self.connection.get_build(builder, -1)['num']
        with self.env.db_transaction as db:
            cursor = db.cursor()

            cursor.execute(last_cached_query, [builder])
            last_cached_num = None
            try:
                last_cached_num = iter(cursor).next()[0]
            except StopIteration:
                pass

            if not last_cached_num: last_cached_num = -1

            for num in xrange(last_cached_num + 1, last_build_num + 1):
                build = self.connection.get_build(builder, num)

                query_build = dict()
                try:
                    for key, val in build.items():
                        if not key in self.fields: continue

                        if type(val) in (str, unicode):
                            query_build[key] = "'%s'" % val
                        elif type(val) == int:
                            query_build[key] = str(int(val))
                        elif type(val) == datetime:
                            query_build[key] = str(time.mktime(val.timetuple()))
                        else:
                            raise BuildbotCacheException('unknown type %s - %s' % (key, val))
                except BuildbotCacheException as e:
                    env.log.error(e)
                    print(e)
                    continue

                cursor.execute(save_build_query % (','.join(query_build.keys()),
                                                  ','.join(query_build.values())))

    def get_builds(self, builders, start, stop):
        start = str(int(time.mktime(start.timetuple())))
        stop = str(int(time.mktime(stop.timetuple())))
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute(get_builds_query %
                           (start, stop, ','.join(["'%s'" % builder for builder in builders])))
            fields = get_column_names(cursor)
            builds = []
            for build in cursor:
                builds.append(dict(zip(fields, build)))
            return builds

    def clear_cache(self):
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("DELETE FROM buildbot_builds")


def async_buildbot_cache_writer_run(queue, env_path, timeout):
    from Queue import Empty
    try:
        env = Environment(env_path)
        builders = []
        cache = BuildbotCache(env)

        while True:
            try:
                command, arg = queue.get(True, timeout.value)
            except Empty:
                command, arg = "cache", builders

            env.log.info("%s - %s" % (command, arg))
            if command == "cache":
                builders = arg
                try:
                    cache.cache(arg)
                except BuildbotException as e:
                    env.log.error(e) 
                env.log.info("cache finish") 
            elif command == "connect":
                cache.connect_to(arg)

            elif command == "stop":
                break

            else:
                print("wtf!?")
    except Exception as e:
        env.log.error(e)


class DeferredBuildbotCache(Singleton):
    def __init__(self, env):
        self.sync_cache = BuildbotCache(env)
        self.timeout = Value('i', 60)
        self.queue = Queue()
        self.proccess = Process(target=async_buildbot_cache_writer_run,
                                args=(self.queue, env.path, self.timeout))
        self.start()

    def __del__(self):
        self.stop()

    def __getattr__(self, name):
        try:
            return getattr(self.sync_cache, name)
        except Exception:
            pass

    def set_timeout(self, timeout):
        self.timeout.value = timeout

    def cache(self, builders):
        self.queue.put_nowait(("cache", builders))

    def connect_to(self, address):
        self.queue.put_nowait(("connect", address))
        self.sync_cache.connect_to(address)

    def start(self):
        self.proccess.start()

    def stop(self):
        self.queue.put(("stop", None))
        self.proccess.join(5)
        if self.proccess.is_alive():
            self.proccess.terminate()


if __name__ == "__main__":
    #cache = BuildbotCache(r"e:\Work\trac\env")
    #cache.connect_to("localhost:8010")
    ##cache.cache(["runtests"])
    #for build in cache.get_builds(["runtests"], 0, 1399833622):
    #    print(build)

    try:
        async_cache = DeferredBuildbotCache(Environment(r"e:\Work\trac\env"))
        async_cache.connect_to("localhost:8010")
        #async_cache.clear_cache()
        #async_cache.cache(["runtests"])
        for build in async_cache.get_builds(["runtests", "runtests2","gutproject"], date(2000,1,1), date(2015,1,1)):
            print(build)
        async_cache.stop()
        pass

    except Exception as e:
        async_cache.stop()
        raise e