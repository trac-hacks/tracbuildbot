from datetime import datetime, date
import time
from multiprocessing import Pool
import traceback

from trac.env import Environment
from trac.db.api import get_column_names

from buildbot_api import BuildbotConnector, BuildbotException
import environmentSetup


class BuildbotCacheException(BuildbotException):
    pass


class BuildbotCache:
    def __init__(self, env, connector):
        self.env = env
        self.connector = connector
        self.fields = [col.name for col in environmentSetup.table.columns]

    def connect_to(self, url):
        self.connector.connect_to(url)

    def cache(self, builders):
        for builder in builders:
            self.cache_builder(builder)

    def cache_builder(self, builder):
        last_build_num = self.connector.get_build(builder, -1)['num']
        with self.env.db_transaction as db:
            cursor = db.cursor()

            cursor.execute("SELECT MAX(num) FROM buildbot_builds WHERE builder=%s", [builder])
            last_cached_num = None
            try:
                last_cached_num = iter(cursor).next()[0]
            except StopIteration:
                return
            if last_cached_num == None: last_cached_num = -1            


            for num in xrange(last_cached_num + 1, last_build_num + 1):
                try:
                    build = self.connector.get_build(builder, num)
                except BuildbotException as e:
                    self.env.log.error(e)
                    continue

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
                    self.env.log.error(e)
                    continue

                cursor.execute("INSERT INTO buildbot_builds (%s) VALUES (%s)" %
                               (','.join(query_build.keys()), ','.join(query_build.values())))

    def get_builds(self, builders, start, stop):
        start = str(int(time.mktime(start.timetuple())))
        stop = str(int(time.mktime(stop.timetuple())))
        with self.env.db_query as db:
            cursor = db.cursor()

            cursor.execute("""
                           SELECT *,finish-start AS duration FROM buildbot_builds
                           WHERE finish >= %s AND finish <= %s AND builder IN (%s)
                           """ %
                           (start, stop, ','.join(["'%s'" % builder for builder in builders])))
            fields = get_column_names(cursor)
            return [dict(zip(fields, build)) for build in cursor]

    def clear_cache(self):
        with self.env.db_transaction as db:
            cursor = db.cursor()
            cursor.execute("DELETE FROM buildbot_builds")


def async_buildbot_cache_init(env_path):
    global cache
    cache = BuildbotCache(Environment(env_path), BuildbotConnector())

def async_buildbot_cache_worker(url, builders):
    global cache
    try:
        cache.env.log.debug('cache %s' % ', '.join(builders))
        cache.connect_to(url)
        for builder in builders:
            try:
                cache.cache_builder(builder)
            except BuildbotException as e:
                cache.env.log.error("builder %s - %s " % (builder, e))
        cache.env.log.debug('cache finished')
    except Exception:
        cache.env.log.error(traceback.format_exc())


class DeferredBuildbotCache:
    def __init__(self, env, connector):
        self.sync_cache = BuildbotCache(env, connector)
        self.pool = Pool(1, async_buildbot_cache_init, (env.path,))

    def __del__(self):
        self.stop()

    def __getattr__(self, name):
        return getattr(self.sync_cache, name)

    def cache(self, builders):
        result = self.pool.apply_async(async_buildbot_cache_worker, (self.connector.url, builders))
        result.wait(3)

    def stop(self):
        self.pool.close()
        self.pool.join()


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