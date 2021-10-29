import cv2
import numpy
import math
from lib.Vectors.Vectors import VectorsMath
from dataclasses import dataclass, fields


G = 6.67*pow(10, -11)
SCREEN_H = 100 
SCREEN_W = 100
SCREEN_S = 5
RADIUS = 25

class OrbitSim:

    @dataclass
    class Object:
        x: float = 0
        y: float = 0

        color: tuple = (255, 255, 255)
        selected: bool = False

        mass: float = 0

        static: bool = True
        path_iterations: int = 50

        gf_x: float = 0
        gf_y: float = 0
        gf_m: float = 0
        gf_d: float = 0

        vf_x: float = 0
        vf_y: float = 0
        vf_m: float = 0
        vf_d: float = 0

        pv_x: float = 0
        pv_y: float = 0


    def __init__(self):

        self._clear_screen = lambda: numpy.zeros((SCREEN_H * SCREEN_S, SCREEN_W * SCREEN_S, 3), numpy.uint8)

        self.screen = self._clear_screen()

        self.v_scale = 1

        cv2.namedWindow('OrbitSim')
        cv2.setMouseCallback('OrbitSim', self._mouse_handler)

        self.objects = list()
        self.pathfinders = list()

        self.objects.append(self.Object(x=50, y=10, vf_x=0, static=False, color=(0, 255, 0),   mass=500))
        self.objects.append(self.Object(x=50, y=50, color=(0, 255, 255),                       mass=1600000))
        # self.objects.append(self.Object(x=35, y=20, static=False, color=( 255, 255, 0),        mass=500))

        self.pathfinders.append(self.Object(x=50, y=10, static=False, color=(0, 255, 0),   mass=500))
        self.pathfinders.append(self.Object(x=50, y=50, color=(0, 255, 255),               mass=1600000))
        # self.pathfinders.append(self.Object(x=35, y=20, static=True, color=( 255, 255, 0),mass=700000))

        self._run()
        self._keyboard_listener()
        return

    def start(self):
        while True:
            self._run()
            cv2.waitKey(100)

    def _run(self, v: bool = False):
        self.screen = self._clear_screen()
        self._compute_g_forces(self.objects, v)
        self._compute_path_vector(self.objects)
        self._compute_path()
        self._draw()
        self._show_screen()
        return

    def _show_screen(self):
        cv2.imshow("OrbitSim", cv2.flip(self.screen, 0))
        return

    def _draw(self, grid: bool = False):

        def __draw_grid():

            for i in range(SCREEN_W):
                cv2.line(self.screen, (i * SCREEN_S, 0), (i * SCREEN_S, SCREEN_H * SCREEN_S), (50, 50, 50))
        
            for i in range(SCREEN_H):
                cv2.line(self.screen, (0, i * SCREEN_S), (SCREEN_W * SCREEN_S, i * SCREEN_S), (50, 50, 50))

            return

        if grid is True:
            __draw_grid()

        for obj in self.objects:

            if obj.selected == True:
                cv2.circle(self.screen, (obj.x * SCREEN_S, obj.y * SCREEN_S), 6 * SCREEN_S, (255,255, 0), 1)

            cv2.circle(self.screen, (obj.x * SCREEN_S, obj.y * SCREEN_S), 5 * SCREEN_S, obj.color, -1)

            # gravity force vector
            cv2.arrowedLine(self.screen, (obj.x * SCREEN_S, obj.y * SCREEN_S), 
                                         (int(obj.x * SCREEN_S + obj.gf_x * SCREEN_S), int(obj.y * SCREEN_S + obj.gf_y * SCREEN_S)),
                                         (0, 0, 255), int(0.5 * SCREEN_S))

            # velocity force vector
            cv2.arrowedLine(self.screen, (obj.x * SCREEN_S, obj.y * SCREEN_S), 
                                         (int(obj.x * SCREEN_S + obj.vf_x * SCREEN_S), int(obj.y * SCREEN_S + obj.vf_y * SCREEN_S)),
                                         (155, 0, 255), int(0.5 * SCREEN_S))

            # path vector
            cv2.arrowedLine(self.screen, (obj.x * SCREEN_S, obj.y * SCREEN_S), 
                                         (int(obj.x * SCREEN_S + obj.pv_x * SCREEN_S), int(obj.y * SCREEN_S + obj.pv_y * SCREEN_S)),
                                         (155, 155, 0), int(0.5 * SCREEN_S))

        return

    def _mouse_handler(self, event, x, y, flags, param):

        for obj in self.objects:

            if event == cv2.EVENT_LBUTTONDOWN:
                
                if obj.selected is False:
                    if (obj.x * SCREEN_S) - ((5 * SCREEN_S)/2) < x < (obj.x  * SCREEN_S) + ((5 * SCREEN_S)/2) and \
                       (obj.y  * SCREEN_S) - ((5 * SCREEN_S)/2) < (SCREEN_H * SCREEN_S) - y < (obj.y  * SCREEN_S) + ((5 * SCREEN_S)/2):

                       obj.selected = True
                    else:
                        obj.selected = False
                else:
                    obj.selected = False

                self._run()


            elif event == cv2.EVENT_MOUSEMOVE:

                if obj.selected is True:

                    obj.x = int(x / SCREEN_S)
                    obj.y = int(SCREEN_H - (y / SCREEN_S))

                    self.pathfinders[self.objects.index(obj)].x = int(x / SCREEN_S)
                    self.pathfinders[self.objects.index(obj)].y = int(SCREEN_H - (y / SCREEN_S))

                    self._run()

        return

    def _keyboard_listener(self):
        while True:
            key = cv2.waitKey()
            if self._keyboard_handler(key) == 0:
                break

    def _keyboard_handler(self, key):

        # print(key)
        if key == 27:  # ESC
            print("Quitting...")
            return 0

        if key == 113:  # Q
            self.v_scale -= 1
            print(f"Velocity scale: {self.v_scale}")
        if key == 101:  # E
            self.v_scale += 1
            print(f"Velocity scale: {self.v_scale}")

        for obj in self.objects:

            pathfinder = self.pathfinders[self.objects.index(obj)]

            if obj.selected:

                if key == 97:  # A
                    obj.vf_x -= 0.1 * self.v_scale
                    pathfinder.vf_x -= 0.1 * self.v_scale

                if key == 115:  # S
                    obj.vf_y -= 0.1 * self.v_scale
                    pathfinder.vf_y -= 0.1 * self.v_scale

                if key == 100:  # D
                    obj.vf_x += 0.1 * self.v_scale
                    pathfinder.vf_x += 0.1 * self.v_scale

                if key == 119:  # W
                    obj.vf_y += 0.1 * self.v_scale
                    pathfinder.vf_y += 0.1 * self.v_scale
                
                if key == 122:  # Z
                    print(f"Path iteration: {pathfinder.path_iterations}")
                    pathfinder.path_iterations += 10
                if key == 120:  # X
                    print(f"Path iteration: {pathfinder.path_iterations}")
                    pathfinder.path_iterations -= 10
        
        self._run()

        return

    @staticmethod
    def __compute_direction(_x, _y):

                if _x != 0 or _y != 0:

                    if _x == 0:
                        if _y < 0:
                            _direction = 90
                        elif _y > 0:
                            _direction = 270
                    elif _y == 0:
                        if _x < 0:
                            _direction = 0
                        elif _x > 0:
                            _direction = 180
                    else:
                        if _x < 0 and _y < 0:
                            _direction = math.degrees(math.atan(_y / _x))
                        elif _x < 0 and _y > 0:
                            _direction = 360 + math.degrees(math.atan(_y / _x))
                        else:
                            _direction = 180 + math.degrees(math.atan(_y / _x))

                    return _direction
                else:
                    return 0

    def _compute_path_vector(self, objects: list):

        for obj in objects:

            obj.pv_x = obj.gf_x + obj.vf_x
            obj.pv_y = obj.gf_y + obj.vf_y

        return

    def _compute_path(self):

        for pathfinder in self.pathfinders:

            pathfinder.x = self.objects[self.pathfinders.index(pathfinder)].x
            pathfinder.y = self.objects[self.pathfinders.index(pathfinder)].y

            if pathfinder.static is False:

                self._compute_g_forces(self.pathfinders)
                self._compute_path_vector(self.pathfinders)

                x1 = pathfinder.x
                y1 = pathfinder.y
                pathfinder.vf_x = self.objects[self.pathfinders.index(pathfinder)].vf_x * -1
                pathfinder.vf_y = self.objects[self.pathfinders.index(pathfinder)].vf_y * -1

                pathfinder.vf_d = self.__compute_direction(pathfinder.vf_x, pathfinder.vf_y)

                d_vg_angle = pathfinder.vf_d - pathfinder.gf_d

                pathfinder.vf_m = math.sqrt(pow(pathfinder.vf_x,2) + pow(pathfinder.vf_y, 2))

                # distance = math.sqrt(pow(self.objects[0].x - self.objects[1].x,2) + pow(self.objects[0].y - self.objects[1].y, 2))
                # self.path_iterations = distance * 5.5
                
                i = 0
                while (x1 < SCREEN_W and y1 < SCREEN_H) and i < pathfinder.path_iterations:

                    if self.objects[1].x - 1 < x1 < self.objects[1].x + 1 and self.objects[1].y - 1 < y1 < self.objects[1].y + 1:
                        break

                    if pathfinder.pv_x == 0:
                        m = 40
                    else:
                        m = pathfinder.pv_y / pathfinder.pv_x

                    if -1 < m < 1:

                        if pathfinder.pv_x < 0:
                            x1 = x1 - 1
                        else:
                            x1 = x1 + 1

                        y1 = (m * (x1 - pathfinder.x)) + pathfinder.y
                        
                    else:

                        if pathfinder.pv_y == 0:
                            m = 40
                        else:
                            m = pathfinder.pv_x / pathfinder.pv_y

                        if pathfinder.pv_y < 0:
                            y1 = y1 - 1
                        else:
                            y1 = y1 + 1

                        x1 = pathfinder.x + (m * (y1 - pathfinder.y))   

                    x1s = int(x1 * SCREEN_S)
                    y1s = int(y1 * SCREEN_S)

                    pathfinder.x = x1
                    pathfinder.y = y1

                    cv2.rectangle(self.screen, (x1s - 1, y1s - 1), (x1s + 1, y1s + 1), (255,255,255), -1)

                    self._compute_g_forces(self.pathfinders)

                    pathfinder.vf_d = pathfinder.gf_d - d_vg_angle

                    pathfinder.vf_x = pathfinder.vf_m * math.cos(math.radians(pathfinder.vf_d))
                    pathfinder.vf_y = pathfinder.vf_m * math.sin(math.radians(pathfinder.vf_d))

                    self._compute_path_vector(self.pathfinders)

                    i += 1 


                for field in fields(self.Object):
                    if field.name != "path_iterations":
                        setattr(pathfinder, field.name, getattr(self.objects[self.pathfinders.index(pathfinder)], field.name))


                self._compute_g_forces(self.pathfinders)
                self._compute_path_vector(self.pathfinders)

                x1 = pathfinder.x
                y1 = pathfinder.y
                pathfinder.vf_x = self.objects[self.pathfinders.index(pathfinder)].vf_x
                pathfinder.vf_y = self.objects[self.pathfinders.index(pathfinder)].vf_y

                pathfinder.vf_d = self.__compute_direction(pathfinder.vf_x, pathfinder.vf_y)

                d_vg_angle = pathfinder.vf_d - pathfinder.gf_d

                pathfinder.vf_m = math.sqrt(pow(pathfinder.vf_x,2) + pow(pathfinder.vf_y, 2))

                i = 0
                while (x1 < SCREEN_W and y1 < SCREEN_H) and i < pathfinder.path_iterations:

                    if self.objects[1].x - 1 < x1 < self.objects[1].x + 1 and self.objects[1].y - 1 < y1 < self.objects[1].y + 1:
                        break

                    if pathfinder.pv_x == 0:
                        m = 40
                    else:
                        m = pathfinder.pv_y / pathfinder.pv_x

                    if -1 < m < 1:

                        if pathfinder.pv_x < 0:
                            x1 = x1 - 1
                        else:
                            x1 = x1 + 1

                        y1 = (m * (x1 - pathfinder.x)) + pathfinder.y
                        
                    else:

                        if pathfinder.pv_y == 0:
                            m = 40
                        else:
                            m = pathfinder.pv_x / pathfinder.pv_y

                        if pathfinder.pv_y < 0:
                            y1 = y1 - 1
                        else:
                            y1 = y1 + 1

                        x1 = pathfinder.x + (m * (y1 - pathfinder.y))   

                    x1s = int(x1 * SCREEN_S)
                    y1s = int(y1 * SCREEN_S)

                    pathfinder.x = x1
                    pathfinder.y = y1

                    cv2.rectangle(self.screen, (x1s - 1, y1s - 1), (x1s + 1, y1s + 1), (255,255,255), -1)

                    self._compute_g_forces(self.pathfinders)

                    pathfinder.vf_d = pathfinder.gf_d - d_vg_angle

                    pathfinder.vf_x = pathfinder.vf_m * math.cos(math.radians(pathfinder.vf_d))
                    pathfinder.vf_y = pathfinder.vf_m * math.sin(math.radians(pathfinder.vf_d))

                    self._compute_path_vector(self.pathfinders)

                    i += 1 
                    
                

        return

    def _compute_g_forces(self, objects: list, verbouse: bool = False):

        def __compute_cartesians(_m, _d):

            _x = _m * math.cos(math.radians(_d))
            _y = _m * math.sin(math.radians(_d))

            return _x, _y

        if len(objects) > 1:
            
            forces = list()
            
            for i in range(len(objects)):
                
                if verbouse is True:
                    print(f"object {i}")

                forces.append(list())
            
                for j in range(len(objects)):
            
                    if j != i:
                        
                        if verbouse is True:
                            print(f"Calculating force between objects {i}, {j}")
                            print(f"\tMass:\n\t\tObject {i}: {objects[i].mass} kg\n\t\tObject {j}: {objects[j].mass} kg")
                            print(f"\tCoordinates:\n\t\tObject {i}: (x={objects[i].x}, y={objects[i].y})\n\t\tObject {j}: (x={objects[j].x}, y={objects[j].y})")
            
                        distance = int(math.sqrt((pow((objects[i].x - objects[j].x), 2)
                                                  + pow((objects[i].y - objects[j].y), 2))))
                        if distance == 0:
                            return 

                        if verbouse is True:
                            print(f"\tDistance: {distance} m")
            
                        f = ((objects[i].mass * objects[j].mass) / distance) * G
            
                        direction = self.__compute_direction(objects[i].x - objects[j].x,
                                                        objects[i].y - objects[j].y)
                        
                        if verbouse is True:
                            print(f"\tForce: {f} N(m/kg)^2")
                            print(f"\tDirection: {direction}°")
            
                        forces[i].append((f, direction))

                if verbouse is True:
                    print(f"\nForces for the Object {i}: {forces[i]}")

                if forces[i] != list():
                    if verbouse is True:
                        print("\nCalculating resultant force...")

                    f_xy = list()

                    for f in forces[i]:

                        f_xy.append(__compute_cartesians(f[0], f[1]))
                    
                    ff_x = 0
                    ff_y = 0
                    
                    for f in f_xy:
                        ff_x = ff_x + f[0]
                        ff_y = ff_y + f[1]
                    
                    if verbouse is True:
                        print(f"Resultant force cartesian components: ({ff_x}, {ff_y})")
                    
                    ff_m = math.sqrt(pow(ff_x, 2) + pow(ff_y, 2))
                    ff_d = self.__compute_direction(ff_x, ff_y)
                    
                    objects[i].gf_x = ff_x
                    objects[i].gf_y = ff_y
                    
                    if verbouse is True:
                        print(f"Resultant force: {ff_m} N(m/kg)^2\n\tWith direction: {ff_d}°\n\n")
                    
                    objects[i].gf_m = ff_m
                    objects[i].gf_d = ff_d


        return


def __main__():
    os = OrbitSim()
    # os.start()
    return


if __name__ == "__main__":
    __main__()
