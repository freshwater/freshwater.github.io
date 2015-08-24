
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from itertools import chain, combinations
from IPython.display import SVG


# named colors
_colors = matplotlib.colors.cnames

# svg defaults
_defaults = {
    'svg': {'padding': 1.02},
    'radius': 50,
    'point-radius': 1,
}



"""
    xml structuring
"""

import xml.etree.ElementTree as etree

def xml(tag, attributes={}, children=None):
    attributes = dict((k, str(v)) for k, v in attributes.items())
    node = etree.Element(tag, attributes)

    if children != None:
        if isinstance(children, list):
            for child in children:
                node.append(child)
        elif isinstance(children, str):
            node.text = children
        else:
            node.append(children)

    return node



"""
    graphics primitives
"""

def tooltip(obj, s):
    """Attach a tooltip to a graphics primitive."""

    title = xml('title', {}, str(s))

    if isinstance(obj, dict):
        obj['svg'].append(title)
    elif isinstance(obj, list):
        for el in obj:
            tooltip(el, s)

    return obj

def Attributes(obj, **attrs):
    if isinstance(obj, dict):
        obj['svg'].attrib.update(attrs)

    return obj


def line(ls, is_poly=False):
    """Line primitive, to be used inside graphics."""

    # bounds
    xs, ys = np.transpose(ls)
    
    svgp = [str(x) + ' ' + str(y) for x, y in ls];
    commands = 'M ' + " L ".join(svgp) + (' Z ' if is_poly else '')
    
    style = '' if is_poly else 'fill: none'

    res = { 'svg': xml('path', {'d': commands, 'style': style}),
            'bounds': (min(xs), max(xs), min(ys), max(ys)) }

    return res
   

def polygon(ls, **kwargs):
    """Polygon primitive, to be used inside graphics."""

    return line(ls, is_poly=True, **kwargs)


def disk(c=[0,0], r=_defaults['radius'], is_disk=False):
    """Disk primitive, to be used inside graphics."""

    return { 'svg': xml('circle', {'cx': c[0], 'cy': c[1], 'r': r}),
             'bounds': (c[0] - r, c[0] + r, c[1] - r, c[1] + r) }


def circle(c=[0,0], r=_defaults['radius']):
    """Circle primitive, to be used inside graphics."""

    circ = disk(c=c, r=r)
    circ['svg'].set('style', 'fill: none')

    return circ


def point(c=[0,0], r=_defaults['point-radius']):
    """Point primitive, to be used inside graphics."""

    circ = disk(c=c, r=r)
    circ['svg'].set('style', 'stroke: none')

    return circ


def rectangle(corners=_defaults['radius']*np.array([[-1, -1], [1, 1]]),
        c=None, wh=[_defaults['radius']]*2):
    """Rectangle primitive, to be used inside graphics."""

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

    return { 'svg': xml('rect', {'x': x, 'y': y, 'width': w, 'height': h}),
             'bounds': (min_x, max_x, min_y, max_y) }

def RGB(r, g, b, a=1):
    return 'rgba(' + ",".join([str(n) for n in [r,g,b,a]]) + ');'



"""
    utilities
"""

def _extract_key(ls, key):
    if isinstance(ls, list):
        for elem in ls:
            yield from _extract_key(elem, key)
            
    if isinstance(ls, dict):
        if key in ls:
            yield ls[key]

def _replace_key(ls, key):
    if isinstance(ls, list):
        return [_replace_key(elem, key) for elem in ls]
            
    if isinstance(ls, dict):
        if key in ls:
            return ls[key]
        
    return ls



"""
    math stuff
"""

def re_im(z):
    return [z.real, z.imag]

def circle_points(n, c=[0,0], r=_defaults['radius'], radial_offset=0):
    return c + np.array(
        [re_im(r * np.e**(1j * (radial_offset + 2*np.pi * k / n))) for k in range(n)])

def subsets(S):
    return chain.from_iterable(combinations(S,k) for k in range(0,len(S)+1))
    


"""
    svg construction
"""

def _subgraphics(ls):
    i = 0
    result = []
    
    # iterate through flat region without running through stack
    while(i < len(ls) and isinstance(ls[i], dict)):
        result.append(ls[i]['svg'])
        i += 1
        
    if ls[i:] == []:
        return result

    elem, *rest = ls[i:]

    if isinstance(elem, list):
        return result + _subgraphics(elem) + _subgraphics(rest)
    elif elem in _colors:
        return result + [xml('g', {'style': 'fill: ' + elem }, _subgraphics(rest))]
    elif isinstance(elem, str):
        return result + [xml('g', {'style': elem}, _subgraphics(rest))]
    else:
        return result + _subgraphics(rest)


