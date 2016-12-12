import sublime, sublime_plugin
import re


def match(rex, str):
    m = rex.match(str)
    if m:
        return m.group(0)
    else:
        return None

def make_completion(tag):
    # make it look like
    # ("table\tTag", "table>$1</table>"),
    return (tag + '\tTag', tag + '>$0</' + tag + '>')

def get_tag_to_attributes():
    """
    Returns a dictionary with attributes accociated to tags
    This assumes that all tags can have global attributes as per MDN:
    https://developer.mozilla.org/en-US/docs/Web/WDML/Global_attributes
    """

    # Map tags to specific attributes applicable for that tag
    tag_dict = {
       'animate' : ['loop', 'delay'],
       'animate-frame' : ['start', 'delay'],
       'button' : ['text', 'h-align', 'v-align', 'color', 'normal', 'sel', 'checked', 'focus', 'disabled', 'sel-focus', 'checked-focus', 'checked-disabled', 'selected', 'silent', 'OnSelect', 'OnDbClick'],
       'checkbox' : []
    }

    # Assume that global attributes are common to all WDML elements
    global_attributes = [
        'name', 'rect', 'visible', 'active', 'enable', 'mushroom', 'autofocus', 
        'frame', 'transparent', 'layouttype', 'border', 'top-float', 'data', 'class',
        'font-family', 'font-size', 'font-style', 'font-auto', 'css', 'critical-sertion',
        'resolution', 'extendstyle', 'margin', 'box', 'type', 'grid-col', 'padding', 
        'scroll', 'scrollbar_body', 'scrollbar_slider'
    ]

    # Extend `global_attributes` by the event handler attributes
    global_attributes.extend([
        'PreBuildChildren', 'BuildChildrenFinished', 'PrePropertySetting', 'PropertySettingFinished',
        'OnKeyDown', 'OnKeyUp', 'OnKeyLongPress', 'OnMouseDown', 'OnMouseLongPress', 'OnGestureBegin',
        'OnGestureMove', 'OnGestureEnd', 'OnDualDown', 'OnDualUp', 'OnDualMove', 'OnTouchEvent', 
        'OnGestureSingleLeft', 'OnGestureDoubleRight', 'OnTick', 'OnSetFocus', 'OnLostFocus', 'OnSetEnable',
        'OnSetVisible', 'OnSetActive', 'OnSpriteEvent', 'OnPluginEvent'
    ])

    for attributes in tag_dict.values():
        attributes.extend(global_attributes)

    # Remove `dir` attribute from `bdi` key, because it is *not* inherited
    # from the global attributes
    if 'bdi' in tag_dict:
        tag_dict['bdi'] = [attr for attr in tag_dict['bdi'] if attr != 'dir']

    return tag_dict


