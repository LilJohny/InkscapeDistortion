import os
from math import sqrt
import inkex
import simplepath
import simpletransform
import simplestyle
try:
    from numpy import matrix
except ImportError:
    raise ImportError("""Cannot find numpy.matrix in {0}.""".format(__file__))

KEEPDEPTH = 0
STARTDEPTH = 0
MAXDEPTH = 65535


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

    def _merge_clippath(self, node, clippathurl):
        if clippathurl:
            node_transform = simpletransform.parseTransform(
                node.get("transform"))
            if node_transform:
                inverse_node_transform = simpletransform.formatTransform(
                    self._invert_transform(node_transform))
                new_clippath = inkex.etree.SubElement(
                    self.xpathSingle("//svg:defs"), "clipPath", {
                        "clipPathUnits": "userScapeOnUse",
                        "id": self.uniqueId("clipPath")
                    })
                clippath = self.getElementById(clippathurl[5:-1])
                for c in clippath.iterchildren():
                    inkex.etree.SubElement(
                        new_clippath, "use", {
                            inkex.addNS('href', 'xlink'): "#" + c.get("id"),
                            "transform": inverse_node_transform,
                            "id": self.uniqueId("use")
                        })
                clippathurl = "url(#" + new_clippath.get("id") + ")"
            node_clippathurl = node.get("clip-path")
            while node_clippathurl:
                node = self.getElementById(node_clippathurl[5:-1])
                node_clippathurl = node.get("clip-path")
            node.set("clip-path", clippathurl)

    def _invert_transform(self, transform):
        return matrix(transform + [[0, 0, 1]]).I.tolist()[0:2]

    def _ungroup(self, node):
        node_parent = node.getparent()
        node_index = list(node_parent).index(node)
        node_style = simplestyle.parseStyle(node.get("style"))
        node_transform = simpletransform.parseTransform(node.get("transform"))
        node_clippathurl = node.get("clip-path")
        for c in reversed(list(node)):
            self._merge_transform(c, node_transform)
            self._merge_style(c, node_style)
            self._merge_clippath(c, node_clippathurl)
            node_parent.insert(node_index, c)
        node_parent.remove(node)

    def _can_ungroup(self, node, depth, height):
        if node.tag == inkex.addNS("g", "svg") and node.getparent(
        ) is not None and height > KEEPDEPTH and depth >= STARTDEPTH and depth <= MAXDEPTH:
            return True
        return False

    def _deep_ungroup(self, node):
        q = [{
            "node": node,
            "depth": 0,
            "prev": {
                "height": None
            },
            "height": None
        }]
        while q:
            current = q[-1]
            node = current["node"]
            depth = current["depth"]
            height = current["height"]
            if height is None:
                if node.tag == inkex.addNS(
                        "namedview", "sodipodi") or node.tag == inkex.addNS(
                            "defs", "svg") or node.tag == inkex.addNS(
                                "metadata", "svg") or node.tag == inkex.addNS(
                                    "foreignObject", "svg"):
                    q.pop
                if node.tag != inkex.addNS("g", "svg") or not len(node):
                    current["height"] = 0
                else:
                    depth += 1
                    for c in node.iterchildren():
                        q.append({
                            "node": c,
                            "prev": current,
                            "depth": depth,
                            "height": None
                        })
            else:
                if self._can_ungroup(node, depth, height):
                    self._ungroup(node)
                height += 1
                previous = current["prev"]
                prev_height = previous["height"]
                if prev_height is None or prev_height < height:
                    previous["height"] = height
                q.pop()

    def effect(self):
        for elem in self.selected.itervalues():
            self._deep_ungroup(elem)
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


if __name__ == '__main__':
    ext = DistorsionExtension()
    ext.affect()
