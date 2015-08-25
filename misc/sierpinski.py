
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
# from itertools import chain, combinations
from IPython.display import SVG


# named colors
_colors = matplotlib.colors.cnames

# svg defaults
_defaults = {
    'padding': 1.02,
    'radius': 50,
    'point-radius': 1,
}



"""
    xml structuring
"""

# multiple issues with xml.etree.ElementTree so made my own Xml class

class Xml():
    def __init__(self, tag, attributes={}, children=None, data=None):
        self.tag = tag
        self.attributes = attributes

        if children != None and not(isinstance(children, list)):
            if not(isinstance(children, str)):
                children = [children]

        self.children = children
        self.data = data

    def append(self, child):
        if self.children == None:
            self.children = []

        self.children.append(child)

    def set(self, **attributes):
        self.attributes.update(attributes)

    def get(self, attribute, default=None):
        return self.attributes.get(attribute, default)

    def _all_data(self, item):
        if isinstance(item, Xml):
            if item.data != None:
                yield item.data
            
            if item.children != None:
                for el in item.children:
                    yield from self._all_data(el)

        elif isinstance(item, list):
            for el in item:
                yield from self._all_data(el)

    def all_data(self):
        """Extract all embedded data items."""
        return list(self._all_data(self))

    def to_str(self):
        attrs = self.attributes
        chl = self.children

        if attrs is not None or attrs != {}:
            _attributes = ' '.join([k + '=\'' + str(v) + '\'' for k, v in attrs.items()])

        if chl is not None:
            _children = ''.join([str(el) for el in chl])

        _tail = ('>' + _children + '</' + self.tag + '>') if chl is not None else '/>'

        return ('<' + self.tag
                + ((' ' + _attributes) if len(attrs) > 0 else '')
                + _tail)

    __str__ = to_str
    __repr__ = to_str
    _repr_html_ = to_str


_flipbook_lib = Xml('script', {'type': 'text/javascript', 'src': 'flipbook-ipy.js'}, ' ')
_oftencss_link = Xml('script', {'type': 'text/javascript'},
"""
if ($('head').children('#oftencsslink').length === 0) {
    $('head').append('<link id="oftencsslink" rel="stylesheet" type="text/css" href="oftencss_ipy.css" />');
}
""")



"""
    graphics primitives
"""

def Tooltip(obj, s):
    """Attach a tooltip to a graphics primitive."""

    title = Xml('title', {}, str(s))

    if isinstance(obj, Xml):
        obj.append(title)
    elif isinstance(obj, list):
        for el in obj:
            Tooltip(el, s)

    return obj


def Attributes(obj, **attributes):
    if isinstance(obj, Xml):
        obj.attributes.update(attributes)

    return obj


def line(ls, is_poly=False):
    """Line primitive, to be used inside graphics."""

    # bounds
    xs, ys = np.transpose(ls)
    
    svgp = [str(x) + ' ' + str(y) for x, y in ls];
    commands = 'M ' + " L ".join(svgp) + (' Z' if is_poly else '')

    style = '' if is_poly else 'fill: none'

    return Xml('path', {'d': commands, 'style': style},
               data=(min(xs), max(xs), min(ys), max(ys)))
   

def polygon(ls):
    """Polygon primitive, to be used inside graphics."""

    return line(ls, is_poly=True)


def disk(c=[0,0], r=_defaults['radius'], is_disk=False):
    """Disk primitive, to be used inside graphics."""
    c = np.array(c)

    return Xml('circle', {'cx': c[0], 'cy': c[1], 'r': r},
               data = (c[0] - r, c[0] + r, c[1] - r, c[1] + r))


def circle(c=[0,0], r=_defaults['radius']):
    """Circle primitive, to be used inside graphics."""

    circ = disk(c=c, r=r)
    circ.set(style='fill: none')

    return circ


def point(c=[0,0], r=_defaults['point-radius']):
    """Point primitive, to be used inside graphics."""

    circ = disk(c=c, r=r)
    circ.set(style='stroke: none')

    return circ


def rectangle(corners=_defaults['radius']*np.array([[-1, -1], [1, 1]]),
        c=None, wh=[_defaults['radius']]*2):
    """
    Rectangle primitive, to be used inside graphics.
    Accepts both center width-height and corner1 corner2 specifications.
    """

    x, y, w, h = [None]*4
    
    if c:
        c, wh = np.array([c, wh])
        x, y = c - wh/2
        w, h = wh
        corners = c + [-wh/2, wh/2]
    else:
        corners = np.array(corners)
        x, y = corners[0]
        w, h = corners[1] - corners[0]

    (min_x, max_x), (min_y, max_y) = map(sorted, np.transpose(corners))

    return Xml('rect', {'x': x, 'y': y, 'width': w, 'height': h},
               data = (min_x, max_x, min_y, max_y))

