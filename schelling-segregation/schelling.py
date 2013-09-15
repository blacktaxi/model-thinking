#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: eis
Created on 25/03/12 01:20
"""
import sys
import threading
import time
import datetime

import random
random.seed()

from fw.vmbridge import *

#

class Citizen(object):
    def __init__(self, citizen_type, happiness_threshold):
        assert 0 <= happiness_threshold <= 1

        self.type = citizen_type
        self.happiness_threshold = happiness_threshold

    def neighbors_alike(self, neighbors=()):
        return float(len([n for n in neighbors if self.is_alike_to(n)])) / len(neighbors) if len(neighbors) > 0 else 0.0

    def is_alike_to(self, citizen):
        return citizen.type == self.type

    def is_happy_with_neighbors(self, neighbors):
        return self.neighbors_alike(neighbors) >= self.happiness_threshold

class SchellingsModel(QtCore.QObject):
    cell_updated = Event(variant)
    
    def __init__(self, world_size=(20, 20)):
        QtCore.QObject.__init__(self)
        
        self.init_world(world_size)

    def init_world(self, world_size):
        self.world = [[None for _ in xrange(world_size[0])] for _ in xrange(world_size[1])]
        self.world_size = world_size
        self.population = []

    #

    def is_free_place(self, coords):
        return self.world_cell(coords) is None

    def world_cell(self, coords):
        return self.world[coords[0]][coords[1]]
    
    def set_cell(self, coords, val):
        self.world[coords[0]][coords[1]] = val
        self.cell_updated.emit(
            dict(
                x=coords[0], 
                y=coords[1], 
                val=val.type if val is not None else ''
            )
        )

    def add_citizen(self, citizen, coords):
        assert self.is_free_place(coords)

        citizen.address = coords
        self.set_cell(coords, citizen)
        self.population.append(citizen)

    def remove_citizen_from(self, coords):
        assert not self.is_free_place(coords)

        citizen = self.world_cell(coords)
        self.set_cell(coords, None)
        self.population.remove(citizen)
        citizen.address = None
 
        return citizen

    def move_citizen(self, from_c, to_c):
        self.add_citizen(
            self.remove_citizen_from(from_c), 
            to_c
        )

    def neighbors_for_citizen(self, citizen):
        assert citizen.address

        w = self.world_size[0]
        h = self.world_size[1]

        x = citizen.address[0]
        y = citizen.address[1]

        return filter(lambda v: v is not None, [
            self.world_cell((x + xd, y + yd,)) for xd in [-1, 0, 1] for yd in [-1, 0, 1] if ((0 <= x + xd < w) and (0 <= y + yd < h) and (not (xd == yd == 0)))
        ])

    def random_free_location(self):
        while 1:
            x = random.randint(0, self.world_size[0]-1)
            y = random.randint(0, self.world_size[1]-1)

            if self.is_free_place((x, y,)): return (x, y,)
            
    def is_citizen_happy(self, citizen):
        return citizen.is_happy_with_neighbors(self.neighbors_for_citizen(citizen))

    #

    def do_world_heartbeat(self, max_moves=200):
        print 'heartbeat...'

        pop = list(self.population)
        random.shuffle(pop)

        moved = 0
        for c in pop:
            if not c.is_happy_with_neighbors(self.neighbors_for_citizen(c)):
                self.move_citizen(c.address, self.random_free_location())
                moved += 1
            if moved >= max_moves: break

        print 'moved: ', moved
        
    def calc_happy_percent(self):
        return int(float(len([c for c in self.population if self.is_citizen_happy(c)])) / len(self.population) * 100 \
            if len(self.population) > 0 else 0)

#

@bridged_view_model
class RacialSegregationViewModel(object):
    # user events
    click_start_life = Event()
    click_stop_life = Event()
    click_create_world = Event(int, int, float, float)
    loaded = Event()

    # model events
    world_created = Event(variant)
    world_updated = Event(variant)
    cell_updated = Event(variant)
    
    # properties
    happy_percent = Property()

#

class Controller(QtCore.QObject):
    def __init__(self):
        QtCore.QObject.__init__(self)
        
        self.model = SchellingsModel((100, 100,))
        self.viewmodel = RacialSegregationViewModel()

        # connections
        self.viewmodel.click_start_life.connect(self.start_life)
        self.viewmodel.click_stop_life.connect(self.stop_life)
        self.viewmodel.click_create_world.connect(self.create_world)
        self.viewmodel.loaded.connect(lambda: self.create_world(50, 50, 0.8, 0.5))

    def populate_world(self, density=0.85, happiness_threshold=0.60):
        # citizen types
        types = ['p', 'r']

        for _ in xrange(int(self.model.world_size[0] * self.model.world_size[1] * density)):    
            self.model.add_citizen(Citizen(random.choice(types), happiness_threshold), self.model.random_free_location())

    def render_world(self):
        result = [[c.type if c is not None else '' for c in line] for line in self.model.world]
        return result

    def start_life(self):
        def tfunc():
            self.model.cell_updated.connect(self.viewmodel.cell_updated)

            self._should_stop_life = False
            
            skip = 0
            while not self._should_stop_life: 
                self.model.do_world_heartbeat()
                self.model.do_world_heartbeat()
                
                skip += 1
                if skip > 5000:
                    self.viewmodel.happy_percent = self.model.calc_happy_percent()
                    skip = 0
                
                time.sleep(0.001)
                #self.viewmodel.world_updated.emit(self.render_world())
                
            self.model.cell_updated.disconnect(self.viewmodel.cell_updated)
                
        threading.Thread(target=tfunc).start()

    def stop_life(self):
        self._should_stop_life = True
        
    def create_world(self, width, height, density, threshold):
        print 'creating new world'
        
        self.model.init_world((width, height,))
        self.populate_world(density, threshold)

        self.viewmodel.world_created.emit(self.model.world_size)
        self.viewmodel.world_updated.emit(self.render_world())
    
#

def main():
    app = QtGui.QApplication([])

    #

    ctrlr = Controller()    

    view = create_webview(
        './views/schelling.html',
        {'viewModel': ctrlr.viewmodel}
    )

    #

    window = QtGui.QMainWindow()
    window.setCentralWidget(view)
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
