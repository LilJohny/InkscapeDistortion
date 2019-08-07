import os
from math import sqrt
import inkex
import simplepath
import simpletransform
import simplestyle


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
        nodes_filtered = [x for x in nodes if x[0] != 'Z']
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

    def _get_dimension(self, s="1024"):
        "Converts an SVG length to pixels"
        if s == "":
            return 0
        try:
            last = int(s[-1])
        except (ValueError, IndexError):
            last = None
        if type(last) == int:
            return float(s)
        elif s[-1] == "%":
            return 1024
        elif s[-2:] == "px":
            return float(s[:-2])
        elif s[-2:] == "pt":
            return float(s[:-2]) * 1.25
        elif s[-2:] == "em":
            return float(s[:-2]) * 16
        elif s[-2:] == "mm":
            return float(s[:-2]) * 3.54
        elif s[-2:] == "pc":
            return float(s[:-2]) * 15
        elif s[-2:] == "cm":
            return float(s[:-2]) * 35.43
        elif s[-2:] == "in":
            return float(s[:-2]) * 90
        else:
            return 1024

    def _merge_transform(self, node, transform):
        if node.tag == inkex.addNS("svg", "svg") and node.get("viewBox"):
            vx, vy, vw, vh = [
                self._get_dimension(x) for x in node.get("viewBox").split()
            ]
            dimension_width = self._get_dimension(node.get("width", vw))
            dimension_height = self._get_dimension(node.get("height", vh))
            t = ("translate(%f, %f) scale(%f, %f)" %
                 (-vx, -vy, dimension_width / vw, dimension_height / vh))
            cur_transform = simpletransform.parseTransform(t, transform)
            cur_transform = simpletransform.parseTransform(
                node.get("transform"), cur_transform)
            del node.attrib["viewBox"]
        else:
            cur_transform = simpletransform.parseTransform(
                node.get("transform"), transform)
        node.set("transform", simpletransform.formatTransform(cur_transform))

    def _merge_style(self, node, style):
        cur_style = simplestyle.parseStyle(node.get("style", ""))
        remaining_style = {}

        non_propagated = ["filter"]
        for key in non_propagated:
            if key in cur_style.keys():
                remaining_style[key] = cur_style[key]
                del cur_style[key]

        parent_style_copy = style.copy()
        parent_style_copy.update(cur_style)
        cur_style = parent_style_copy
        style_attribs = ["fill", "stroke"]
        for attrib in style_attribs:
            if node.get(attrib):
                cur_style[attrib] = node.get(attrib)
                del node.attrib[attrib]

                if (node.tag == inkex.addNS("svg", "svg")
                        or node.tag == inkex.addNS("g", "svg")
                        or node.tag == inkex.addNS("a", "svg")
                        or node.tag == inkex.addNS("switch", "svg")):
                    if len(remaining_style) == 0:
                        if "style" in node.keys():
                            del node.attrib["style"]
                    else:
                        node.set("style",
                                 simplestyle.formatStyle(remaining_style))

                else:
                    cur_style.update(remaining_style)

                    node.set("style", simplestyle.formatStyle(cur_style))


if __name__ == '__main__':
    ext = DistorsionExtension()
    ext.affect()
