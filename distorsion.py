import inkex
import os
import sys
import cubicsuperpath
from math import sqrt
import simplepath
import simpletransform

inkex.localize()


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

    #def effect(self):
    #    self.svg_file = sys.argv[-1]
    #    self.parse()
    #    self.getoptions()
    #    q = self.options.lambda_coef
    #    element = self.getElementById(self.options.ids[0])
    #    nodes = cubicsuperpath.parsePath(element.get('d'))
    #    start, finish = element.attrib['d'].split(' ')[-2:]
    #    self.getposinlayer()
    #    x_c, y_c = self.view_center
    #    width = int(self.getDocumentWidth().replace('mm', ''))
    #    height = int(self.getDocumentHeight().replace('mm', ''))
    #    distorted_nodes = []
    #    for node in nodes[0]:
    #        coordinates_distorted = []
    #        for coordinates in node:
    #            x_u = (coordinates[0] - x_c) / (width + height)
    #            y_u = (coordinates[1] - y_c) / (width + height)
    #            x_d = x_u / 2 / (q * y_u**2 + x_u**2 * q) * (
    #                1 - sqrt(1 - 4 * q * y_u**2 - 4 * x_u**2 * q))
    #            y_d = y_u / 2 / (q * y_u**2 + x_u**2 * q) * (
    #                1 - sqrt(1 - 4 * q * y_u**2 - 4 * x_u**2 * q))
    #            coordinates_distorted.append([x_d, y_d])
    #        distorted_nodes.append(coordinates_distorted)
    #    for distorted_node in distorted_nodes:
    #        for distorted_coordinates in distorted_node:
    #            distorted_coordinates[0] *= width + height
    #            distorted_coordinates[0] += x_c
    #            distorted_coordinates[1] *= width + height
    #            distorted_coordinates[1] += y_c
    #    distorted_path = cubicsuperpath.formatPath([distorted_nodes])
    #    inkex.debug(element.get('d'))
    #    inkex.debug(distorted_path)
    #    element.set("d", distorted_path)
    #    inkex.debug(dir(element))

    def distort_coordinates(self, x, y):
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
        #self.width = int(self.getDocumentWidth().replace('mm', ''))
        #self.height = int(self.getDocumentHeight().replace('mm', ''))
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
        self.x_c = 82.0
        self.y_c = 279.0
        inkex.debug(self.x_c)
        inkex.debug(self.y_c)
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