import time
import random

from db_handler import DbHandler

db = DbHandler()

db.open_db()

for i in range(100):
    my_zoom = random.randint(1, 14)
    print(my_zoom)
    # db.insert_tile(my_zoom, 3800, 16302, False, '/hello/world', 1234)

    my_xtile = random.randint(1, 5)
    db.insert_tile(my_zoom, my_xtile, 16302, False, '/hello/world', 1234)
    # db.clean_tiles()
    # db.print_tiles()
    db.update_tile_status(my_zoom, 3800, 16302, True, random.randint(1, 1e6))
    # db._tile_exists(my_zoom, my_xtile, 16302)
    print(db.get_tile_size(my_zoom, my_xtile, 16302))
    db.remove_tile(my_zoom, my_xtile, 16302)
db.print_tiles()
# db.clean_tiles()
# db.print_tiles()
db.close_db()
