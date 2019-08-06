import inkex
import os
from math import sqrt
import simplepath



class DistorsionExtension(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        try:
            self.tty = open("/dev/tty", 'w')
        except:
            self.tty = open(os.devnull, 'w')
        self.OptionParser.add_option("-l",
                                     "--lambda",
                                     action="store",
                                     type="float",
                                     dest="lambda_coef",
                                     default=1.0,
                                     help="command line help")

    def distort_coordinates(self, x, y):
        """Method applies barrel distorsion to given points with distorsion center in center of image, selected to 
        
        Args:
            x (float): X coordinate of given point
            y (float): Y coordinate of given point
        
        Returns:
            tuple(float, float): Tuple with X,Y distorted coordinates of given point
        """
        x_u = (x - self.x_c) / (self.width + self.height)
        y_u = (y - self.y_c) / (self.width + self.height)
        x_d = x_u / 2 / (self.q * y_u**2 + x_u**2 * self.q) * (
            1 - sqrt(1 - 4 * self.q * y_u**2 - 4 * x_u**2 * self.q))
        y_d = y_u / 2 / (self.q * y_u**2 + x_u**2 * self.q) * (
            1 - sqrt(1 - 4 * self.q * y_u**2 - 4 * x_u**2 * self.q))
        x_d *= self.width + self.height
        y_d *= self.width + self.height
        x_d += self.x_c
        y_d += self.y_c
        return x_d, y_d

    def effect(self):
        self.q = self.options.lambda_coef
        nodes = []
        for id, node in self.selected.iteritems():
            if node.tag == inkex.addNS('path', 'svg'):
                d = node.get('d')
                path = simplepath.parsePath(d)
                nodes += path
        nodes_filtered = [x for x in nodes if x[0]!='Z']
        x_coordinates = [x[-1][-2] for x in nodes_filtered]
        y_coordinates = [y[-1][-1] for y in nodes_filtered]
        self.width = max(x_coordinates) - min(x_coordinates)
        self.height = max(y_coordinates) - min(y_coordinates)
        self.x_c = sum(x_coordinates) / len(x_coordinates)
        self.y_c = sum(y_coordinates) / len(y_coordinates)
        for id, node in self.selected.iteritems():
            if node.tag == inkex.addNS('path', 'svg'):
                d = node.get('d')
                path = simplepath.parsePath(d)
                distorted = []
                first = True
                for cmd, params in path:
                    if cmd != 'Z':
                        if first == True:
                            x = params[-2]
                            y = params[-1]
                            distorted.append(
                                ['M',
                                 list(self.distort_coordinates(x, y))])
                            first = False
                        else:
                            x = params[-2]
                            y = params[-1]
                            distorted.append(
                                ['L', self.distort_coordinates(x, y)])
                node.set('d', simplepath.formatPath(distorted))


if __name__ == '__main__':
    ext = DistorsionExtension()
    ext.affect()