def RGB(r, g, b, a=1):
    return 'rgba(' + ",".join([str(n) for n in [r,g,b,a]]) + ');'



"""
    utilities
"""

def _intersperse(ls, sep):
    it = iter(ls)

    yield next(it)
    for el in it:
        yield sep
        yield el



"""
    math stuff
"""

def re_im(z):
    return [z.real, z.imag]


def circle_points(n, c=[0,0], r=_defaults['radius'], radial_offset=0):
    return c + np.array(
        [re_im(r * np.e**(1j * (radial_offset + 2*np.pi * k / n))) for k in range(n)])


# def subsets(S):
#     return chain.from_iterable(combinations(S,k) for k in range(0,len(S)+1))



"""
    svg construction
"""

def _subgraphics(ls):
    i = 0
    result = []
    
    # iterate through flat region without running through stack
    while(i < len(ls) and isinstance(ls[i], Xml)):
        result.append(ls[i])
        i += 1
        
    if ls[i:] == []:
        return result

    elem, *rest = ls[i:]

    if isinstance(elem, list):
        return result + _subgraphics(elem) + _subgraphics(rest)
    elif elem in _colors:
        return result + [Xml('g', {'style': 'fill: ' + elem }, _subgraphics(rest))]
    elif isinstance(elem, str):
        return result + [Xml('g', {'style': elem}, _subgraphics(rest))]
    else:
        return result + _subgraphics(rest)


# default width/height is defined in CSS to enable certain containments
# e.g. to automatically make the svg pane smaller when inside a Table
def graphics(directives=[], width=None, height=None, **attributes):
    """Render a sequence of graphics primitives to SVG."""

    if not(isinstance(directives, list)): # eg graphics(disk())
        return graphics([directives], width=width, height=height, **attributes)
    
    # extract all bounds
    bounds = Xml("", {}, directives).all_data()

    if bounds == []: # no primitives. output a blank pane
        return graphics(["stroke: none", line([[0, 0], [50, 50]])],
                width=width, height=height, **attributes)

    min_xs, max_xs, min_ys, max_ys = np.transpose(bounds)
    mins, maxs = np.array([[min(min_xs), min(min_ys)], [max(max_xs), max(max_ys)]])
    
    # viewbox values, with some padding
    center = (maxs + mins) / 2
    spans = (maxs - mins) * _defaults['padding'] # padding
    [x, y], [w, h] = center - spans/2, spans
    
    view_box = " ".join(map(str, [x, y, w, h]))
    
    attrs = {'xmlns': "http://www.w3.org/2000/svg",
             'viewBox': view_box,
             'class': "sierpinski Graphics"}

    attrs.update(attributes)

    default_style = {'style': "stroke: black; stroke-width: 1; fill: black"}

    svg = Xml('svg', attrs,
            Xml('g', default_style,
                _subgraphics(directives)))

    # convert width height keywords to style directives
    # and append to user-specified style
    wh_style = "; ".join([
                'width: ' + str(width) + 'px' if width != None else '',
                'height: ' + str(height) + 'px' if height != None else ''])

    svg.set(style=svg.get('style', '') + ';' + wh_style)

    return Xml('span', {}, [_oftencss_link, svg])



""""
    ipython display
"""

from IPython.display import HTML, display

def _first_repr(a):
    if isinstance(a, Xml):
        return a
    else:
        for rep in ['_repr_svg_', '_repr_html_']:
            if rep in dir(a):
                return getattr(a, rep)()
    
        return str(a)

import uuid


# index names
def Gallery(ls, name=None, **attributes):
    """
    Creates a tabbed view pane. Link to it with
        <span class='flipbookLink' name='<gallery name>' index='<tab number>'>link</span>
    """

    id = uuid.uuid4()

    attrs = {'id': 's' + str(id), 'class': 'flipbook static'}
    attrs.update({'name': name} if name != None else {})
    attrs.update(attributes)

    construct_js = Xml('script', {'type': 'text/javascript'},
                       'constructFlipbook($, $("#' + attrs['id'] + '"));')

    return Xml('ol', attrs,
        [Xml('li', {}, _first_repr(el)) for el in ls]
        + [_flipbook_lib, _oftencss_link, construct_js])


