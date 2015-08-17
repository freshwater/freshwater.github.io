
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from itertools import chain, combinations
from IPython.display import SVG

# named colors
_colors = matplotlib.colors.cnames

# svg defaults
_defaults = {
    'width': 400,
    'height': 240,
    'padding': 1.02,
    'radius': 50,
    'point-radius': 1,
    'render': SVG
}



"""
    graphics primitives
"""

def line(ls, is_poly=False):
    # bounds
    xs, ys = np.transpose(ls)
    
    svgp = [" ".join(map(str,xy)) for xy in ls];
    commands = " L ".join(svgp)
    
    # handle polygon case
    closed = ' Z ' if is_poly else ''
    style = '' if is_poly else 'style="fill: none;"'
    
    return { 'svg': '<path d="M ' + commands + closed + '" ' + style + '/>',
             'bounds': (min(xs), max(xs), min(ys), max(ys)) }

def polygon(ls):
    return line(ls, is_poly=True)

def circle(c=[0,0], r=_defaults['radius'], is_disk=False):
    style = '' if is_disk else 'style="fill: none;"'
    coords = { 'cx': c[0], 'cy': c[1], 'r': r, 'style': style }
    
    return { 'svg': '<circle cx="%(cx)s" cy="%(cy)s" r="%(r)s" %(style)s />' % coords,
             'bounds': (c[0] - r, c[0] + r, c[1] - r, c[1] + r) }

def disk(c=[0,0], r=_defaults['radius']):
    return circle(c=c, r=r, is_disk=True)

def point(c=[0,0], r=_defaults['point-radius']):
    coords = { 'cx': c[0], 'cy': c[1], 'r': r, 'style': 'style="stroke: none"' }
    
    return { 'svg': '<circle cx="%(cx)s" cy="%(cy)s" r="%(r)s" %(style)s />' % coords,
             'bounds': (c[0] - r, c[0] + r, c[1] - r, c[1] + r) }

def rectangle(corners=[[-.5,-.5], [.5,.5]], c=None, wh=[_defaults['radius']]*2):
    x, y, w, h = [None]*4
    
    if c:
        c, wh = np.array([c, wh])
        x, y = c - .5*wh
        w, h = wh
    else:
        corners = np.array(corners)
        x, y = corners[0]
        w, h = corners[1] - corners[0]

    coords = { 'x': x, 'y': y, 'width': w, 'height': h }
    
    (min_x, max_x), (min_y, max_y) = map(sorted, np.transpose(corners))
    
    return { 'svg': '<rect x="%(x)s" y="%(y)s" width="%(width)s" height="%(height)s" />' % coords,
             'bounds': (min_x, max_x, min_y, max_y) }



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

def subgraphics(ls):
    i = 0
    result = ""
    
    # iterate through flat region without running through stack
    # Iterable version would be better
    while(i < len(ls) and isinstance(ls[i], dict)):
        result += ls[i]['svg']
        i += 1
        
    if ls[i:] == []:
        return result

    elem, *rest = ls[i:]

    if isinstance(elem, list):
        return result + subgraphics(elem) + subgraphics(rest)
    elif elem in _colors or isinstance(elem, str) and elem[0] == '#':
        return result + '<g style="fill: ' + elem + '">' + subgraphics(rest) + '</g>'
    elif isinstance(elem, str):
        return result + '<g style="' + elem + '">' + subgraphics(rest) + '</g>'
    else:
        return result + subgraphics(rest)

        
# main graphics function. set render to lambda x: x to get plain svg
def graphics(directives=[], **options):
    opts = _defaults.copy()
    opts.update(options)
    
    # if not(isinstance(directives, collections.Iterable)): # eg graphics(disk())
    if not(isinstance(directives, list)): # eg graphics(disk())
        return graphics([directives], **options)
    
    # extract all bounds
    bounds = list(_extract_key(directives, 'bounds'))
    if bounds == []: # no primitives. output a blank pane
        return graphics(["stroke: none", line([[0,0],[50,50]])], options)
    
    min_xs, max_xs, min_ys, max_ys = np.transpose(bounds)
    mins, maxs = np.array([[min(min_xs), min(min_ys)], [max(max_xs), max(max_ys)]])
    
    # viewbox values, with some padding
    center = (maxs + mins) / 2
    spans = (maxs - mins) * opts['padding'] # padding
    [x, y], [w, h] = center - spans/2, spans
    
    view_box = " ".join(map(str, [x, y, w, h]))
    
    # luckily, svg appears to automatically configure a 1:1 aspect ratio for us
    
    return opts['render']('<svg xmlns="http://www.w3.org/2000/svg" '
           + 'width="%(width)s" height="%(height)s" ' % opts
           + 'viewBox="' + view_box + '"'
           + '>'
           + '<g style="stroke: black; stroke-width: 1; fill: black;">' # give lines a default color
           + subgraphics(directives)
           + '</g>' + '</svg>')



""""
    ipython display
"""
        
import uuid

# needs to be made into a general tab view
class SVGTabView:
    def _pre(self, item):
        if '_repr_svg_' in dir(item):
            return item._repr_svg_()
        
        if '_repr_html_' in dir(item):
            return item._repr_html_()
        
        return str(item)
    
    def __init__(self, ls):
        self.ls = map(self._pre, ls)

    def _repr_html_(self, name=""):
        id = uuid.uuid4()
        
        return ("""
            <script type="text/javascript">

            </script>
            
            <ol id="%(id)s" class="flipbook static" name='%(name)s'>
            <li>
                """
                + "</li><li>".join(self.ls)
                + """
            </li>
            </ol>
            
            <script type="text/javascript" src="flipbook-ipy.js"></script>
            <script type="text/javascript">
                $('head').append('<link rel="stylesheet" type="text/css" href="oftencss_ipy.css" />');
                
                if (typeof constructFlipbook === 'undefined') {
                    setTimeout( function() { constructFlipbook($, $("#%(id)s")); }, 200 )
                } else {
                    constructFlipbook($, $("#%(id)s"));
                }
            </script>
            
                """) % {'id': id, 'name': name}
        

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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

















