from datetime import datetime

from glass.template import Node
from glass.template.nodes import VarNode

def date(parser):
    _, args = parser.get_next_token().clean_tag()
    obj, fmt = args.split(maxsplit=1)
    obj = VarNode.parse(obj)
    return DateNode(obj, fmt)


class DateNode(Node):
    def __init__(self, obj, fmt):
        self.obj = obj
        self.fmt = fmt

    def render(self, context, env):
        obj = self.obj.eval(context, env)
        fmt = self.fmt.replace('"',"'")
        fmt = fmt.strip("'")
        if isinstance(obj, datetime):
            return obj.strftime(fmt)
        if isinstance(obj, int):
            return datetime.fromtimestamp(obj).strftime(fmt)
        return ''
