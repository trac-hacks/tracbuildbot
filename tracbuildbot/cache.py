import pickle
import os

from buildbot_api import BuildbotException

class BuildbotBuildsCache:
    def __init__(self, tmp_path):
        self.cached_data = dict()
        self.connection = None
        self.tmp_path = tmp_path
        self.last_cached_num = dict()


    def get_builds(self, builder):        
        self.cache(builder)
        return self.cached_data[builder]

    def read_cache_file(self, builder):
        builder_cache_path = self.tmp_path + "\\" + builder
        self.cached_data[builder] = dict()
        self.last_cached_num[builder] = -1

        # read cache_file
        if os.path.exists(builder_cache_path):
            with open(builder_cache_path) as cache_file:
                rec = None
                try:
                    while True:
                        rec = pickle.load(cache_file)
                        self.cached_data[builder][rec['num']] = rec
                except EOFError:
                    pass
            self.last_cached_num[builder] = rec['num']

    def cache(self, builder):
        if not builder in self.cached_data:
            self.read_cache_file(builder)

        last_build = self.connection.get_build(builder, -1)

        last_cached_num = self.last_cached_num[builder]
        if last_build['num'] > last_cached_num:
            builder_cache_path = self.tmp_path + "\\" + builder
            try:
                if not os.path.exists(self.tmp_path): os.makedirs(self.tmp_path)
            except os.error as e:
                raise BuildbotException(str(e))
            cache_file = open(builder_cache_path, "w+")
            for num in xrange(last_cached_num + 1, last_build['num']):
                build = self.connection.get_build(builder, num)
                pickle.dump(build, cache_file)
                self.cached_data[builder][num] = build
            pickle.dump(last_build, cache_file)