import re

def Javascript(*js, scope=True, minify=True):
    """Concatenate and auto scope Javascript code."""

    js = " ".join(js)

    if minify:
        js = re.sub(r'\s+', ' ', js)

    if scope:
        return "(function(){" + js + "})();"
    else:
        return js    


def Column(ls, item_style=None, **attributes):
    """Display a list of items in a column."""

    if not(isinstance(ls, list)):
        return Column([ls], item_style=item_style, **attributes)

    attrs = {'class': 'sierpinski Column'}
    attrs.update(attributes)

    item_attrs = {'style': item_style} if item_style != None else {}

    return Xml('table', attrs,
            [Xml('tr', item_attrs, Xml('td', {}, el)) for el in ls])


def Row(ls, item_style=None, **attributes):
    """Display a list of items in a row."""

    if not(isinstance(ls, list)):
        return Row([ls], item_style=item_style, **attributes)

    attrs = {'class': 'sierpinski Row'}
    attrs.update(attributes)

    item_attrs = {'style': item_style} if item_style != None else {}

    return Xml('table', attrs, Xml('tr', {},
               [Xml('td', item_attrs,
                    _first_repr(el)) for el in ls]))


def List(ls, separator=", ", before="[", after="]", item_style=None, **attributes):
    """Display a list of items in a list. Unlike a Row, List can wrap."""

    separator, before, after = [Xml('span', {}, s)
                                for s in [separator, before, after]]

    attrs = {'class': 'sierpinski List'}
    attrs.update(attributes)

    item_attrs = {'style': item_style} if item_style != None else {}

    inner = [Xml('span', item_attrs, _first_repr(el)) for el in ls]

    return Xml('span', attrs,
               [before] + list(_intersperse(inner, separator)) + [after])


def Frame(item, **attributes):
    """Display an item in a frame."""

    attrs = {'class': 'sierpinski Frame'}
    attrs.update(attributes)

    return Xml('span', attrs, _first_repr(item))


def EventHandler(item, **attributes):
    """Set Javascript event attributes."""

    attrs = { 'class': "sierpinski EventHandler" }
    attrs.update(attributes)

    return Xml('span', attrs, _first_repr(item))


def Table(ls, row_style=None, item_style=None, **attributes):
    """Display a rectangular array in a grid."""

    attrs = {'class': 'sierpinski Table'}
    attrs.update(attributes)

    row_attrs = {'style': row_style} if row_style != None else {}
    item_attrs = {'style': item_style} if item_style != None else {}

    return Xml('table', attrs,
               [Xml('tr', row_attrs,
                    [Xml('td', item_attrs, _first_repr(el)) for el in row])
                for row in ls])

import uuid
from scipy import misc
import networkx as nx

