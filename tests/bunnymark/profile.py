#./ignifuga-python
import cProfile, pstats
import bunnies
profileFileName = 'profile_data.pyprof'
profile = cProfile.Profile()
profile.run('bunnies.run()')
profile.dump_stats(profileFileName)
profile.print_stats()

pstats.Stats(profileFileName).strip_dirs().sort_stats("time").print_stats()