# main graphics function. use `data` method to get raw svg.
# default width/height defined in CSS to enable certain containments
# e.g. to automatically make the svg pane smaller when inside a Table
def graphics(directives=[], width=None, height=None, **attributes):
    """Render a sequence of graphics primitives to SVG."""

    if not(isinstance(directives, list)): # eg graphics(disk())
        return graphics([directives], width=width, height=height, **attributes)
    
    # extract all bounds
    bounds = list(_extract_key(directives, 'bounds'))
    if bounds == []: # no primitives. output a blank pane
        return graphics(["stroke: none", line([[0, 0], [50, 50]])],
                width=width, height=height, **attributes)

    min_xs, max_xs, min_ys, max_ys = np.transpose(bounds)
    mins, maxs = np.array([[min(min_xs), min(min_ys)], [max(max_xs), max(max_ys)]])
    
    # viewbox values, with some padding
    center = (maxs + mins) / 2
    spans = (maxs - mins) * _defaults['svg']['padding'] # padding
    [x, y], [w, h] = center - spans/2, spans
    
    view_box = " ".join(map(str, [x, y, w, h]))
    
    attrs = {'xmlns': "http://www.w3.org/2000/svg",
             'viewBox': view_box,
             'class': "sierpinski Graphics"}

    attrs.update(attributes)

    structure = xml('svg', attrs,
            xml('g', {'style': "stroke: black; stroke-width: 1; fill: black"},
                _subgraphics(directives)))

    # convert width height keywords to style directives
    style = ";" + "; ".join([
                'width: ' + str(width) + 'px' if width != None else '',
                'height: ' + str(height) + 'px' if height != None else ''])

    structure.attrib['style'] = structure.attrib.get('style', '') + style

    return HTML(etree.tostring(structure).decode())



""""
    ipython display
"""

from IPython.display import HTML, Javascript, display

def _first_repr(a):
    for rep in ['_repr_svg_', '_repr_html_']:
        if rep in dir(a):
            return getattr(a, rep)()
    
    return str(a)

import uuid

# needs to be made into a general tab view
def Gallery(ls, name=""):
    """
    Creates a tabbed view pane. Link to it with
        <span class='flipbookLink' name='<gallery name>' index='<tab number>'>link</span>
    """

    id = uuid.uuid4()
    
    return HTML(("""
        <ol id="s%(id)s" class="flipbook static" name="%(name)s">
        <li>
            """
            + "</li><li>".join([_first_repr(el) for el in ls])
            + """
        </li>
        </ol>
        
        <script type="text/javascript" src="flipbook-ipy.js"></script>
        <script type="text/javascript">
            if ($('head').children('#oftencsslink').length === 0) {
                $('head').append('<link id="oftencsslink" rel="stylesheet" type="text/css" href="oftencss_ipy.css" />');
            }

            constructFlipbook($, $("#s%(id)s"));
        </script>
        
            """) % {'id': id, 'name': name})


def Javascript(*js, scope=True):
    """Concatenate and auto scope Javascript code."""
    js = " ".join(js)

    if scope:
        return "(function(){" + js + "})();"
    else:
        return js    



def Column(ls, style="", item_style=""):
    return HTML(('<table class="sierpinski Column" style="%(style)s">' 
                + " ".join(['<tr style="%(item_style)s"><td>' + _first_repr(el) + '</td></tr>' for el in ls])
                + '</table>') % { 'style': style, 'item_style': item_style })


def Row(ls, style="", item_style=""):
    if not(isinstance(ls, list)):
        return Row([ls], style=style)
    
    return HTML(('<table class="sierpinski Row" style="%(style)s"><tr>'
                + " ".join(['<td style="%(item_style)s">' + _first_repr(el) + '</td>' for el in ls])
                + '</tr></table>') % { 'style': style, 'item_style': item_style })


def List(ls, style="", separator=", ", before="[", after="]"):
    return HTML(('<span class="sierpinski List" style="%(style)s"> '
                + before + separator.join(['<span>' + _first_repr(el) + '</span>' for el in ls]) + after
                + '</span>') % { 'style': style })


def Frame(item, style=""):
    return HTML(('<span class="sierpinski Frame" style="%(style)s">'
                 + _first_repr(item)
                 + '</span>') % { 'style': style })


### need to refactor system to preserve XML structure.
def EventHandler(item, **kwargs):
    attributes = " ".join([str(k) + '=\'' + str(v) + '\'' for k, v in kwargs.items()])
    # attrs = { 'class': "sierpinski EventHandler" }
    # attrs.update(attributes)

    # return etree.tostring(xml('span', attrs, _first_repr(item))).decode()

    return HTML(('<span class="sierpinski EventHandler" %(attributes)s>'
                 + _first_repr(item)
                 + '</span>') % { 'attributes': attributes })


def Button(item, **kwargs):
    attributes = " ".join([str(k) + '=\'' + str(v) + '\'' for k, v in kwargs.items()])
    return HTML(('<button class="sierpinski Button" %(attributes)s>'
                 + _first_repr(item)
                 + '</span>') % { 'attributes': attributes })


# def Table(ls, style="", row_style="", item_style=""):
def Table(ls, **kwargs):
    kw = {'row_style': "", 'item_style': ""}

    opts = dict([(k, kwargs.get(k, "")) for k in kw.keys()])
    attributes = " ".join([str(k) + '=\'' + str(v) + '\''
                           for k, v in kwargs.items() if not(k in kw)])

    kw.update(opts)
    kw.update({ 'attributes': attributes })

    return HTML(('<table class="sierpinski Table" %(attributes)s">'
                + " ".join(['<tr style="%(row_style)s">'
                            + " ".join(['<td style="%(item_style)s">' + _first_repr(el) + '</td>' for el in row])
                            + '</tr>'
                   for row in ls])
                + '</table>') % kw)


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
        // .linkDistance((edge_distance)s)
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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

