class Graph(nx.classes.graph.Graph):
    _html_template = ("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.5/d3.min.js"></script>
    <svg id="%(id)s" class="sierpinski Graph"></svg>
    
    <script>
(function() {
    if ($('head').children('#oftencsslink').length === 0) {
        $('head').append('<link id="oftencsslink" rel="stylesheet" type="text/css" href="oftencss_ipy.css" />');
    }
    
    // modified from http://blog.thomsonreuters.com/index.php/mobile-patent-suits-graphic-of-the-day/
    
    var links = %(edges)s;
    
    var nodes = {};

    // Compute the distinct nodes from the links.
    
    links.forEach(function(link) {
      link.source = nodes[link.source] || (nodes[link.source] = {name: link.source});
      link.target = nodes[link.target] || (nodes[link.target] = {name: link.target});
    });
    
    
    /*
    links.forEach(function(link) {
        nodes[link.source] = {name: link.source};
        nodes[link.target] = {name: link.target};
    });
    */
    
    /*
    var width = (width)s;
    var height = (height)s;
    */

    /* needs css w/h to be defined */
    /* from css */
    var width = parseInt($("#%(id)s").css("width"), 10);
    var height = parseInt($("#%(id)s").css("height"), 10);

    var area = width * height;

    /* from python */
    var edge_count = %(edge_count)s;
    var node_count = %(node_count)s;
    var nd = %(node_density)s;

    var enRatio = edge_count / node_count;
    // alert(enRatio);


    var edgeDistance = Math.min( .8 * Math.sqrt(area),
        1.3 * Math.sqrt(area) / Math.sqrt(edge_count) );


    var nodeRadius = Math.sqrt(nd * area / node_count / (2 * Math.PI))

    var edgeArea = edge_count * edgeDistance;
    var strokeOpacity = Math.max(.3, 1 - Math.sqrt(edgeArea / area));
    var strokeWidth = 2*strokeOpacity;

    var force = d3.layout.force()
        .nodes(d3.values(nodes))
        .links(links)
        .size([width, height])
        .linkDistance(edgeDistance)
        .charge(-300)
        .on("tick", tick)
        .start();

    var svg = d3.select("#%(id)s")
        .attr("class", "sierpinski Graph")
        .attr("width", width)
        .attr("height", height);

    // Per-type markers, as they don't inherit styles.
    svg.append("defs").selectAll("marker")
        .data(["suit", "licensing", "resolved"])
      .enter().append("marker")
        .attr("id", function(d) { return "%(id)s" + d; })
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 15)
        .attr("refY", -1.5)
        .attr("markerWidth", 2)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
      .append("path")
        .attr("d", "M0,-5L10,0L0,5");

    var path = svg.append("g").selectAll("path")
        .data(force.links())
      .enter().append("path")
        .attr("class", function(d) { return "link " + d.type; })
        // .attr("style", function() { return "stroke-opacity: " + (stroke_opacity)s; stroke-width: (stroke_width)s"; })
        .attr("style", function() { return "stroke-opacity: " + strokeOpacity + "; stroke-width: " + strokeWidth; })
        .attr("marker-end", function(d) { return "url(#" + d.type + ")"; });

    var circle = svg.append("g").selectAll("circle")
        .data(force.nodes())
      .enter().append("circle")
        // .attr("r", (node_radius)s)
        .attr("r", nodeRadius)
        .attr("class", "sierpinski Graph node")
        .call(force.drag);

    var text = svg.append("g").selectAll("text")
        .data(force.nodes())
      .enter().append("text")
        .attr("class", function(d) { return "graphtext"; })
        .attr("x", 8)
        .attr("y", ".31em")
        .text(%(textf)s);
        // .text(function(d) { return d.name; });

    // Use elliptical arc path segments to doubly-encode directionality.
    function tick() {
      path.attr("d", linkArc);
      circle.attr("transform", transform);
      text.attr("transform", transform);
    }

    function linkArc(d) {
      var dx = d.target.x - d.source.x,
          dy = d.target.y - d.source.y,
          dr = Math.sqrt(dx * dx + dy * dy);
      // return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
      return "M" + d.source.x + "," + d.source.y + "L" + d.target.x + "," + d.target.y;
    }

    function transform(d) {
      return "translate(" + d.x + "," + d.y + ")";
    }
})();
    </script>
    """)
    
    def __init__(self, *g, **kwargs):
        self._settings = {
            'node_labels': False,
            'node_density': .015,
            'edge_density': .01,
            'width': 400,
            'height': 360
        }

        self._settings.update(kwargs)
    
        super(Graph, self).__init__(*g)
    
    def _repr_html_(self):
        edge_pack = lambda s, t: '{source: "' + str(s) + '", ' + 'target: "' + str(t) + '"}'
        edges = "[" + ", ".join([edge_pack(s, t) for s, t in self.edges()]) + "]"

        node_density, edge_density, w, h = [self._settings[k] for k in
                                            ['node_density', 'edge_density', 'width', 'height']]

        edge_count, node_count = self.number_of_edges(), self.number_of_nodes()

        opts = {
            'id': 's' + str(uuid.uuid4()),
            'node_density': node_density,
            'edge_density': edge_density,
            'edge_count': edge_count,
            'node_count': node_count,
            'edges': edges,
            'textf': 'function(d) { return d.name; }' if self._settings['node_labels'] else 'function(d) { return ""; }'
        }

        opts.update(self._settings)
        
        return self._html_template % opts



"""
    plotting
"""

def array_plot(ls, cmap=matplotlib.cm.gray):
    plt.matshow(ls, cmap=cmap)
    plt.xticks([])
    plt.yticks([])
    plt.axis('off')


_point_defaults = {
    'linestyle': '',
    'marker': 'o',
    'markersize': 1,
    'color': 'black'
}

def point_plot(ls, **kwargs):
    opts = _point_defaults.copy()
    opts.update(kwargs)
    
    plt.axes(aspect='equal')
    plt.plot(*np.transpose(ls), **opts)
    plt.xticks([])
    plt.yticks([])
    plt.axis('off')
    plt.show()