class WDMLTagCompletions(sublime_plugin.EventListener):
    """
    Provide tag completions for WDML
    It matches just after typing the first letter of a tag name
    """
    def __init__(self):
        completion_list = self.default_completion_list()
        self.prefix_completion_dict = {}
        # construct a dictionary where the key is first character of
        # the completion list to the completion
        for s in completion_list:
            prefix = s[0][0]
            self.prefix_completion_dict.setdefault(prefix, []).append(s)

        # construct a dictionary from (tag, attribute[0]) -> [attribute]
        self.tag_to_attributes = get_tag_to_attributes()

    def on_query_completions(self, view, prefix, locations):
        # Only trigger within WDML
        if not view.match_selector(locations[0], "text.WDML - source - string.quoted"):
            return []

        # check if we are inside a tag
        is_inside_tag = view.match_selector(locations[0],
                "text.WDML meta.tag - text.WDML punctuation.definition.tag.begin")

        return self.get_completions(view, prefix, locations, is_inside_tag)

    def get_completions(self, view, prefix, locations, is_inside_tag):
        # see if it is in tag.attr or tag#attr format
        if not is_inside_tag:
            tag_attr_expr = self.expand_tag_attributes(view, locations)
            if tag_attr_expr != []:
                return (tag_attr_expr, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

        pt = locations[0] - len(prefix) - 1
        ch = view.substr(sublime.Region(pt, pt + 1))

        # print('prefix:', prefix)
        # print('location0:', locations[0])
        # print('substr:', view.substr(sublime.Region(locations[0], locations[0] + 3)), '!end!')
        # print('is_inside_tag', is_inside_tag)
        # print('ch:', ch)

        completion_list = []
        if is_inside_tag and ch != '<':
            if ch in [' ', '\t', '\n']:
                # maybe trying to type an attribute
                completion_list = self.get_attribute_completions(view, locations[0], prefix)
            # only ever trigger completion inside a tag if the previous character is a <
            # this is needed to stop completion from happening when typing attributes
            return (completion_list, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

        if prefix == '':
            # need completion list to match
            return ([], sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

        # match completion list using prefix
        completion_list = self.prefix_completion_dict.get(prefix[0], [])

        # if the opening < is not here insert that
        if ch != '<':
            completion_list = [(pair[0], '<' + pair[1]) for pair in completion_list]

        flags = 0
        if is_inside_tag:
            flags = sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS

        return (completion_list, flags)

    def default_completion_list(self):
        """
        Generate a default completion list for WDML
        """
        default_list = []
        normal_tags = ([
            'abbr', 'acronym', 'address', 'applet', 'article', 'aside',
            'audio', 'b', 'basefont', 'bdi', 'bdo', 'big', 'blockquote',
            'body', 'button', 'center', 'canvas', 'caption', 'cdata',
            'cite', 'colgroup', 'code', 'content', 'data', 'datalist',
            'dir', 'div', 'dd', 'del', 'details', 'dfn', 'dl', 'dt', 'element',
            'em', 'embed', 'fieldset', 'figure', 'figcaption', 'font', 'footer',
            'form', 'frame', 'frameset', 'head', 'header', 'h1', 'h2', 'h3',
            'h4', 'h5', 'h6', 'i', 'ins', 'isindex', 'kbd', 'keygen',
            'li', 'label', 'legend', 'main', 'map', 'mark', 'meter',
            'nav', 'noframes', 'noscript', 'object', 'ol', 'optgroup',
            'option', 'output', 'p', 'picture', 'pre', 'q', 'rp',
            'rt', 'rtc', 'ruby', 's', 'samp', 'section', 'select', 'shadow',
            'small', 'span', 'strong', 'sub', 'summary', 'sup',
            'table', 'tbody', 'td', 'template', 'textarea', 'tfoot', 'th',
            'thead', 'time', 'title', 'tr', 'tt', 'u', 'ul', 'var',
            'video'
        ])

        for tag in normal_tags:
            default_list.append(make_completion(tag))
            default_list.append(make_completion(tag.upper()))

        default_list += ([
            ('a\tTag', 'a href=\"$1\">$0</a>'),
            ('area\tTag', 'area shape=\"$1\" coords=\"$2\" href=\"$3\">'),
            ('audio\tTag', 'audio src=\"$1\">$0</audio>'),
            ('base\tTag', 'base href=\"$1\">'),
            ('br\tTag', 'br>'),
            ('col\tTag', 'col>'),
            ('hr\tTag', 'hr>'),
            ('iframe\tTag', 'iframe src=\"$1\">$0</iframe>'),
            ('input\tTag', 'input type=\"$1\" name=\"$2\">'),
            ('img\tTag', 'img src=\"$1\">'),
            ('link\tTag', 'link rel=\"stylesheet\" type=\"text/css\" href=\"$1\">'),
            ('meta\tTag', 'meta ${1:charset=\"utf-8\"}>'),
            ('param\tTag', 'param name=\"$1\" value=\"$2\">'),
            ('progress\tTag', 'progress value=\"$1\" max=\"$2\">'),
            ('script\tTag', 'script${2: type=\"${1:text/javascript}\"}>$0</script>'),
            ('source\tTag', 'source src=\"$1\" type=\"$2\">'),
            ('style\tTag', 'style type=\"${1:text/css}\">$0</style>'),
            ('track\tTag', 'track kind=\"$1\" src=\"$2\">'),
            ('wbr\tTag', 'wbr>'),
            ('video\tTag', 'video src=\"$1\">$0</video>')
        ])

        return default_list

    # This responds to on_query_completions, but conceptually it's expanding
    # expressions, rather than completing words.
    #
    # It expands these simple expressions:
    # tag.class
    # tag#id
    def expand_tag_attributes(self, view, locations):
        # Get the contents of each line, from the beginning of the line to
        # each point
        lines = [view.substr(sublime.Region(view.line(l).a, l))
            for l in locations]

        # Reverse the contents of each line, to simulate having the regex
        # match backwards
        lines = [l[::-1] for l in lines]

        # Check the first location looks like an expression
        rex = re.compile("([\w-]+)([.#])(\w+)")
        expr = match(rex, lines[0])
        if not expr:
            return []

        # Ensure that all other lines have identical expressions
        for i in range(1, len(lines)):
            ex = match(rex, lines[i])
            if ex != expr:
                return []

        # Return the completions
        arg, op, tag = rex.match(expr).groups()

        arg = arg[::-1]
        tag = tag[::-1]
        expr = expr[::-1]

        if op == '.':
            snippet = '<{0} class=\"{1}\">$1</{0}>$0'.format(tag, arg)
        else:
            snippet = '<{0} id=\"{1}\">$1</{0}>$0'.format(tag, arg)

        return [(expr, snippet)]

    def get_attribute_completions(self, view, pt, prefix):
        SEARCH_LIMIT = 500
        search_start = max(0, pt - SEARCH_LIMIT - len(prefix))
        line = view.substr(sublime.Region(search_start, pt + SEARCH_LIMIT))

        line_head = line[0:pt - search_start]
        line_tail = line[pt - search_start:]

        # find the tag from end of line_head
        i = len(line_head) - 1
        tag = None
        space_index = len(line_head)
        while i >= 0:
            c = line_head[i]
            if c == '<':
                # found the open tag
                tag = line_head[i + 1:space_index]
                break
            elif c == ' ':
                space_index = i
            i -= 1

        # check that this tag looks valid
        if not tag or not tag.isalnum():
            return []

        # determines whether we need to close the tag
        # default to closing the tag
        suffix = '>'

        for c in line_tail:
            if c == '>':
                # found end tag
                suffix = ''
                break
            elif c == '<':
                # found another open tag, need to close this one
                break

        if suffix == '' and not line_tail.startswith(' ') and not line_tail.startswith('>'):
            # add a space if not there
            suffix = ' '

        # got the tag, now find all attributes that match
        attributes = self.tag_to_attributes.get(tag, [])
        # ("class\tAttr", "class="$1">"),
        attri_completions = [(a + '\tAttr', a + '="$1"' + suffix) for a in attributes]
        return attri_completions


# unit testing
# to run it in sublime text:
# import WDML.WDML_completions
# WDML.WDML_completions.Unittest.run()

import unittest

class Unittest(unittest.TestCase):

    class Sublime:
        INHIBIT_WORD_COMPLETIONS = 1
        INHIBIT_EXPLICIT_COMPLETIONS = 2

    # this view contains a hard coded one line super simple WDML fragment
    class View:
        def __init__(self):
            self.buf = '<tr><td class="a">td.class</td></tr>'

        def line(self, pt):
            # only ever 1 line
            return sublime.Region(0, len(self.buf))

        def substr(self, region):
            return self.buf[region.a : region.b]

    def run():
        # redefine the modules to use the mock version
        global sublime

        sublime_module = sublime
        # use the normal region
        Unittest.Sublime.Region = sublime.Region
        sublime = Unittest.Sublime

        test = Unittest()
        test.test_simple_completion()
        test.test_inside_tag_completion()
        test.test_inside_tag_no_completion()
        test.test_expand_tag_attributes()

        # set it back after testing
        sublime = sublime_module

    # def get_completions(self, view, prefix, locations, is_inside_tag):
    def test_simple_completion(self):
        # <tr><td class="a">td.class</td></tr>
        view = Unittest.View()
        completor = WDMLTagCompletions()

        # simulate typing 'tab' at the start of the line, it is outside a tag
        completion_list, flags = completor.get_completions(view, 'tab', [0], False)

        # should give a bunch of tags that starts with t
        self.assertEqual(completion_list[0], ('table\tTag', '<table>$0</table>'))
        self.assertEqual(completion_list[1], ('tbody\tTag', '<tbody>$0</tbody>'))
        # don't suppress word based completion
        self.assertEqual(flags, 0)

    def test_inside_tag_completion(self):
        # <tr><td class="a">td.class</td></tr>
        view = Unittest.View()
        completor = WDMLTagCompletions()

        # simulate typing 'h' after <tr><, i.e. <tr><h
        completion_list, flags = completor.get_completions(view, 'h', [6], True)

        # should give a bunch of tags that starts with h, and without <
        self.assertEqual(completion_list[0], ('head\tTag', 'head>$0</head>'))
        self.assertEqual(completion_list[1], ('header\tTag', 'header>$0</header>'))
        self.assertEqual(completion_list[2], ('h1\tTag', 'h1>$0</h1>'))
        # suppress word based completion
        self.assertEqual(flags, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

        # simulate typing 'he' after <tr><, i.e. <tr><he
        completion_list, flags = completor.get_completions(view, 'he', [7], True)

        # should give a bunch of tags that starts with h, and without < (it filters only on the first letter of the prefix)
        self.assertEqual(completion_list[0], ('head\tTag', 'head>$0</head>'))
        self.assertEqual(completion_list[1], ('header\tTag', 'header>$0</header>'))
        self.assertEqual(completion_list[2], ('h1\tTag', 'h1>$0</h1>'))
        # suppress word based completion
        self.assertEqual(flags, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

    def test_inside_tag_no_completion(self):
        # <tr><td class="a">td.class</td></tr>
        view = Unittest.View()
        completor = WDMLTagCompletions()

        # simulate typing 'h' after <tr><td , i.e. <tr><td h
        completion_list, flags = completor.get_completions(view, 'h', [8], True)

        # should give nothing, but disable word based completions, since it is inside a tag
        self.assertEqual(completion_list, [])
        self.assertEqual(flags, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

    def test_expand_tag_attributes(self):
        # <tr><td class="a">td.class</td></tr>
        view = Unittest.View()
        completor = WDMLTagCompletions()

        # simulate typing tab after td.class
        completion_list, flags = completor.get_completions(view, '', [26], False)

        # should give just one completion, and suppress word based completion
        self.assertEqual(completion_list, [('td.class', '<td class="class">$1</td>$0')])
        self.assertEqual(flags, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
